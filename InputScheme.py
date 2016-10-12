from functools import partial
import time, logging

from PySide import QtGui, QtCore

from DragDropUI import IconLayout, FolderIcon
from pymouse import PyMouse

import settings, assets

pyMouse = PyMouse()

def clamp(number, minimum, maximum):
	return max(min(number, maximum), minimum)

class InputScheme(QtCore.QObject):
	imageMoved = QtCore.Signal(str, str)
	ready = QtCore.Signal()
	error = QtCore.Signal(object)
	
	def __init__(self, window=None):
		super().__init__()
		self.grabbedIcons = []
		self.setWindow(window)
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
		if len(self.grabbedIcons) > 0:
			self.releaseImages()
			
		widget = self.findWidgetAt(x, y)
		if widget is not None and not isinstance(widget, FolderIcon):
			logging.info('Image grabbed %s' % widget.text)
			self.grabImage(widget)
			return True
		else:
			logging.info('Grab failure')
			assets.play('bummer')
			return False

	def doRelease(self, x, y):
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
		
		assets.play('select')
		
	def moveImages(self, folder):
		if len(self.grabbedIcons) == 0:
			return

		for icon in self.grabbedIcons:
			p = icon.parentWidget()
			if p is not None:
				replacement = QtGui.QWidget(icon.parent())
				replacement.setMinimumSize(icon.size())
				p.layout().replaceItem(icon, replacement)
				icon.setParent(None)
			self.imageMoved.emit(icon.text, folder.text)
		
		self.grabbedIcons = []
		
		folder.blink()
		assets.play('drop')

	def releaseImages(self):
		if len(self.grabbedIcons) == 0:
			return
		
		for icon in self.grabbedIcons:
			icon.setUnselected()

		self.grabbedIcons = []
		assets.play('release')
		
	def isGrabbing(self):
		return len(self.grabbedIcons) > 0

class GazeAndGestureScheme(InputScheme):
	def __init__(self, window=None):
		from GestureDevice import GestureDevice
		import GazeDevice

		super().__init__(window)
		
		self.gestureTracker = GestureDevice()
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
		super().start()
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)
		self.gazeTracker.reset()
		
	def setWindow(self, window):
		super().setWindow(window)
		if window is not None:
			window.feedbackWindow.showEye()
			window.feedbackWindow.showHand()
			self.gestureTracker.handAppeared.connect(window.feedbackWindow.setHandGood)
			self.gestureTracker.noHands.connect(window.feedbackWindow.setHandBad)
			self.gestureTracker.grabbed.connect(window.feedbackWindow.setHandClosed)
			self.gestureTracker.released.connect(window.feedbackWindow.setHandOpen)
			self.gestureTracker.moved.connect(window.feedbackWindow.setHandGood)
			self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
			self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)
			
	def grabbed(self, hand):
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		self.doGrab(gaze[0], gaze[1])
		pyMouse.move(int(gaze[0]), int(gaze[1]))
		self.gazeTracker.clearLastFixation()
		
	def released(self, hand):
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		self.doRelease(gaze[0], gaze[1])
		pyMouse.move(int(gaze[0]), int(gaze[1]))
		self.gazeTracker.clearLastFixation()

	def stop(self):
		super().stop()
		self.gestureTracker.stop()
		self.gazeTracker.stop()

class MouseScheme(InputScheme):
	def __init__(self, window=None):
		super().__init__(window)
		
		self.floatingIcon = None
		self._ready = True
		
	def setWindow(self, window):
		super().setWindow(window)
		if window is not None:
			self.window.mousePressed.connect(self.grab)
			self.window.mouseReleased.connect(self.release)
			self.window.mouseMoved.connect(self.moveIcon)
			if type(self) == MouseScheme:
				window.feedbackWindow.close()
		
	def grab(self, obj, mouseEvent):
		pos = obj.mapToGlobal(mouseEvent.pos())
		if self.doGrab(pos.x(), pos.y()):
			if len(self.grabbedIcons) == 1:
				self.floatingIcon = DraggingIcon(self.grabbedIcons[0], self.window)
				self.floatingIcon.move(
					int(pos.x()-self.floatingIcon.width()/2),
					int(pos.y()-self.floatingIcon.height()/2)
				)
				
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

