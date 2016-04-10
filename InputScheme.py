from functools import partial
import time, logging

from PySide import QtGui, QtCore

from DragDropUI import IconLayout, FolderIcon
from pymouse import PyMouse
import sound

pyMouse = PyMouse()

class InputScheme(QtCore.QObject):
	imageMoved = QtCore.Signal(str, str)
	ready = QtCore.Signal()
	error = QtCore.Signal(object)
	
	def __init__(self, window=None):
		super().__init__()
		self.grabbedIcons = []
		self.window = window
		self._ready = False
		
		self.preselectedIcon = None
		
	def changePreselectedIcon(self, pos):
		if self.preselectedIcon is not None and hasattr(self.preselectedIcon, 'setUnhovered'):
			self.preselectedIcon.setUnhovered()
			
		icon = self.findWidgetAt(pos[0], pos[1])
		if icon is not None and hasattr(icon, 'setHovered'):
			self.preselectedIcon = icon
			self.preselectedIcon.setHovered()
		else:
			self.preselectedIcon = None
	
	def isReady(self):
		return self._ready
		
	def start(self):
		pass

	def stop(self):
		pass
		
	def setWindow(self, window=None):
		self.window = window
		
	def findWidgetAt(self, x, y):
		widget = QtGui.QApplication.instance().widgetAt(x, y)
		while widget != None:
			if isinstance(widget, IconLayout):
				return widget
			else:
				widget = widget.parentWidget()
		return widget

	def doGrab(self, x, y):
		pyMouse.move(int(x), int(y))
		widget = self.findWidgetAt(x, y)
		if widget is not None and not isinstance(widget, FolderIcon):
			logging.info('Image grabbed %s' % widget.text)
			self.grabImage(widget)
			return True
		else:
			logging.info('Grab failure')
			sound.play('bummer.wav')
			return False

	def doRelease(self, x, y):
		pyMouse.move(int(x), int(y))
		if len(self.grabbedIcons) == 0:
			return False

		widget = QtGui.QApplication.instance().widgetAt(x, y)
		while widget != None:
			if isinstance(widget, FolderIcon):
				break
			else:
				widget = widget.parentWidget()
				
		if widget != None:
			self.moveImages(widget)
			return True
		else:
			self.releaseImages()
			logging.info('Drop failure')
			return False
			
	def grabImage(self, image):
		# only allow one image to be grabbed for now...
		for icon in self.grabbedIcons:
			icon.setUnselected()
		del self.grabbedIcons[:]
		
		image.setSelected()
		self.grabbedIcons.append(image)
		
		sound.play("select.wav")
		
	def moveImages(self, folder):
		if len(self.grabbedIcons) == 0:
			return

		for icon in self.grabbedIcons:
			p = icon.parentWidget()
			if p is not None:
				p.layout().removeWidget(icon)
				icon.setParent(None)
			self.imageMoved.emit(icon.text, folder.text)
		
		self.grabbedIcons = []
		
		folder.blink()
		sound.play("drop.wav")

	def releaseImages(self):
		if len(self.grabbedIcons) == 0:
			return
		
		for icon in self.grabbedIcons:
			icon.setUnselected()

		self.grabbedIcons = []
		sound.play("release.wav")
		
	def isGrabbing(self):
		return len(self.grabbedIcons) > 0

class LookGrabLookDropScheme(InputScheme):
	def __init__(self, window=None):
		from LeapDevice import LeapDevice
		import GazeDevice

		super().__init__(window)
		
		self.gestureTracker = LeapDevice()
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
			self.gazeTracker.ready.connect(self.ready.emit)
			self.gazeTracker.error.connect(self.error.emit)
			self.gazeTracker.moved.connect(self.changePreselectedIcon)
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
			
		self.scale = 0
		
	def isReady(self):
		return self.gazeTracker.isReady()
		
	def start(self):
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)
		
	def setWindow(self, window):
		super().setWindow(window)
		window.feedbackWindow.showEye()
		window.feedbackWindow.showHand()
		self.gestureTracker.handAppeared.connect(window.feedbackWindow.setHandGood)
		self.gestureTracker.noHands.connect(window.feedbackWindow.setHandBad)
		self.gestureTracker.grabbed.connect(window.feedbackWindow.setHandClosed)
		self.gestureTracker.released.connect(window.feedbackWindow.setHandOpen)
		self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)

	def grabbed(self, hand):
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		self.doGrab(gaze[0], gaze[1])
		
	def released(self, hand):
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		self.doRelease(gaze[0], gaze[1])

	def setScaling(self, value):
		pass

	def stop(self):
		self.gestureTracker.stop()
		self.gazeTracker.stop()

