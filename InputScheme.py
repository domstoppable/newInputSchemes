from PySide import QtGui, QtCore
from DragDropUI import IconLayout, FolderIcon
from functools import partial
import sound
import time

from selectionDetector import DwellSelect, Point

from LeapDevice import LeapDevice
from peyetribe import EyeTribe

'''
'
'''
class InputScheme(QtCore.QObject):
	imageMoved = QtCore.Signal(object, object)
	def __init__(self, window):

		super().__init__()
		self.grabbedIcon = None
		self.destination = None
		self.window = window

	def quit(self):
		pass
		
	def findWidgetAt(self, x, y):
		widget = QtGui.QApplication.instance().widgetAt(x, y)
		while widget != None:
			if isinstance(widget, IconLayout):
				return widget
			else:
				widget = widget.parentWidget()
		return widget

	def doGrab(self, x, y):
		widget = self.findWidgetAt(x, y)
		if widget is not None and not isinstance(widget, FolderIcon):
			self.grabImage(widget)
			return True
		else:
			sound.play("bummer.wav")			
			return False

	def doRelease(self, x, y):
		if self.grabbedIcon == None:
			return False

		widget = QtGui.QApplication.instance().widgetAt(x, y)
		while widget != None:
			if isinstance(widget, FolderIcon):
				self.moveImage(widget)
				return True
			else:
				widget = widget.parentWidget()
				
		if widget == None:
			self.releaseImage()
			
		return False
			
	def grabImage(self, image):
		self.grabbedIcon = image
		self.grabbedIcon._highlight()
		
		sound.play("select.wav")
		
	def moveImage(self, folder):
		self.destination = folder
		QtCore.QTimer.singleShot(0, self._moveImage)
		
	def _moveImage(self):
		folder = self.destination
		if self.grabbedIcon == None:
			return

		p = self.grabbedIcon.parentWidget()
		p.layout().removeWidget(self.grabbedIcon)
		self.grabbedIcon.setParent(None)
		
		print("Emitting")
		self.imageMoved.emit(self.grabbedIcon.text, folder.text)
		
		self.grabbedIcon = None
		folder.blink.emit()
		sound.play("drop.wav")

	def releaseImage(self):
		QtCore.QTimer.singleShot(0, self._releaseImage)
		
	def _releaseImage(self):
		if self.grabbedIcon == None:
			return
			
		self.grabbedIcon.unhighlight.emit()
		self.grabbedIcon = None
		sound.play("release.wav")
		
	def isGrabbing(self):
		return self.grabbedIcon != None

'''
'
'''
class LookGrabLookDropScheme(InputScheme):
	def __init__(self, window):
		super().__init__(window)
		
		self.gestureTracker = LeapDevice()
		try:
			self.gazeTracker = EyeTribe()		
			self.gazeTracker.connect()
		except:
			print("Could not connect to EyeTribe")
			
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)
		self.scale = 0

	def grabbed(self, hand):
		gaze = self.getGaze()
		self.doGrab(gaze[0], gaze[1])
		
	def released(self, hand):
		gaze = self.getGaze()
		self.doRelease(gaze[0], gaze[1])

	def getGaze(self):
		gazeFrame = None
		try:
			gazeFrame = self.gazeTracker.next()
		except:
			print("Could not collect gaze data")
			
		#if gazeFrame.state == peyetribe.STATE_TRACKING_GAZE:
		if gazeFrame != None and gazeFrame.state < 0x8:
			return (gazeFrame.avg.x, gazeFrame.avg.y)
		else:
			sound.play("bummer.wav")
			pos = QtGui.QCursor.pos()
			return (pos.x(), pos.y())

	def setScaling(self, value):
		pass

	def setGrabThreshold(self, value):
		self.gestureTracker.listener.grabThreshold = value

	def setReleaseThreshold(self, value):
		self.gestureTracker.listener.releaseThreshold = value
		
	def quit(self):
		self.gestureTracker.exit()