class GestureScheme(MouseScheme):
	def __init__(self, window=None):
		from GestureDevice import GestureDevice

		self.gestureTracker = GestureDevice()
		self.attentivePoint = None
		super().__init__(window)
		self.virtualPos = None
		
	def changePreselectedIcon(self, pos):
		if self.attentivePoint is None or pos == self.attentivePoint:
			super().changePreselectedIcon(pos)

	def start(self):
		super().start()
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)
		self.gestureTracker.moved.connect(self.handMoved)
		self.gestureTracker.fixated.connect(self.fixated)
		self.gestureTracker.fixationInvalidated.connect(self.fixationInvalidated)
		
		mousePos = pyMouse.position()
		self.virtualPos = [mousePos[0], mousePos[1]]

		screenSize = QtGui.QDesktopWidget().screenGeometry()
		self.screenSize = [screenSize.width(), screenSize.height()]
		logging.debug('Leap connected')
		
	def setWindow(self, window):
		super().setWindow(window)
		if window is not None:
			window.feedbackWindow.showHand()
			self.gestureTracker.handAppeared.connect(window.feedbackWindow.setHandGood)
			self.gestureTracker.noHands.connect(window.feedbackWindow.setHandBad)
			self.gestureTracker.grabbed.connect(window.feedbackWindow.setHandClosed)
			self.gestureTracker.released.connect(window.feedbackWindow.setHandOpen)
			self.gestureTracker.moved.connect(window.feedbackWindow.setHandGood)
			self.gestureTracker.reachingBounds.connect(window.feedbackWindow.setGestureBoundNotice)

	def fixated(self, handPosition):
		self.attentivePoint = pyMouse.position()
		self.changePreselectedIcon(self.attentivePoint)

	def fixationInvalidated(self, handPosition):
		self.attentivePoint = None

	def grabbed(self, hand):
		if self.attentivePoint is None:
			location = self.virtualPos
		else:
			location = self.attentivePoint
		
		previousLocation = pyMouse.position()
		pyMouse.press(round(location[0]), round(location[1]))
		pyMouse.move(previousLocation[0], previousLocation[1])
		self.gestureTracker.clearLastFixation()
		self.attentivePoint = None

	def released(self, hand):
		if self.attentivePoint is None:
			location = self.virtualPos
		else:
			location = self.attentivePoint

		previousLocation = pyMouse.position()
		pyMouse.release(round(location[0]), round(location[1]))
		self.release(position=location)
		pyMouse.move(previousLocation[0], previousLocation[1])
		self.gestureTracker.clearLastFixation()
		self.attentivePoint = None
				
	def handMoved(self, delta):
		self.virtualPos[0] = clamp(self.virtualPos[0] + delta[0], 0, self.screenSize[0])
		self.virtualPos[1] = clamp(self.virtualPos[1] + delta[2] , 0, self.screenSize[1])
		pyMouse.move(round(self.virtualPos[0]), round(self.virtualPos[1]))
			
	def stop(self):
		self.gestureTracker.stop()

class GazeAndMotionScheme(GestureScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)
		self._ready = False
		
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
			self.gazeTracker.ready.connect(self.ready.emit)
			self.gazeTracker.error.connect(self.error.emit)
			self.gazeTracker.moved.connect(self.eyesMoved)
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
	
	def isReady(self):
		return self.gazeTracker.isReady()
	
	def fixated(self, handPosition):
		if self.floatingIcon is not None:
			super().fixated(handPosition)
		
	def eyesMoved(self, pos):
		if self.floatingIcon is None:
			self.attentivePoint = pos
			self.changePreselectedIcon(pos)
		
	def setWindow(self, window):
		super().setWindow(window)
		if window is not None:
			window.feedbackWindow.showEye()
			self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
			self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)

	def grabbed(self, hand):
		self.gestureTracker.clearLastFixation()
		self.gazeTracker.clearLastFixation()
		gaze = self.gazeTracker.getAttentiveGaze(clear=True)
		pyMouse.press(int(gaze[0]), int(gaze[1]))
		if settings.checkBool(settings.systemValue('syncGestureAndGaze')):
			self.virtualPos = gaze
		
	def released(self, hand):
		super().released(hand)
		self.gazeTracker.clearLastFixation()
		
	def handMoved(self, delta):
		if self.floatingIcon is not None:
			super().handMoved(delta)
		
	def start(self):
		super().start()
		self.gazeTracker.reset()

