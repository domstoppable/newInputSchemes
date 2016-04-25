import logging
import os, random
from PySide import QtGui, QtCore
from FlowLayout import *

import settings, assets

class DragDropTaskWindow(QtGui.QWidget):
	closed = QtCore.Signal()
	mousePressed = QtCore.Signal(object, object)
	mouseReleased = QtCore.Signal(object, object)
	mouseMoved = QtCore.Signal(object, object)
	
	def __init__(self):
		super().__init__()
		self.loaded = False
		self.optionsWindow = None
		self.feedbackWindow = InputFeedbackWindow()
		
		self.mainContainer = QtGui.QWidget(self)
		self.mainContainer.setLayout(QtGui.QHBoxLayout())
		self.mainContainer.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		
		self.foldersWindow = FoldersWindow()
		self.imagesWindow = ImagesWindow()
		self.mainContainer.layout().addWidget(self.foldersWindow)
		self.mainContainer.layout().addWidget(self.imagesWindow)
		
		self.loaded = True
		
		self.feedbackWindow.show()
		
		font = self.font()
		font.setPointSize(18)
		self.setFont(font)
		self.setMouseTracking(True)
		
	def hide(self):
		self.optionsWindow.hide()
		self.feedbackWindow.hide()
		return super().hide()
	
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
			
	def mouseMoveEvent(self, event):
		self.mouseMoved.emit(self, event)
		return super().mouseMoveEvent(event)
		
	def mousePressEvent(self, event):
		self.mousePressed.emit(self, event)
		return super().mousePressEvent(event)
		
	def mouseReleaseEvent(self, event):
		self.mouseReleased.emit(self, event)
		return super().mouseReleaseEvent(event)
		
	def closeEvent(self, e):
		super().closeEvent(e)
		self.hide()
		if self.optionsWindow:
			self.optionsWindow.close()
		if self.feedbackWindow:
			self.feedbackWindow.close()
			
		self.closed.emit()
		
	def resizeEvent(self, e):
		self.mainContainer.resize(self.width(), self.height())

class IconLayout(QtGui.QWidget):
	def __init__(self, image, text):
		super().__init__()

		self.image = image
		self.text = text
		
		self.selected = False
		self.hovered = False

		self.imageWidget = QtGui.QLabel()
		self.imageWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.imageWidget.setPixmap(QtGui.QPixmap.fromImage(self.image))

		if text[0] == '.':
			text = ''
		self.labelWidget = QtGui.QLabel(text)
		self.labelWidget.setAlignment(QtCore.Qt.AlignCenter)
		
		self.setMinimumSize(225, 250)

		self.initUI()

	def initUI(self):
		layout = QtGui.QVBoxLayout()
		layout.setSpacing(0)
		self.setLayout(layout)
		
		layout.addWidget(self.imageWidget)
		layout.addWidget(self.labelWidget)
		
		self.setHovered(False)
		
	def setUnhovered(self):
		self.setHovered(False)
		
	def setHovered(self, enabled=True):
		self.hovered = enabled
		self.update()
		
	def setUnselected(self):
		self.setSelected(False)
		
	def setSelected(self, enabled=True):
		self.selected = enabled
		self.update()

	def blink(self):
		self.setSelected(True)
		QtCore.QTimer.singleShot(500, self.setUnselected)
		
	def paintEvent(self, event):
		super().paintEvent(event)
		if self.selected:
			bg = QtGui.QColor(QtCore.Qt.darkGreen)
			bg.setAlpha(128)
		elif self.hovered:
			bg = QtGui.QColor(QtCore.Qt.darkGreen)
			bg.setAlpha(48)
		else:
			bg = None

		if bg is not None:
			painter = QtGui.QPainter(self)
			painter.setBrush(bg)
			painter.setPen(bg)
			painter.drawRect(0, 0, self.width(), self.height())

class FolderIcon(IconLayout):
	def initUI(self):
		layout = QtGui.QStackedLayout()
		layout.setStackingMode(layout.StackAll)
		self.setLayout(layout)
		
		layout.addWidget(self.labelWidget)
		layout.addWidget(self.imageWidget)
		
		self.setHovered(False)

class ImagesWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout(spacing=0)
		container.setLayout(layout)
	
		images = assets.getFileList('animals')
		random.shuffle(images)
		for imageName in images:
			image = assets.getQImage('animals/%s' % imageName).scaled(200, 175)

			w = IconLayout(image, imageName)
			layout.addWidget(w)

		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Images')
		
	def getRemainingImageCount(self):
		layout = self.widget().layout()
		count = 0
		for i in range(layout.count()):
			if isinstance(layout.itemAt(i).widget(), IconLayout):
				count = count + 1
		return count
		
class FoldersWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout(spacing=0)
		
		image = assets.getQImage('folder.png').scaled(200, 200)
		folderNames = [
			'.1,1',	'.1,2',	'.1,3',	'Cats',
			'.2,1', 'Cows', '.2,3',	'.2,4',
			'.3,1',	'.3,2',	'Dogs',	'.3,4',
			'Pigs',	'.4,2', '.4,3',	'.4,4'
		]
		#folderNames = sorted(folderNames)
		for i in range(len(folderNames)):
			w = FolderIcon(image, folderNames[i])
			layout.addWidget(w)

		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Folders')

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
			True: assets.getQPixmap('eye-good.png'),
			False: assets.getQPixmap('eye-bad.png')
		}
		self.eyeWidget = QtGui.QLabel()
		self.eyeWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.layout.addWidget(self.eyeWidget)

		self._updateIcons()

	def showHand(self):
		self.handImages = {
			True: {
				True: assets.getQPixmap('hand-open-good.png'),
				False: assets.getQPixmap('hand-closed-good.png'),
			},
			False: {
				True: assets.getQPixmap('hand-open-bad.png'),
				False: assets.getQPixmap('hand-closed-bad.png'),
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

class DeviceOptionsWindow(QtGui.QWidget):
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle('Device Options')
		
		self.calibratingGrab = False
		self.gazeTracker = None
		self.gazeCalibrationWindow = None

		self.gestureTracker = None
		
		font = self.font()
		font.setStyleHint(QtGui.QFont.Monospace)
		font.setFamily("Courier New")
		font.setPointSize(18)
		self.setFont(font)
		
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		layout = QtGui.QGridLayout()
		layout.setSpacing(20)
		self.setLayout(layout)
		
		self.tableElementCount = 0
		self.addSystemControls()
		
	def addSystemControls(self):
		def syncGestureAndGazeBoxChanged(state):
			settings.setSystemValue('syncGestureAndGaze', state == QtCore.Qt.Checked)
			
		syncGestureAndGazeBox = QtGui.QCheckBox()
		syncGestureAndGazeBox.setChecked(settings.checkBool(settings.systemValue('syncGestureAndGaze')))
		syncGestureAndGazeBox.stateChanged.connect(syncGestureAndGazeBoxChanged)
		
		self.addElements([
			['<b>-- System Options --</b>'],
			['Sync gesture with gaze', syncGestureAndGazeBox],
		])
		
	def addGestureControls(self, scheme):
		self.gestureTracker = scheme.gestureTracker

		prescaleBox = QtGui.QDoubleSpinBox()
		prescaleBox.setValue(scheme.gestureTracker.getPrescale())
		prescaleBox.setRange(1, 4)
		prescaleBox.setSingleStep(0.25)
		prescaleBox.valueChanged.connect(scheme.gestureTracker.setPrescale)
		
		accelerationBox = QtGui.QDoubleSpinBox()
		accelerationBox.setValue(scheme.gestureTracker.getAcceleration())
		accelerationBox.setRange(1, 4)
		accelerationBox.setSingleStep(0.25)
		accelerationBox.valueChanged.connect(scheme.gestureTracker.setAcceleration)
		
		grabThresholdBox = QtGui.QDoubleSpinBox()
		grabThresholdBox.setValue(scheme.gestureTracker.grabThreshold)
		grabThresholdBox.setRange(0, 100)
		grabThresholdBox.setSingleStep(1)
		grabThresholdBox.setSuffix("%")
		grabThresholdBox.valueChanged.connect(scheme.gestureTracker.setGrabThreshold)
		
		releaseThresholdBox = QtGui.QDoubleSpinBox()
		releaseThresholdBox.setValue(scheme.gestureTracker.releaseThreshold)
		releaseThresholdBox.setRange(0, 100)
		releaseThresholdBox.setSingleStep(1)
		releaseThresholdBox.setSuffix("%")
		releaseThresholdBox.valueChanged.connect(scheme.gestureTracker.setReleaseThreshold)

		pinchThresholdBox = QtGui.QDoubleSpinBox()
		pinchThresholdBox.setValue(scheme.gestureTracker.pinchThreshold)
		pinchThresholdBox.setRange(0, 100)
		pinchThresholdBox.setSingleStep(1)
		pinchThresholdBox.setSuffix("%")
		pinchThresholdBox.valueChanged.connect(scheme.gestureTracker.setPinchThreshold)
		
		unpinchThresholdBox = QtGui.QDoubleSpinBox()
		unpinchThresholdBox.setValue(scheme.gestureTracker.unpinchThreshold)
		unpinchThresholdBox.setRange(0, 100)
		unpinchThresholdBox.setSingleStep(1)
		unpinchThresholdBox.setSuffix("%")
		unpinchThresholdBox.valueChanged.connect(scheme.gestureTracker.setUnpinchThreshold)		
		
		font = self.font()
		font.setPointSize(24)
		self.currentGrabBox = QtGui.QLabel()
		self.currentGrabBox.setAlignment(QtCore.Qt.AlignRight)
		self.currentGrabBox.setFont(font)

		self.currentPinchBox = QtGui.QLabel()
		self.currentPinchBox.setAlignment(QtCore.Qt.AlignLeft)
		self.currentPinchBox.setFont(font)
		
		dwellDurationBox = QtGui.QDoubleSpinBox()
		dwellDurationBox.setValue(scheme.gestureTracker.getDwellDuration())
		dwellDurationBox.setRange(0, 5)
		dwellDurationBox.setSingleStep(.1)
		dwellDurationBox.setSuffix("s")
		dwellDurationBox.valueChanged.connect(scheme.gestureTracker.setDwellDuration)
		
		dwellRangeBox = QtGui.QDoubleSpinBox()
		dwellRangeBox.setValue(scheme.gestureTracker.getDwellRange())
		dwellRangeBox.setRange(0, 10)
		dwellRangeBox.setSingleStep(.5)
		dwellRangeBox.valueChanged.connect(scheme.gestureTracker.setDwellRange)
		
		attentionDurationBox = QtGui.QDoubleSpinBox()
		attentionDurationBox.setValue(scheme.gestureTracker.getAttentionStalePeriod())
		attentionDurationBox.setRange(0, 5)
		attentionDurationBox.setSingleStep(.1)
		attentionDurationBox.setSuffix("s")
		attentionDurationBox.valueChanged.connect(scheme.gestureTracker.setAttentionStalePeriod)
		
		self.calibrateButton = QtGui.QPushButton('Calibrate grab')
		self.calibrateButton.setCheckable(True)
		self.calibrateButton.clicked.connect(self.toggleCalibration)
		
		self.addElements([
			['<b>-- Gesture Options --</b>'],
			[self.calibrateButton, self.currentGrabBox],
			['Movement prescale', prescaleBox],
			['Movement acceleration', accelerationBox],
			['Grab threshold', grabThresholdBox],
			['Release threshold', releaseThresholdBox],
			['Dwell duration', dwellDurationBox],
			['Dwell range', dwellRangeBox],
			['Attention memory', attentionDurationBox],
#			['Pinch threshold', pinchThresholdBox],
#			['Unpinch threshold', unpinchThresholdBox],
#			['Current pinch value', self.currentPinchBox],
		])
		
		scheme.gestureTracker.grabValued.connect(self.setGrabValue)
		scheme.gestureTracker.pinchValued.connect(self.setPinchValue)
		scheme.gestureTracker.noHands.connect(self.setGrabValue)
		scheme.gestureTracker.grabbed.connect(self.grabbed)
		scheme.gestureTracker.released.connect(self.released)
		
	def addGazeControls(self, gazeTracker):
		self.gazeTracker = gazeTracker
		dwellDurationBox = QtGui.QDoubleSpinBox()
		dwellDurationBox.setValue(gazeTracker.getDwellDuration())
		dwellDurationBox.setRange(0, 5)
		dwellDurationBox.setSingleStep(.1)
		dwellDurationBox.setSuffix("s")
		dwellDurationBox.valueChanged.connect(gazeTracker.setDwellDuration)
		
		dwellRangeBox = QtGui.QDoubleSpinBox()
		dwellRangeBox.setValue(gazeTracker.getDwellRange())
		dwellRangeBox.setRange(0, 500)
		dwellRangeBox.setSingleStep(10)
		dwellRangeBox.setSuffix("px")
		dwellRangeBox.valueChanged.connect(gazeTracker.setDwellRange)
		
		attentionDurationBox = QtGui.QDoubleSpinBox()
		attentionDurationBox.setValue(gazeTracker.getAttentionStalePeriod())
		attentionDurationBox.setRange(0, 5)
		attentionDurationBox.setSingleStep(.1)
		attentionDurationBox.setSuffix("s")
		attentionDurationBox.valueChanged.connect(gazeTracker.setAttentionStalePeriod)

		calibrateButton = QtGui.QPushButton('Calibrate gaze')
		calibrateButton.setCheckable(True)
		calibrateButton.clicked.connect(self.showGazeCalibration)
		
		self.addElements([
			['<b>-- Gaze options --</b>', None],
			[calibrateButton, ''],
			['Dwell duration', dwellDurationBox],
			['Dwell range', dwellRangeBox],
			['Attention memory', attentionDurationBox],
		])
		
	def showGazeCalibration(self):
		from GazeCalibrationWindow import CalibrationWindow
		self.gazeCalibrationWindow = CalibrationWindow(self.gazeTracker)
		self.gazeCalibrationWindow.show()
		
	def addElements(self, tableElements):
		for elements in tableElements:
			for column, element in enumerate(elements):
				if element is None:
					continue
				if not isinstance(element, QtGui.QWidget):
					element = QtGui.QLabel(element)
				self.layout().addWidget(element, self.tableElementCount, column)
			
			self.tableElementCount = self.tableElementCount + 1

	def startGrabCalibration(self):
		self.calibratingGrab = True
		
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
		self.gestureTracker.toggleCalibration()
		self.calibrateButton.setChecked(self.gestureTracker.calibrating)

if __name__ == '__main__':
	import sys
	app = QtGui.QApplication(sys.argv)
	font = app.font()
	font.setPointSize(18)
	app.setFont(font)
	window = LeapOptions()
	window.show()
	app.exec_()