'''
'
'''
class LeapMovesMeScheme(LookGrabLookDropScheme):
	def __init__(self, window):
		super().__init__(window)
		
		self.scale = 8.5
		self.floatingIcon = None
		self.gestureTracker.moved.connect(self.moved)

	def grabbed(self, hand):
		super().grabbed(hand)
		
		if self.grabbedIcon != None:
			self.floatingIcon = DraggingIcon(self.grabbedIcon, self.window)

	def released(self, hand):
		if self.floatingIcon == None:
			return

		self.floatingIcon.hide()

		center = self.floatingIcon.geometry().center()
		super().doRelease(center.x(), center.y())

		self.floatingIcon.close()
		self.floatingIcon = None

	def moved(self, delta):
		if self.floatingIcon:
			self.floatingIcon.moveBy(
				delta[0] * self.scale,
				delta[1] * self.scale
			)
			
	def setScaling(self, value):
		self.scale = value

	def setGrabThreshold(self, value):
		self.gestureTracker.listener.grabThreshold = value

	def setReleaseThreshold(self, value):
		self.gestureTracker.listener.releaseThreshold = value
		
'''
'
'''
class MouseOnlyScheme(InputScheme):
	def __init__(self, window):
		super().__init__(window)
		
		self.connectEvents()
		self.floatingIcon = None
		self.mouseStartPoint = None
		
	def connectEvents(self):
		if self.window == None:
			QtCore.QTimer.singleShot(100, self.connectEvents)
		else:
			self.window.mousePressed.connect(self.grab)
			self.window.mouseReleased.connect(self.release)
			self.window.mouseMoved.connect(self.move)
			print("Events connected")
		
	def grab(self, obj, mouseEvent):
		if self.grabbedIcon == None:
			pos = obj.mapToGlobal(mouseEvent.pos())
			if self.doGrab(pos.x(), pos.y()):
				self.floatingIcon = DraggingIcon(self.grabbedIcon, self.window, mouseEvent.pos())
				self.mouseStartPoint = mouseEvent.pos()
				self.move(obj, mouseEvent)
				
	def release(self, obj, mouseEvent):
		if self.floatingIcon == None:
			return
		pos = obj.mapToGlobal(mouseEvent.pos())
		self.floatingIcon.hide()

		self.doRelease(pos.x(), pos.y())
		
		self.floatingIcon.close()
		self.floatingIcon = None
		
	def move(self, obj, mouseEvent):
		if self.floatingIcon:
			p = obj.mapToGlobal(mouseEvent.pos())
				
			self.floatingIcon.move(
				p.x() - self.floatingIcon.width()/2,
				p.y() - self.floatingIcon.height()/2
			)
'''
'
'''
class LeapOnlyScheme(MouseOnlyScheme):
	def __init__(self, window):
		super().__init__(window)

		from LeapDevice import LeapDevice
		from pymouse import PyMouse
		
		self.scale = 8.5
		
		self.gestureTracker = LeapDevice()
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)
		self.gestureTracker.moved.connect(self.moved)
		
		self.mouse = PyMouse()
		
	def grab(self, obj, mouseEvent):
		if self.grabbedIcon == None:
			pos = obj.mapToGlobal(mouseEvent.pos())
			if self.doGrab(pos.x(), pos.y()):
				self.floatingIcon = DraggingIcon(self.grabbedIcon, self.window, mouseEvent.pos())
				self.mouseStartPoint = mouseEvent.pos()
				self.move(obj, mouseEvent)
						
	def grabbed(self, hand):
		location = self.mouse.position()
		self.mouse.press(location[0], location[1])

	def released(self, hand):
		location = self.mouse.position()
		self.mouse.release(location[0], location[1])
		
	def moved(self, delta):
		location = self.mouse.position()
		self.mouse.move(
			int(location[0] + delta[0] * self.scale),
			int(location[1] - delta[1] * self.scale)
		)
		if self.floatingIcon:
			self.floatingIcon.moveBy(delta)
			
	def setScaling(self, value):
		self.scale = value

	def setGrabThreshold(self, value):
		self.gestureTracker.listener.grabThreshold = value

	def setReleaseThreshold(self, value):
		self.gestureTracker.listener.releaseThreshold = value

	def quit(self):
		self.gestureTracker.exit()