class GazeAndButtonScheme(InputScheme):
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
		if window is not None:
			window.installEventFilter(self)
			window.feedbackWindow.showEye()
			self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
			self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)
		
	def eventFilter(self, widget, event):
		if event.type() == QtCore.QEvent.KeyPress and not event.isAutoRepeat():
			gaze = self.gazeTracker.getAttentiveGaze(clear=True)
			self.doGrab(gaze[0], gaze[1])
			pyMouse.move(int(gaze[0]), int(gaze[1]))
		elif event.type() == QtCore.QEvent.KeyRelease and not event.isAutoRepeat():
			gaze = self.gazeTracker.getAttentiveGaze(clear=True)
			self.doRelease(gaze[0], gaze[1])
			pyMouse.move(int(gaze[0]), int(gaze[1]))

		return QtGui.QWidget.eventFilter(self, widget, event)

	def start(self):
		super().start()
		self.gazeTracker.reset()

	def stop(self):
		self.gazeTracker.stop()

class GazeScheme(InputScheme):
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
		super().start()
		self.gazeTracker.fixated.connect(self.onFixate)
		self.gazeTracker.eyesAppeared.connect(self.window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(self.window.feedbackWindow.setEyeBad)
		self.gazeTracker.reset()

	def setWindow(self, window):
		super().setWindow(window)
		if window is not None:
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
		pyMouse.move(int(position.x), int(position.y))
		
	def stop(self):
		super().stop()
		self.gazeTracker.stop()

class DraggingIcon(QtGui.QLabel):
	def __init__(self, fromIcon, parentWindow):
		super().__init__(parentWindow)
		self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
		self.setPixmap(QtGui.QPixmap.fromImage(fromIcon.image.scaled(75, 75)))
		self.show()

class SchemeSelector(QtGui.QWidget):
	selected = QtCore.Signal(object, object, bool)
	closed = QtCore.Signal()
	
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle('Input Scheme Selector')
		font = self.font()
		font.setPointSize(18)
		self.setFont(font)
		
		self.setLayout(QtGui.QGridLayout())
		
		self.participantIDBox = QtGui.QLineEdit()
		self.participantIDBox.setAlignment(QtCore.Qt.AlignCenter)
		self.participantIDBox.setText(settings.systemValue('participantID'))
		self.layout().addWidget(QtGui.QLabel('<center>Participant ID</center>'), 0, 0, 1, 2)
		self.layout().addWidget(self.participantIDBox, 1, 0, 1, 2)

		components = [
			{'scheme':'MouseScheme', 'label': 'Mouse only'},
			{'scheme':'GestureScheme', 'label': 'Gesture only'},
			{'scheme':'GazeScheme', 'label': 'Gaze only'},
			{'scheme':'GazeAndButtonScheme', 'label': 'Gaze + button'},
			{'scheme':'GazeAndGestureScheme', 'label': 'Gaze + gesture'},
			{'scheme':'GazeAndMotionScheme', 'label': 'Gaze + motion'},
		]
		
		colors = {
			'Practice': QtCore.Qt.yellow,
			'Experiment': QtCore.Qt.green,
		}
		for column, heading in enumerate(['Practice', 'Experiment']):
			self.layout().addWidget(QtGui.QLabel('<center>%s</center>' % heading), 2, column)
			for rowOffset, component in enumerate(components):
				row = 3 + rowOffset
				b = QtGui.QPushButton(component['label'])
				b.clicked.connect(partial(self.schemeClicked, component['scheme'], heading == 'Practice'))
				pal = b.palette()
				pal.setColor(pal.Button, colors[heading])
				b.setAutoFillBackground(True)
				b.setPalette(pal)
				b.update()
				self.layout().addWidget(b, row, column)
			
		self.label = QtGui.QLabel()
		self.errorLabel = QtGui.QLabel()
		
	def displayText(self, msg):
		self.label.setText('<font size="14"><b><center>%s</center></b></font>' % msg)
		
	def displayError(self, msg):
		self.errorLabel.setText('<font size="6">Error: %s</font>' % msg)
		
	def schemeClicked(self, scheme, practiceOnly):
		participantID = self.participantIDBox.text()
		if participantID.strip() == "":
			QtGui.QMessageBox.critical(self, 'Error', '<font size="6">Please enter a participant ID</font>')
			self.participantIDBox.setFocus()
		else:
			settings.setSystemValue('participantID', participantID)
			while self.layout().count() > 0:
				item = self.layout().takeAt(0)
				widget = item.widget()
				self.layout().removeWidget(widget)
				widget.setParent(None)
				del widget
				del item
				
			self.displayText('Loading<br>Please wait...')
			self.layout().addWidget(self.label, 0, 0, 1, 2)
			self.layout().addWidget(self.errorLabel, 1, 0, 1, 2)
			self.update()
			self.repaint()
			
			self.selected.emit(scheme, participantID, practiceOnly)
			

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
