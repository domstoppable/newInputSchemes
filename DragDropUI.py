import logging
import os, random
from PySide import QtGui, QtCore
from FlowLayout import *

class DragDropTaskWindow(QtGui.QMdiArea):
	mousePressed = QtCore.Signal(object, object)
	mouseReleased = QtCore.Signal(object, object)
	mouseMoved = QtCore.Signal(object, object)
	
	def __init__(self):
		super().__init__()
		self.loaded = False
		self.optionsWindow = None
		self.feedbackWindow = InputFeedbackWindow()
		
		self.setBackground(QtGui.QColor.fromRgb(0, 0, 0))
		self.foldersWindow = FoldersWindow()
		self.imagesWindow = ImagesWindow()
		self.addSubWindow(FixedQMDISubWindow(self.foldersWindow))
		self.addSubWindow(FixedQMDISubWindow(self.imagesWindow))
		
		self.setMouseTracking(True)
		self.loaded = True
		
		self.feedbackWindow.show()
		self.gazeCalibrationWindow = None
		
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
	
	def getRemainingImageCount(self):
		return self.imagesWindow.getRemainingImageCount()
	
	def keyPressEvent(self, event):
		super().keyPressEvent(event)
		if event.text() == 'o' and self.optionsWindow is not None:
			self.optionsWindow.show()
		
	def eventFilter(self, obj, event):
		if not self.loaded:
			return False

		if event.type() == QtCore.QEvent.Type.MouseMove:
			self.mouseMoved.emit(obj, event)
			return True
		elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
			self.mousePressed.emit(obj, event)
			return True
		elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
			self.mouseReleased.emit(obj, event)
			return True

		return False
		
	def closeEvent(self, e):
		super().closeEvent(e)
		if self.optionsWindow:
			self.optionsWindow.close()
		if self.feedbackWindow:
			self.feedbackWindow.close()

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
			image = QtGui.QImage(os.path.join(imagePath, imageName)).scaled(200, 200)

			w = IconLayout(image, imageName)
			layout.addWidget(w)

		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Images')
		
	def getRemainingImageCount(self):
		return self.widget().layout().count()
		
class FoldersWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout(spacing=30)
		
		image = QtGui.QImage('assets/folder.png').scaled(200, 200)
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

class InputFeedbackWindow(QtGui.QWidget):
	def __init__(self):
		super().__init__()
		
		self.layout = QtGui.QVBoxLayout()
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
		self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

		self.setLayout(self.layout)
		
		self.eyeWidget = None
		self.handWidget = None
		
		self.eyeImages = None
		self.handImages = None
		
		self.eyeGood = False
		self.handGood = False
		self.handOpen = True
		
	def resizeEvent(self, e):
		desktopSize = QtGui.QDesktopWidget().screenGeometry()
		self.move(
			(desktopSize.width() - self.size().width()) / 2,
			desktopSize.height() - self.size().height()
		)

	def showEye(self):
		self.eyeImages = {
			True: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/eye-good.png')),
			False: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/eye-bad.png'))
		}
		self.eyeWidget = QtGui.QLabel()
		self.eyeWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.eyeWidget)

		self._updateIcons()

	def showHand(self):
		self.handImages = {
			True: {
				True: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/hand-open-good.png')),
				False: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/hand-closed-good.png')),
			},
			False: {
				True: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/hand-open-bad.png')),
				False: QtGui.QPixmap.fromImage(QtGui.QImage('./assets/hand-closed-bad.png')),
			},
		}
		self.handWidget = QtGui.QLabel()
		self.handWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.handWidget)
			
		self._updateIcons()
	
	def _updateIcons(self):
		if self.eyeWidget is not None:
			self.eyeWidget.setPixmap(self.eyeImages[self.eyeGood])
		
		if self.handWidget is not None:
			self.handWidget.setPixmap(self.handImages[self.handGood][self.handOpen])
			
	def setHandGood(self):
		logging.debug("Hand good")
		self.handGood = True
		self._updateIcons()
	
	def setHandBad(self):
		logging.debug("Hand bad")
		self.handGood = False
		self._updateIcons()
	
	def setHandOpen(self):
		logging.debug("Hand open")
		self.handOpen = True
		self._updateIcons()
	
	def setHandClosed(self):
		logging.debug("Hand closed")
		self.handOpen = False
		self._updateIcons()

	def setEyeGood(self):
		logging.debug("Eyes good")
		self.eyeGood = True
		self._updateIcons()
		
	def setEyeBad(self):
		logging.debug("Eyes bad")
		self.eyeGood = False
		self._updateIcons()

