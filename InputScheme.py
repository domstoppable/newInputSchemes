from functools import partial
import time, logging

from PySide import QtGui, QtCore

from DragDropUI import IconLayout, FolderIcon
from pymouse import PyMouse
import sound

pyMouse = PyMouse()

'''
'
'''
class InputScheme(QtCore.QObject):
	imageMoved = QtCore.Signal(str, str)
	def __init__(self, window=None):

		super().__init__()
		self.grabbedIcons = []
		self.destination = None
		self.window = window
		
	def start(self):
		pass

	def quit(self):
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
			icon._unhighlight()
		del self.grabbedIcons[:]
		
		image._highlight()
		self.grabbedIcons.append(image)
		
		sound.play("select.wav")
		
	def moveImages(self, folder):
		self.destination = folder
		QtCore.QTimer.singleShot(0, self._moveImages)
		
	def _moveImages(self):
		folder = self.destination
		if len(self.grabbedIcons) == 0:
			return

		for icon in self.grabbedIcons:
			p = icon.parentWidget()
			if p is not None:
				p.layout().removeWidget(icon)
				icon.setParent(None)
			icon._unhighlight()
			self.imageMoved.emit(icon.text, folder.text)
		
		self.grabbedIcons = []
		
		folder.blink.emit()
		sound.play("drop.wav")

	def releaseImages(self):
		QtCore.QTimer.singleShot(0, self._releaseImages)
		
	def _releaseImages(self):
		if len(self.grabbedIcons) == 0:
			return
		
		for icon in self.grabbedIcons:
			icon._unhighlight()

		self.grabbedIcons = []
		sound.play("release.wav")
		
	def isGrabbing(self):
		return len(self.grabbedIcons) > 0

'''
'
'''
class LookGrabLookDropScheme(InputScheme):
	def __init__(self, window=None):
		from LeapDevice import LeapDevice
		import GazeDevice

		super().__init__(window)
		
		self.gestureTracker = LeapDevice()
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
			
		self.scale = 0
		
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
		gaze = self.gazeTracker.getGaze()
		self.doGrab(gaze[0], gaze[1])
		
	def released(self, hand):
		gaze = self.gazeTracker.getGaze()
		self.doRelease(gaze[0], gaze[1])

	def setScaling(self, value):
		pass

	def setGrabThreshold(self, value):
		self.gestureTracker.grabThreshold = value

	def setReleaseThreshold(self, value):
		self.gestureTracker.releaseThreshold = value
		
	def quit(self):
		self.gestureTracker.exit()

class MouseOnlyScheme(InputScheme):
	def __init__(self, window=None):
		super().__init__(window)
		
		self.floatingIcon = None
		
	def start(self):
		if self.window == None:
			QtCore.QTimer.singleShot(100, self.connectEvents)
		else:
			self.window.mousePressed.connect(self.grab)
			self.window.mouseReleased.connect(self.release)
			self.window.mouseMoved.connect(self.moveIcon)
		
	def setWindow(self, window):
		super().setWindow(window)
		if type(self) == MouseOnlyScheme:
			window.feedbackWindow.close()
		
	def grab(self, obj, mouseEvent):
		pos = obj.mapToGlobal(mouseEvent.pos())
		if self.doGrab(pos.x(), pos.y()):
			if len(self.grabbedIcons) == 1:
				self.floatingIcon = DraggingIcon(self.grabbedIcons[0], self.window)
				self.move(obj, mouseEvent)
				
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
		if self.floatingIcon:
			pos = pyMouse.position()
			self.floatingIcon.move(pos[0] - self.floatingIcon.width()/2, pos[1]-self.floatingIcon.height()/2)
'''
'
'''

class LeapOnlyScheme(MouseOnlyScheme):
	def __init__(self, window=None):
		from LeapDevice import LeapDevice

		super().__init__(window)

		self.scale = 8.5
		
		self.gestureTracker = LeapDevice()

	def start(self):
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

	def grab(self):
		x, y = pyMouse.position()
		if self.doGrab(x, y):
			if len(self.grabbedIcons) == 1:
				self.floatingIcon = DraggingIcon(self.grabbedIcons[0], self.window)
						
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
			int(location[0] + delta[0] * self.scale),
			int(location[1] - delta[1] * self.scale)
		)
			
	def setScaling(self, value):
		self.scale = value

	def setGrabThreshold(self, value):
		self.gestureTracker.grabThreshold = value

	def setReleaseThreshold(self, value):
		self.gestureTracker.releaseThreshold = value

	def quit(self):
		self.gestureTracker.exit()

'''
'
'''
class LeapMovesMeScheme(LeapOnlyScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)
		
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))

	def setWindow(self, window):
		super().setWindow(window)
		window.feedbackWindow.showEye()
		self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)

	def grabbed(self, hand):
		gaze = self.gazeTracker.getGaze()
		pyMouse.move(int(gaze[0]), int(gaze[1]))
		super().grab()
		
	def moved(self, delta):
		if self.floatingIcon:
			super().moved(delta)
		
class GazeAndKeyboardScheme(InputScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)
		
		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
		except Exception as exc:
			logging.critical('Eyetribe error: %s', exc)
			raise(Exception('Could not connect to EyeTribe'))
			
	def start(self):
		self.gazeTracker.eyesAppeared.connect(window.feedbackWindow.setEyeGood)
		self.gazeTracker.eyesDisappeared.connect(window.feedbackWindow.setEyeBad)

	def setWindow(self, window):
		super().setWindow(window)
		window.installEventFilter(self)
		window.feedbackWindow.showEye()
		
	def eventFilter(self, widget, event):
		if event.type() == QtCore.QEvent.KeyPress and not event.isAutoRepeat():
			gaze = self.gazeTracker.getGaze()
			self.doGrab(gaze[0], gaze[1])
		elif event.type() == QtCore.QEvent.KeyRelease and not event.isAutoRepeat():
			gaze = self.gazeTracker.getGaze()
			self.doRelease(gaze[0], gaze[1])
            
		return QtGui.QWidget.eventFilter(self, widget, event)

	def quit(self):
		pass

class GazeOnlyScheme(InputScheme):
	def __init__(self, window=None):
		import GazeDevice

		super().__init__(window)

		try:
			self.gazeTracker = GazeDevice.getGazeDevice()
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
		
	def quit(self):
		self.gazeTracker.exit()

'''
'
'''
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
	selected = QtCore.Signal(object)
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle('Project 2 Launcher')
		
		layout = QtGui.QVBoxLayout()
		self.setLayout(layout)
		
		components = [
			{'scheme':'LookGrabLookDropScheme', 'label': 'Look, grab, look'},
			{'scheme':'LeapMovesMeScheme', 'label': 'Look, grab, move'},
			{'scheme':'MouseOnlyScheme', 'label': 'Mouse only'},
			{'scheme':'LeapOnlyScheme', 'label': 'LEAP only'},
			{'scheme':'GazeAndKeyboardScheme', 'label': 'Gaze and button'},
			{'scheme':'GazeOnlyScheme', 'label': 'Gaze only'},
		]
		
		for component in components:
			b = QtGui.QPushButton(component['label'])
			font = b.font()
			font.setPointSize(18)
			b.setFont(font)
			b.clicked.connect(partial(self.startScheme, component['scheme']))
			layout.addWidget(b)
		
	def startScheme(self, scheme):
		self.hide()
		self.selected.emit(scheme)

	def resizeEvent(self, e):
		desktopSize = QtGui.QDesktopWidget().screenGeometry()
		self.move(
			(desktopSize.width() - self.size().width()) / 2,
			(desktopSize.height() - self.size().height()) / 2
		)
