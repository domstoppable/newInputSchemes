import os, random
from PySide import QtGui, QtCore
from FlowLayout import *

class IconLayout(QtGui.QWidget):
	highlight = QtCore.Signal()
	unhighlight = QtCore.Signal()
	blink = QtCore.Signal()

	def __init__(self, image, text):
		super().__init__()
		self.image = image
		self.text = text
		self.highlighted = False

		self.highlight.connect(self._highlight)
		self.unhighlight.connect(self._unhighlight)
		self.blink.connect(self._blink)

		self.imageWidget = QtGui.QLabel()
		self.imageWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.imageWidget.setPixmap(QtGui.QPixmap.fromImage(self.image))

		self.labelWidget = QtGui.QLabel()
		self.labelWidget.setText('<font size="32"><center>%s</center></font>' % self.text)
		
		self.selectionEffect = QtGui.QGraphicsColorizeEffect(self)
		self.setGraphicsEffect(self.selectionEffect)
		self.selectionEffect.setEnabled(False)

		glow = QtGui.QGraphicsDropShadowEffect(self)
		glow.setColor(QtGui.QColor(255, 255, 255))
		glow.setOffset(0, 0)
		glow.setBlurRadius(15)
		self.labelWidget.setGraphicsEffect(glow)

		self.initUI()

	def initUI(self):
		layout = QtGui.QVBoxLayout()
		layout.setSpacing(0)
		self.setLayout(layout)
		
		layout.addWidget(self.imageWidget)
		layout.addWidget(self.labelWidget)
		
		self.setHighlight(False)
		
	@QtCore.Slot()
	def _highlight(self):
		self.setHighlight(True)
		
	@QtCore.Slot()
	def _unhighlight(self):
		self.setHighlight(False)
		
	def toggleHighlight(self):
		self.setHighlight(not self.graphicsEffect().isEnabled())
		
	def setHighlighted(self):
		self.setHighlight(True)
		
	def setUnhighlighted(self):
		self.setHighlight(False)
		
	def setHighlight(self, enabled):
		self.graphicsEffect().setEnabled(enabled)
		self.update()
		
	def _blink(self):
		self.setHighlight(True)
		QtCore.QTimer.singleShot(250, self.setUnhighlighted)

class FolderIcon(IconLayout):
	def initUI(self):
		layout = QtGui.QStackedLayout()
		layout.setStackingMode(layout.StackAll)
		self.setLayout(layout)
		
		layout.addWidget(self.labelWidget)
		layout.addWidget(self.imageWidget)
		
		self.setHighlight(False)

class ImagesWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout(spacing=15)
		container.setLayout(layout)
	
		imagePath = './assets/animals/'
		images = [ f for f in os.listdir(imagePath) if os.path.isfile(os.path.join(imagePath,f)) ]
		random.shuffle(images)
		for imageName in images:
			image = QtGui.QImage(os.path.join(imagePath, imageName)).scaled(150, 150)

			w = IconLayout(image, imageName)
			layout.addWidget(w)


		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Images')
		
class FoldersWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout()
		
		image = QtGui.QImage('assets/folder.svg').scaled(150, 150)
		folderNames = [
			'Cats', 'Cows', 'Dogs', 'Pigs',
			'Rabbits', 'Birds', 'Bugs', 'Vacation',
			'Unsorted', 'Misc.', 'Kids', 'Art',
			'Trip', 'Backup', 'Old', 'Save',
		]
		folderNames = sorted(folderNames)
		for i in range(len(folderNames)):
			w = FolderIcon(image, folderNames[i])
			layout.addWidget(w)

		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Folders')

class FixedQMDISubWindow(QtGui.QMdiSubWindow):
	def __init__(self, child):
		super().__init__()
		self.setWidget(child)
		self.resizeCount = 0
		self.lockedSize = None
		self.lockedPosition = None
#		self.windowStateChanged.connect(self.stateChanged)
		self.setWindowFlags(QtCore.Qt.CustomizeWindowHint|QtCore.Qt.WindowTitleHint)
		
	def moveEvent(self, event):
		if self.resizeCount < 2:
			super().moveEvent(event)
		else:
			super().move(self.lockedPosition)
		
	def resizeEvent(self, event):
		super().resizeEvent(event)
		if self.resizeCount < 2:
			self.resizeCount += 1
			self.lockedSize = self.size()
			self.lockedPosition = self.pos()
		else:
			self.resize(self.lockedSize)
		