class LeapOptionsWindow(QtGui.QWidget):
	scalingChanged = QtCore.Signal(object)
	grabThresholdChanged = QtCore.Signal(object)
	pinchThresholdChanged = QtCore.Signal(object)
	releaseThresholdChanged = QtCore.Signal(object)
	unpinchThresholdChanged = QtCore.Signal(object)
	
	def __init__(self, scheme):
		super().__init__()
		
		self.setWindowTitle('LEAP Options')
		
		self.leapDevice = scheme.gestureTracker
		self.calibratingGrab = False
		
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
		grabThresholdBox.setValue(100 * self.leapDevice.grabThreshold)
		grabThresholdBox.setRange(0, 100)
		grabThresholdBox.setSingleStep(1)
		grabThresholdBox.setSuffix("%")
		grabThresholdBox.valueChanged.connect(self.emitGrabThresholdChange)
		
		pinchThresholdBox = QtGui.QDoubleSpinBox()
		pinchThresholdBox.setValue(100 * self.leapDevice.pinchThreshold)
		pinchThresholdBox.setRange(0, 100)
		pinchThresholdBox.setSingleStep(1)
		pinchThresholdBox.setSuffix("%")
		pinchThresholdBox.valueChanged.connect(self.emitPinchThresholdChange)
		
		unpinchThresholdBox = QtGui.QDoubleSpinBox()
		unpinchThresholdBox.setValue(100 * self.leapDevice.unpinchThreshold)
		unpinchThresholdBox.setRange(0, 100)
		unpinchThresholdBox.setSingleStep(1)
		unpinchThresholdBox.setSuffix("%")
		unpinchThresholdBox.valueChanged.connect(self.emitUnpinchThresholdChange)
		
		releaseThresholdBox = QtGui.QDoubleSpinBox()
		releaseThresholdBox.setValue(100 * self.leapDevice.releaseThreshold)
		releaseThresholdBox.setRange(0, 100)
		releaseThresholdBox.setSingleStep(1)
		releaseThresholdBox.setSuffix("%")
		releaseThresholdBox.valueChanged.connect(self.emitReleaseThresholdChange)
		
		self.currentGrabBox = QtGui.QLabel()
		self.currentGrabBox.setAlignment(QtCore.Qt.AlignRight)
		font.setPointSize(24)
		self.currentGrabBox.setFont(font)

		self.currentPinchBox = QtGui.QLabel()
		self.currentPinchBox.setAlignment(QtCore.Qt.AlignLeft)
		font.setPointSize(24)
		self.currentPinchBox.setFont(font)
		
		self.calibrateButton = QtGui.QPushButton('Current grab value')
		self.calibrateButton.setCheckable(True)
		self.calibrateButton.clicked.connect(self.toggleCalibration)
		
		tableElements = [
			['Movement scaling', scalingBox],
			['Grab threshold', grabThresholdBox],
			['Release threshold', releaseThresholdBox],
			[self.calibrateButton, self.currentGrabBox],
			['Pinch threshold', pinchThresholdBox],
			['Unpinch threshold', unpinchThresholdBox],
			['Current pinch value', self.currentPinchBox],
		]
		for index, elements in enumerate(tableElements):
			if not isinstance(elements[0], QtGui.QWidget):
				elements[0] = QtGui.QLabel(elements[0])
			layout.addWidget(elements[0], index, 0)
			layout.addWidget(elements[1], index, 1)

		self.leapDevice.grabValued.connect(self.setGrabValue)
		self.leapDevice.pinchValued.connect(self.setPinchValue)
		self.leapDevice.noHands.connect(self.setGrabValue)
		self.leapDevice.grabbed.connect(self.grabbed)
		self.leapDevice.released.connect(self.released)
		
	def startGrabCalibration(self):
		self.calibratingGrab = True
		
	def emitScaleChange(self, value):
		self.scalingChanged.emit(value)
	
	def emitGrabThresholdChange(self, value):
		self.grabThresholdChanged.emit(value / 100)
	
	def emitReleaseThresholdChange(self, value):
		self.releaseThresholdChanged.emit(value / 100)
		
	def emitPinchThresholdChange(self, value):
		self.grabThresholdChanged.emit(value / 100)
	
	def emitUnpinchThresholdChange(self, value):
		self.releaseThresholdChanged.emit(value / 100)
		
	def grabbed(self):
		font = self.currentGrabBox.font()
		font.setBold(True)
		self.currentGrabBox.setFont(font)

	def released(self):
		font = self.currentGrabBox.font()
		font.setBold(False)
		self.currentGrabBox.setFont(font)

	def setGrabValue(self, value=None):
		if value is None:
			self.currentGrabBox.setText('')
		else:
			self.currentGrabBox.setText('%.1f%% ' % (100*value))
	
	def setPinchValue(self, value=None):
		if value is None:
			self.currentPinchBox.setText('')
		else:
			self.currentPinchBox.setText('%.1f%% ' % (100*value))
	
	def toggleCalibration(self):		
		self.leapDevice.toggleCalibration()
		self.calibrateButton.setChecked(self.leapDevice.calibrating)
		


if __name__ == '__main__':
	import sys
	app = QtGui.QApplication(sys.argv)
	font = app.font()
	font.setPointSize(18)
	app.setFont(font)
	window = LeapOptions()
	window.show()
	app.exec_()