class GazeAndKeyboard(InputScheme):
	def __init__(self, window):
		super().__init__(window)
		
		try:
			self.gazeTracker = EyeTribe()		
			self.gazeTracker.connect()
		except:
			print("Could not connect to EyeTribe")
			
		window.installEventFilter(self)
		
	def eventFilter(self, widget, event):
		if (event.type() == QtCore.QEvent.KeyPress):
			key = event.key()
			gaze = self.getGaze()
			if self.isGrabbing():
				self.doRelease(gaze[0], gaze[1])
			else:
				self.doGrab(gaze[0], gaze[1])
            
		return QtGui.QWidget.eventFilter(self, widget, event)

	def getGaze(self):
		gazeFrame = None
		try:
			gazeFrame = self.gazeTracker.next()
		except:
			print("Could not collect gaze data")
			
		#if gazeFrame.state == peyetribe.STATE_TRACKING_GAZE:
		if gazeFrame != None and gazeFrame.state < 0x8:
			return (gazeFrame.avg.x, gazeFrame.avg.y)
		else:
			sound.play("bummer.wav")
			pos = QtGui.QCursor.pos()
			return (pos.x(), pos.y())

	def quit(self):
		pass

class GazeOnly(InputScheme):
	def __init__(self, window):
		super().__init__(window)
		self.timeToStop = False
		self.detector = DwellSelect(.33, 75)

		try:
			self.gazeTracker = EyeTribe()		
			self.gazeTracker.connect()
		except:
			print("Could not connect to EyeTribe")
		
		self.fixationStartTime = None
		self.fixationWidget = None
	
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.loop)
		self.timer.start(1000 / 30)

	def loop(self):
		gazeFrame = self.gazeTracker.next()
		if gazeFrame != None and gazeFrame.state < 0x8:
			currentTime = time.time()
			point = Point(
				gazeFrame.avg.x,
				gazeFrame.avg.y,
				0,
				currentTime,
				gazeFrame.avg
			)
			self.detector.addPoint(point)
			if self.detector.selection != None:
				selection = self.detector.clearSelection()
				if self.isGrabbing():
					print("Release")
					self.doRelease(selection.x, selection.y)
				else:
					print("Grab")
					self.doGrab(selection.x, selection.y)
	
	def quit(self):
		self.timeToStop = True

'''
'
'''
class DraggingIcon(QtGui.QMdiSubWindow):
	def __init__(self, fromIcon, parentWindow, offset=None):
		super().__init__()
		
		icon = QtGui.QLabel()
		icon.setPixmap(QtGui.QPixmap.fromImage(fromIcon.image.scaled(75, 75)))
		self.setWidget(icon)
		
		parentWindow.addSubWindow(self, QtCore.Qt.FramelessWindowHint)
		
		if offset == None:
			offset = QtCore.QPoint(75, 75)
		pos = fromIcon.mapToGlobal(fromIcon.imageWidget.rect().center())
		
		self.move(pos.x() , pos.y() )
		self.show()

	def moveBy(self, delta, delta2=None):
		if delta2 is not None:
			delta = [delta, delta2]
			
		pos = [
			self.x() + delta[0],
			self.y() - delta[1]
		]
		self.move(pos[0], pos[1])


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
			{'scheme':'GazeAndKeyboard', 'label': 'Gaze and button'},
			{'scheme':'GazeOnly', 'label': 'Gaze only'},
		]
		
		for component in components:
			b = QtGui.QPushButton(component['label'])
			font = b.font()
			font.setPointSize(18)
			b.setFont(font)
			b.clicked.connect(partial(self.startScheme, component['scheme']))
			layout.addWidget(b)
		
	def startScheme(self, scheme):
		self.destroy()
		self.selected.emit(scheme)