class LeapOptionsWindow(QtGui.QWidget):
	scalingChanged = QtCore.Signal(object)
	grabThresholdChanged = QtCore.Signal(object)
	releaseThresholdChanged = QtCore.Signal(object)
	
	def __init__(self, scheme):
		super().__init__()
		
		self.setWindowTitle('LEAP Options')
		
		leapDevice = scheme.gestureTracker
		
		font = self.font()
		font.setStyleHint(QtGui.QFont.Monospace)
		font.setFamily("Courier New")
		font.setPointSize(18)
		self.setFont(font)
		
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		layout = QtGui.QGridLayout()
		layout.setSpacing(20)
		self.setLayout(layout)
		
		scalingBox = QtGui.QDoubleSpinBox()
		scalingBox.setValue(scheme.scale)
		scalingBox.setRange(-20, 20)
		scalingBox.setSingleStep(0.5)
		scalingBox.setSuffix("x")
		scalingBox.valueChanged.connect(self.emitScaleChange)
		
		grabThresholdBox = QtGui.QDoubleSpinBox()
		grabThresholdBox.setValue(100 * leapDevice.listener.grabThreshold)
		grabThresholdBox.setRange(0, 100)
		grabThresholdBox.setSingleStep(1)
		grabThresholdBox.setSuffix("%")
		grabThresholdBox.valueChanged.connect(self.emitGrabThresholdChange)
		
		releaseThresholdBox = QtGui.QDoubleSpinBox()
		releaseThresholdBox.setValue(100 * leapDevice.listener.releaseThreshold)
		releaseThresholdBox.setRange(0, 100)
		releaseThresholdBox.setSingleStep(1)
		releaseThresholdBox.setSuffix("%")
		releaseThresholdBox.valueChanged.connect(self.emitReleaseThresholdChange)
		
		self.currentPinchBox = QtGui.QLabel()
		self.currentPinchBox.setAlignment(QtCore.Qt.AlignRight)
		font.setPointSize(24)
		self.currentPinchBox.setFont(font)

		
		layout.addWidget(QtGui.QLabel('Movement scaling'), 0, 0)
		layout.addWidget(scalingBox, 0, 1)
		
		layout.addWidget(QtGui.QLabel('Grab threshold'), 1, 0)
		layout.addWidget(grabThresholdBox, 1, 1)
		
		layout.addWidget(QtGui.QLabel('Release threshold'), 2, 0)
		layout.addWidget(releaseThresholdBox, 2, 1)
		
		layout.addWidget(QtGui.QLabel('Current pinch value'), 3, 0)
		layout.addWidget(self.currentPinchBox, 3, 1)
		
		leapDevice.pinchValued.connect(self.setPinchValue)
		leapDevice.noHands.connect(self.setPinchValue)
		leapDevice.grabbed.connect(self.grabbed)
		leapDevice.released.connect(self.released)
		
	def emitScaleChange(self, value):
		self.scalingChanged.emit(value)
	
	def emitGrabThresholdChange(self, value):
		self.grabThresholdChanged.emit(value / 100)
	
	def emitReleaseThresholdChange(self, value):
		self.releaseThresholdChanged.emit(value / 100)
		
	def grabbed(self):
		font = self.currentPinchBox.font()
		font.setBold(True)
		self.currentPinchBox.setFont(font)

	def released(self):
		font = self.currentPinchBox.font()
		font.setBold(False)
		self.currentPinchBox.setFont(font)

	def setPinchValue(self, value=None):
		if value is None:
			self.currentPinchBox.setText('')
		else:
			self.currentPinchBox.setText('%.1f%% ' % (100*value))
		
class DragDropTaskWindow(QtGui.QMdiArea):
	mousePressed = QtCore.Signal(object, object)
	mouseReleased = QtCore.Signal(object, object)
	mouseMoved = QtCore.Signal(object, object)
	
	def __init__(self):
		super().__init__()
		self.optionsWindow = None
		
		self.setBackground(QtGui.QColor.fromRgb(0, 0, 0))
		self.addSubWindow(FixedQMDISubWindow(ImagesWindow()))
		self.addSubWindow(FixedQMDISubWindow(FoldersWindow()))
		
		self.setMouseTracking(True)
		
	def setMouseTracking(self, flag):
		def recursive_set(parent):
			for child in parent.findChildren(QtCore.QObject):
				try:
					child.setMouseTracking(flag)
				except:
					pass
				recursive_set(child)
		QtGui.QWidget.setMouseTracking(self, flag)
		recursive_set(self)
		
	def keyPressEvent(self, event):
		super().keyPressEvent(event)
		if event.text() == 'o' and self.optionsWindow is not None:
			self.optionsWindow.show()

		
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.Type.MouseMove:
			self.mouseMoved.emit(obj, event)
		elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
			self.mousePressed.emit(obj, event)
		elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
			self.mouseReleased.emit(obj, event)
			
		return False

if __name__ == '__main__':
	import sys
	app = QtGui.QApplication(sys.argv)
	font = app.font()
	font.setPointSize(18)
	app.setFont(font)
	window = LeapOptions()
	window.show()
	app.exec_()
