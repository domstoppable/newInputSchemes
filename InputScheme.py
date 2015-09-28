from PySide import QtGui, QtCore
from IconLayout import *
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

	def grabbed(self, hand):
		gaze = self.getGaze()
		
		widget = QtGui.QApplication.instance().widgetAt(gaze[0], gaze[1])
		while widget != None:
			if isinstance(widget, IconLayout):
				if ".jpg" in widget.text:
					self.grabImage(widget)
				break
			else:
				widget = widget.parentWidget()
		if self.grabbedIcon == None:
			sound.play("bummer.wav")
		
	def released(self, hand):
		if self.grabbedIcon == None:
			return

		target = self.getTarget()
		widget = QtGui.QApplication.instance().widgetAt(target[0], target[1])
		
		while widget != None:
			if isinstance(widget, FolderIcon):
				self.moveImage(widget)
				break
			else:
				widget = widget.parentWidget()
				
		if widget == None:
			self.releaseImage()
			
	def getTarget(self):
		return self.getGaze()
	
	def quit(self):
		self.gestureTracker.exit()

'''
'
'''
class LeapMovesMeScheme(LookGrabLookDropScheme):
	def __init__(self):
		super().__init__()
		self.floatingIcon = None
		self.gestureTracker.moved.connect(self.moveFloater)

	def grabbed(self, hand):
		super().grabbed(hand)
		
		if self.grabbedIcon != None:
			self.floatingIcon = DraggingIcon(self.grabbedIcon)

	def released(self, hand):
		if self.floatingIcon == None:
			return
			
		self.floatingIcon.hide()
		super().released(hand)
		
		self.floatingIcon.close()
		self.floatingIcon = None

	def moveFloater(self, delta):
		if self.floatingIcon:
			self.floatingIcon.moveBy(delta)
		
	def getTarget(self):
		center = self.floatingIcon.geometry().center()
		return (center.x(), center.y())
	
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
			QtCore.QTimer.singleShot(10, self.connectEvents)
		else:
			window.mousePressed.connect(self.grab)
			window.mouseReleased.connect(self.release)
			window.mouseMoved.connect(self.move)
		
	def grab(self, obj, mouseEvent):
		if isinstance(obj, IconLayout) and not isinstance(obj, FolderIcon):
			self.grabImage(obj)
			self.floatingIcon = DraggingIcon(self.grabbedIcon, mouseEvent.pos())
			self.mouseStartPoint = obj.mapToGlobal(mouseEvent.pos())

	def release(self, obj, mouseEvent):
		if self.floatingIcon == None:
			return
			
		self.floatingIcon.hide()
		p = obj.mapToGlobal(mouseEvent.pos())
		widget = QtGui.QApplication.instance().widgetAt(p)
		while widget != None:
			if isinstance(widget, IconLayout):
				if ".jpg" not in widget.text:
					self.moveImage(widget)
				break
			else:
				widget = widget.parentWidget()
				
		self.releaseImage()
		
		if self.floatingIcon:
			self.floatingIcon.close()
			self.floatingIcon = None
		
	def move(self, obj, mouseEvent):
		if self.floatingIcon:
			p = obj.mapToGlobal(mouseEvent.pos())
			delta = [
				p.x() - self.mouseStartPoint.x(),
				self.mouseStartPoint.y() - p.y()
			]
			self.floatingIcon.moveBy(delta)
		
'''
'
'''
class DraggingIcon(QtGui.QMdiSubWindow):
	def __init__(self, fromIcon, offset=None):
		super().__init__()
		
		if offset == None:
			offset = QtCore.QPoint(75, 75)
		offset = offset + QtCore.QPoint(-38, -38)
		self.startPoint = fromIcon.mapToGlobal(fromIcon.rect().topLeft()) + offset
		
		icon = QtGui.QLabel()
		icon.setPixmap(QtGui.QPixmap.fromImage(fromIcon.image.scaled(75, 75)))
		self.setWidget(icon)
		
		QtGui.QApplication.instance().activeWindow().addSubWindow(self, QtCore.Qt.FramelessWindowHint)
		
		self.move(self.startPoint)
		self.show()

	def moveBy(self, delta):
		pos = [
			self.startPoint.x() + delta[0],
			self.startPoint.y() - delta[1]
		]
		self.move(pos[0], pos[1])
