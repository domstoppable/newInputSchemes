from PySide import QtGui, QtCore
from DragDropUI import IconLayout, FolderIcon
import sound

'''
'
'''
class InputScheme(QtCore.QObject):
	def __init__(self):
		super(QtCore.QObject).__init__()
		self.grabbedIcon = None
		self.destination = None

	def quit(self):
		pass

	def doGrab(self, x, y):
		widget = QtGui.QApplication.instance().widgetAt(x, y)
		while widget != None:
			if isinstance(widget, IconLayout) and not isinstance(widget, FolderIcon):
				self.grabImage(widget)
				return True
			else:
				widget = widget.parentWidget()
		
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
		
		print("Moved %s to %s" % (self.grabbedIcon.text, folder.text))
		
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

'''
'
'''
class LookGrabLookDropScheme(InputScheme):
	def __init__(self):
		super().__init__()
		
		from LeapDevice import LeapDevice
		from peyetribe import EyeTribe
		
		self.gestureTracker = LeapDevice()
		try:
			self.gazeTracker = EyeTribe()		
			self.gazeTracker.connect()
		except:
			print("Could not connect to EyeTribe")
			
		self.gestureTracker.grabbed.connect(self.grabbed)
		self.gestureTracker.released.connect(self.released)

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

	def quit(self):
		self.gestureTracker.exit()

'''
'
'''
class LeapMovesMeScheme(LookGrabLookDropScheme):
	def __init__(self):
		super().__init__()
		self.floatingIcon = None
		self.gestureTracker.moved.connect(self.moved)

	def grabbed(self, hand):
		super().grabbed(hand)
		
		if self.grabbedIcon != None:
			self.floatingIcon = DraggingIcon(self.grabbedIcon)

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
			self.floatingIcon.moveBy(delta)
		
'''
'
'''
class MouseOnlyScheme(InputScheme):
	def __init__(self):
		super().__init__()
		
		self.connectEvents()
		self.floatingIcon = None
		self.mouseStartPoint = None
		
	def connectEvents(self):
		window = QtGui.QApplication.instance().activeWindow()
		
		if window == None:
			QtCore.QTimer.singleShot(100, self.connectEvents)
		else:
			window.mousePressed.connect(self.grab)
			window.mouseReleased.connect(self.release)
			window.mouseMoved.connect(self.move)
			print("Events connected")
		
	def grab(self, obj, mouseEvent):
		if self.grabbedIcon == None:
			pos = obj.mapToGlobal(mouseEvent.pos())
			if self.doGrab(pos.x(), pos.y()):
				self.floatingIcon = DraggingIcon(self.grabbedIcon, mouseEvent.pos())
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
class DraggingIcon(QtGui.QMdiSubWindow):
	def __init__(self, fromIcon, offset=None):
		super().__init__()
		
		icon = QtGui.QLabel()
		icon.setPixmap(QtGui.QPixmap.fromImage(fromIcon.image.scaled(75, 75)))
		self.setWidget(icon)
		
		QtGui.QApplication.instance().activeWindow().addSubWindow(self, QtCore.Qt.FramelessWindowHint)
		
		if offset == None:
			offset = QtCore.QPoint(75, 75)
		pos = fromIcon.mapToGlobal(fromIcon.imageWidget.rect().center())
		
		self.move(pos.x() , pos.y() )
		self.show()

	def moveBy(self, delta):
		pos = [
			self.x() + delta[0] * 10,
			self.y() - delta[1] * 10
		]
		self.move(pos[0], pos[1])