class MouseOnlyScheme(InputScheme):
	def __init__(self, window=None):
		super().__init__(window)
		
		self.floatingIcon = None
		self._ready = True
		
	def start(self):
		if self.window == None:
			QtCore.QTimer.singleShot(100, self.start)
			return False
		else:
			self.window.mousePressed.connect(self.grab)
			self.window.mouseReleased.connect(self.release)
			self.window.mouseMoved.connect(self.moveIcon)
			return True
		
	def setWindow(self, window):
		super().setWindow(window)
		if type(self) == MouseOnlyScheme:
			window.feedbackWindow.close()
		
	def grab(self, obj, mouseEvent):
		pos = obj.mapToGlobal(mouseEvent.pos())
		if self.doGrab(pos.x(), pos.y()):
			if len(self.grabbedIcons) == 1:
				self.floatingIcon = DraggingIcon(self.grabbedIcons[0], self.window)
				
	def release(self, obj=None, mouseEvent=None, position=None):
		if position is None:
			position = obj.mapToGlobal(mouseEvent.pos())
			position = [position.x(), position.y()]
		if self.floatingIcon != None:
			self.floatingIcon.hide()
			self.floatingIcon.close()
			self.floatingIcon = None

		self.doRelease(position[0], position[1])
			
	def moveIcon(self):
		pos = pyMouse.position()
		if self.floatingIcon:
			self.floatingIcon.move(pos[0] - self.floatingIcon.width()/2, pos[1]-self.floatingIcon.height()/2)
		self.changePreselectedIcon(pos)

class LeapOnlyScheme(MouseOnlyScheme):
	def __init__(self, window=None):
		from LeapDevice import LeapDevice

		self.gestureTracker = LeapDevice()
		super().__init__(window)

	def start(self):
		if super().start():
			self.gestureTracker.grabbed.connect(self.grabbed)
			self.gestureTracker.released.connect(self.released)
			self.gestureTracker.moved.connect(self.moved)
			logging.debug('Leap connected')
		
	def setWindow(self, window):
		super().setWindow(window)
		window.feedbackWindow.showHand()
		self.gestureTracker.handAppeared.connect(window.feedbackWindow.setHandGood)
		self.gestureTracker.noHands.connect(window.feedbackWindow.setHandBad)
		self.gestureTracker.grabbed.connect(window.feedbackWindow.setHandClosed)
		self.gestureTracker.released.connect(window.feedbackWindow.setHandOpen)

	def grabbed(self, hand):
		location = pyMouse.position()
		pyMouse.press(location[0], location[1])

	def released(self, hand):
		location = pyMouse.position()
		pyMouse.release(location[0], location[1])
		self.release(position=location)
		
	def moved(self, delta):
		location = pyMouse.position()
		pyMouse.move(
			int(location[0] + delta[0]),
			int(location[1] - delta[1])
		)
			
	def setScaling(self, value):
		self.scale = value

	def stop(self):
		self.gestureTracker.stop()

class LeapMovesMeScheme(LeapOnlyScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)
		self._ready = False
		
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
			self.gazeTracker.ready.connect(self.ready.emit)
			self.gazeTracker.error.connect(self.error.emit)
			self.gazeTracker.moved.connect(self.changePreselectedIcon)
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
			
	def isReady(self):
		return self.gazeTracker.isReady()
		
	def setWindow(self, window):
		super().setWindow(window)
		window.feedbackWindow.showEye()
		self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)

	def grabbed(self, hand):
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		pyMouse.press(int(gaze[0]), int(gaze[1]))
		
	def doGrab(self, x, y):
		if super().doGrab(x, y):
			try:
				self.gazeTracker.moved.disconnect(self.changePreselectedIcon)
			except:
				pass
			self.gestureTracker.moved.connect(self.changePreselectedIcon)
			return True
		else:
			return False

	def doRelease(self, x, y):
		if super().doRelease(x, y):
			try:
				self.gestureTracker.moved.disconnect(self.changePreselectedIcon)
			except:
				pass
			self.gazeTracker.moved.connect(self.changePreselectedIcon)
			return True
		else:
			return False
			
	def moved(self, delta):
		if self.floatingIcon:
			super().moved(delta)
		
class GazeAndKeyboardScheme(InputScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)
		
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
			self.gazeTracker.ready.connect(self.ready.emit)
			self.gazeTracker.error.connect(self.error.emit)
			self.gazeTracker.moved.connect(self.changePreselectedIcon)
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
			
	def isReady(self):
		return self.gazeTracker.isReady()

	def setWindow(self, window):
		super().setWindow(window)
		window.installEventFilter(self)
		window.feedbackWindow.showEye()
		self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)
		
	def eventFilter(self, widget, event):
		if event.type() == QtCore.QEvent.KeyPress and not event.isAutoRepeat():
			gaze = self.gazeTracker.getAttentiveGaze(clear=True)
			self.doGrab(gaze[0], gaze[1])
		elif event.type() == QtCore.QEvent.KeyRelease and not event.isAutoRepeat():
			gaze = self.gazeTracker.getAttentiveGaze(clear=True)
			self.doRelease(gaze[0], gaze[1])
            
		return QtGui.QWidget.eventFilter(self, widget, event)

	def stop(self):
		self.gazeTracker.stop()

class GazeOnlyScheme(InputScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)

		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
			self.gazeTracker.ready.connect(self.ready.emit)
			self.gazeTracker.error.connect(self.error.emit)
			self.gazeTracker.moved.connect(self.changePreselectedIcon)
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))

	def start(self):
		self.gazeTracker.fixated.connect(self.onFixate)
		self.gazeTracker.eyesAppeared.connect(self.window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(self.window.feedbackWindow.setEyeBad)

	def setWindow(self, window):
		super().setWindow(window)
		window.feedbackWindow.showEye()
		
	def onFixate(self, position):
		widget = QtGui.QApplication.instance().widgetAt(position.x, position.y)
		while widget != None:
			if isinstance(widget, IconLayout):
				break
			else:
				widget = widget.parentWidget()
		
		if widget != None:
			if isinstance(widget, FolderIcon):
				self.doRelease(position.x, position.y)
			else:
				self.doGrab(position.x, position.y)
		else:
			if not self.isGrabbing():
				self.doGrab(position.x, position.y)
			else:
				self.doRelease(position.x, position.y)
		
	def stop(self):
		self.gazeTracker.stop()

class DraggingIcon(QtGui.QMdiSubWindow):
	def __init__(self, fromIcon, parentWindow):
		super().__init__()
		self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
		
		icon = QtGui.QLabel()
		icon.setPixmap(QtGui.QPixmap.fromImage(fromIcon.image.scaled(75, 75)))
		self.setWidget(icon)
		
		parentWindow.addSubWindow(self, QtCore.Qt.FramelessWindowHint)
		
		pos = fromIcon.mapToGlobal(fromIcon.imageWidget.rect().center())
		
		self.move(pos.x() , pos.y())
		self.show()

class SchemeSelector(QtGui.QWidget):
	selected = QtCore.Signal(object, object)
	closed = QtCore.Signal()
	
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle('Project 2 Launcher')
		font = self.font()
		font.setPointSize(18)
		self.setFont(font)
		
		layout = QtGui.QVBoxLayout()
		self.setLayout(layout)
		
		self.participantIDBox = QtGui.QLineEdit()
		self.participantIDBox.setAlignment(QtCore.Qt.AlignCenter)
		
		participantInfoWidget = QtGui.QWidget()
		participantInfoWidget.setLayout(QtGui.QHBoxLayout())
		participantInfoWidget.layout().addWidget(QtGui.QLabel("Participant ID"))
		participantInfoWidget.layout().addWidget(self.participantIDBox)
		
		layout.addWidget(participantInfoWidget)

		components = [
			{'scheme':'LookGrabLookDropScheme', 'label': 'Gaze + gesture'},
			{'scheme':'LeapMovesMeScheme', 'label': 'Gaze + gesture with motion'},
			{'scheme':'MouseOnlyScheme', 'label': 'Mouse only'},
			{'scheme':'LeapOnlyScheme', 'label': 'Gesture only'},
			{'scheme':'GazeAndKeyboardScheme', 'label': 'Gaze and button'},
			{'scheme':'GazeOnlyScheme', 'label': 'Gaze only'},
		]
		
		for component in components:
			b = QtGui.QPushButton(component['label'])
			b.clicked.connect(partial(self.startScheme, component['scheme']))
			layout.addWidget(b)
			
		self.label = QtGui.QLabel()
		self.errorLabel = QtGui.QLabel()
		
	def displayText(self, msg):
		self.label.setText('<font size="14"><b><center>%s</center></b></font>' % msg)
		
	def displayError(self, msg):
		self.errorLabel.setText('<font size="6">Error: %s</font>' % msg)
		
	def startScheme(self, scheme):
		participantID = self.participantIDBox.text()
		if participantID.strip() == "":
			QtGui.QMessageBox.critical(self, 'Error', '<font size="6">Please enter a participant ID</font>')
		else:
			while self.layout().count() > 0:
				item = self.layout().takeAt(0)
				widget = item.widget()
				self.layout().removeWidget(widget)
				widget.setParent(None)
				del widget
				del item
				
			self.displayText('Loading<br>Please wait...')
			self.layout().addWidget(self.label)
			self.layout().addWidget(self.errorLabel)
			self.selected.emit(scheme, participantID)
			self.update()
			self.repaint()

	def resizeEvent(self, e):
		desktopSize = QtGui.QDesktopWidget().screenGeometry()
		self.move(
			(desktopSize.width() - self.size().width()) / 2,
			(desktopSize.height() - self.size().height()) / 2
		)

	def closeEvent(self, e):
		self.hide()
		super().closeEvent(e)
		self.closed.emit()
