from math import atan2, degrees, pi, sqrt, pow
import logging

from PySide import QtGui, QtCore

xResolution, yResolution = 3, 3
instructions = '''
	Please sit comfortably.
	A target will appear on the screen.
	Follow the target with your eyes.
	
	Press any key to begin gaze calibration
'''.replace('\n', '<br>')

class CalibrationWindow(QtGui.QWidget):
	closed = QtCore.Signal()

	def __init__(self, device=None):
		super().__init__()
		if device is None:
			import GazeDevice
			self.gazeTracker = GazeDevice.getGazeDevice()
		else:
			self.gazeTracker = device
			
		self.setStyleSheet("background-color: #ddd;");
			
		self.movementTime = 750
		self.pointCaptureDelay = 500
		self.pointCaptureDuration = 1000

		self.started = False
		self.eyes = EyeballWidget(self)
		self.target = TargetWidget(parent=self)
		self.target.hide()

		self.eyeTimer = QtCore.QTimer()
		self.eyeTimer.setSingleShot(False)
		self.eyeTimer.timeout.connect(self.moveEyes)

		self.gazeTimer = QtCore.QTimer()
		self.gazeTimer.setSingleShot(False)
		self.gazeTimer.timeout.connect(self.trackGazeWithTarget)

		self.pointLabels = []
		self.showCalibratedLabels()
		
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.showFullScreen()
		self.centerChildAt(self.eyes)

		
		self.animation = QtCore.QPropertyAnimation(self.target, 'pos');
		self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

		self.pulseAnimation = QtCore.QPropertyAnimation(self.target, 'scale');
		self.pulseAnimation.setStartValue(1.0)
		self.pulseAnimation.setKeyValueAt(0.5, 1.0/3.0)
		self.pulseAnimation.setEndValue(1.0)
		self.pulseAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
		self.pulseAnimation.setLoopCount(-1)
		
		self.gazeTracker.eyesAppeared.connect(self.setEyesGood)
		self.gazeTracker.eyesDisappeared.connect(self.setEyesBad)
		
		self.eyeTimer.start(1000/30)
		self.gazeTimer.start(1000/30)
		self.gazeTracker.startPolling()
		
		self.points = None
		
	def setEyesBad(self):
		self.eyes.ok = False
		
	def setEyesGood(self):
		self.eyes.ok = True
		
	def trackGazeWithTarget(self):
		gaze = self.gazeTracker.getGaze()
		self.centerChildAt(self.target, gaze)
		self.target.show()
		
	def moveEyes(self):
		if self.eyes.ok or True:
			eyePos = self.gazeTracker.getEyePositions()
			x1, x2 = eyePos[0][0], eyePos[1][0]
			y1, y2 = eyePos[0][1], eyePos[1][1]
			if (x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0):
				pass
			else:
				x = (x1 + x2)/2
				y = (y1 + y2)/2
				if x > 0 and y > 0:
					dx = x2 - x1
					dy = y2 - y1
					
					distance = sqrt(pow(dx,2) + pow(dy,2))
					self.eyes.scale = distance * 5
					
					rads = atan2(-dy,dx)
					rads %= 2*pi
					
					self.eyes.angle = -degrees(rads)
					desktopSize = QtGui.QDesktopWidget().screenGeometry()
					self.centerChildAt(self.eyes, [x*desktopSize.width(), y*desktopSize.height()])
		
	def keyPressEvent(self, event):
		super().keyPressEvent(event)
		if event.key() in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
			self.close()
			if self.gazeTracker.isCalibrating():
				self.gazeTracker.cancelCalibration()
		elif event.key() == QtCore.Qt.Key_Space:
			if self.gazeTracker.isCalibrating():
				self.gazeTracker.cancelCalibration()
				
			self.started = True
			self.startCalibration()
			self.eyes.opacity = 0.15
		
	def startCalibration(self, points=None):
		logging.debug("calibration started")
		for l in self.pointLabels:
			l.hide()
		self.pointLabels = []
		
		self.gazeTimer.stop()
		self.pulseAnimation.setDuration(self.pointCaptureDuration / 3)
		self.points = points
		try:
			self.animation.finished.disconnect()
		except:
			pass
		self.animation.setDuration(self.movementTime * 2)
		self.animation.finished.connect(self._startCalibration)
		self.goToPoint([self.width()/2, self.height()/2])
		
	def _startCalibration(self):
		self.animation.finished.disconnect()
		self.animation.finished.connect(self.startPointCaptureSoon)
		self.animation.setDuration(self.movementTime)
		if self.points is None:
			desktopSize = QtGui.QDesktopWidget().screenGeometry()
			self.centerChildAt(self.target)
			self.goToPoint(self.gazeTracker.startCalibration(xResolution, yResolution, desktopSize.width(), desktopSize.height()))
		else:
			logging.debug("redo-ing calibration")
			self.goToPoint(self.gazeTracker.redoCalibration(self.points))
		
	def centerChildAt(self, child, pos=None):
		if pos is None:
			pos = [self.width()/2, self.height()/2]
		child.move(
			pos[0] - child.width()/2,
			pos[1] - child.height()/2
		)

	def resizeEvent(self, event):
		super().resizeEvent(event)
#		self.centerChildAt(self.label)
		
	def goToPoint(self, point):
		self.animation.setStartValue(self.target.pos())
		self.animation.setEndValue(QtCore.QPoint(
			point[0] - self.target.width()/2,
			point[1] - self.target.height()/2
		))
		self.animation.start()
		
	def startPointCaptureSoon(self):
		QtCore.QTimer.singleShot(self.pointCaptureDelay, self.startPointCapture)

	def startPointCapture(self):
		if self.isVisible():
			self.gazeTracker.beginPointCapture()
			self.pulseAnimation.start()

			QtCore.QTimer.singleShot(self.pointCaptureDuration, self.endPointCapture)
		
	def endPointCapture(self):
		self.pulseAnimation.stop()
		if self.isVisible():			
			nextPoint = self.gazeTracker.endPointCapture()
			if nextPoint != None:
				self.goToPoint(nextPoint)
			else:
				calibration = self.gazeTracker.getCalibration()
				badPoints = []
				for point in calibration.points:
					if point.state < 2:
						logging.debug("Bad Coordinates : %s" % point.cp)
						logging.debug("\tstate     : %d" % point.state)
						logging.debug("\taccuracy  : %d" % point.ad)
						logging.debug("\tmean error: %d" % point.mep)
						logging.debug("\tstd dev   : %d" % point.asd)
						
						badPoints.append([point.cp.x, point.cp.y])
					
				if len(badPoints) > 0:
					logging.debug("%d bad points during gaze calibration" % len(badPoints))
					self.pointCaptureDuration = self.pointCaptureDuration * 1.25
					badPoints.reverse()
					self.startCalibration(badPoints)
				else:
					self.gazeTimer.start(1000/60)
					self.showCalibratedLabels(calibration)
					
	def showCalibratedLabels(self, calibration=None):
		self.gazeTimer.start(1000/60)
		if calibration is None:
			calibration = self.gazeTracker.getCalibration()
		
		if not (calibration is None or calibration.points is None):
			for point in calibration.points:
				text = '''
					acc:%d
					err:%d
					dev:%d
				''' % (point.ad, point.mep, point.asd)
				label = QtGui.QLabel('<font size="12">%s</font>' % text.replace('\n', '<br>'), self)
				label.setStyleSheet("background-color: transparent;");
				font = self.font()
				font.setStyleHint(QtGui.QFont.Monospace)
				font.setFamily("Courier New")
				label.setFont(font)
				label.show()
				self.centerChildAt(label, [point.cp.x, point.cp.y])
				
				self.pointLabels.append(label)
				logging.debug("Calibration point : %s" % point.cp)
				logging.debug("\taccuracy  : %d" % point.ad)
				logging.debug("\tmean error: %d" % point.mep)
				logging.debug("\tstd dev   : %d" % point.asd)
	
	def targetScaled(self):
		self.centerChildAt(self.target)
		
	def closeEvent(self, e):
		super().closeEvent(e)
		self.pulseAnimation.stop()
		self.animation.stop()
		self.gazeTimer.stop()
		self.eyeTimer.stop()
		try:
			self.gazeTracker.endPointCapture()
		except:
			pass
		self.closed.emit()
		
class TargetWidget(QtGui.QWidget):
	def __init__(self, parent):
		super().__init__(parent)
		self.resize(64, 64)
		self._scale = 1
		
	def getScale(self):
		return self._scale
	
	def setScale(self, scale):
		self._scale = scale
		self.repaint()
		
	def paintEvent(self, event):
		super().paintEvent(event)
		painter = QtGui.QPainter(self)
		painter.setPen(QtGui.QColor(0, 0, 0))
		painter.setBrush(QtGui.QColor(128, 128, 128))
		painter.setRenderHint(painter.RenderHint.Antialiasing)
		size = self.width() * self.scale
		painter.drawEllipse(
			(self.width() - size)/2+1,
			(self.height() - size)/2+1,
			size-2,
			size-2
		)
		colors = [QtGui.QColor(0, 0, 0), QtGui.QColor(255, 255, 255)]
		for color in colors:
			size = size / 3.5
			painter.setBrush(color)
			painter.drawEllipse(
				(self.width() - size)/2+1,
				(self.height() - size)/2+1,
				size-2,
				size-2
			)
		
	scale = QtCore.Property(float, getScale, setScale)

class EyeballWidget(QtGui.QWidget):
	def __init__(self, parent):
		super().__init__(parent)
		self.resize(720, 720)
		self._opacity = 1.0
		self._scale = 1.0
		self._angle = 0
		self._ok = False
		
		self.eyePixmaps = {
			True: QtGui.QPixmap.fromImage(QtGui.QImage('assets/eyes-good.png')),
			False: QtGui.QPixmap.fromImage(QtGui.QImage('assets/eyes-bad.png'))
		}
		
	def getOpacity(self):
		return self._opacity
		
	def setOpacity(self, opacity):
		self._opacity = opacity
		
	def getScale(self):
		return self._scale
	
	def setScale(self, scale):
		self._scale = scale
		self.repaint()
		
	def getAngle(self):
		return self._angle
	
	def setAngle(self, angle):
		self._angle = angle
		self.repaint()
		
	def getOk(self):
		return self._ok
	
	def setOk(self, ok):
		self._ok = ok
		self.repaint()
		
	def paintEvent(self, event):
		super().paintEvent(event)
		painter = QtGui.QPainter(self)
		painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)
		painter.setOpacity(self._opacity)
		painter.translate(self.width()/2, self.height()/2)
		painter.rotate(self._angle)
		painter.scale(self._scale, self._scale)
		painter.drawPixmap(-90, -90, self.eyePixmaps[self._ok])
		painter.translate(-self.width()/2, -self.height()/2)
		
	opacity = QtCore.Property(float, getOpacity, setOpacity)
	scale = QtCore.Property(float, getScale, setScale)
	angle = QtCore.Property(float, getAngle, setAngle)
	ok = QtCore.Property(bool, getOk, setOk)


if __name__ == '__main__':
	import sys, os, inspect, time, logging
	
	logging.basicConfig(
		format='%(levelname)-8s %(asctime)s %(message)s',
		filename='logs/%d.log' % int(time.time()),
		level=logging.DEBUG,
	)

	src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
	arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
	sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
	sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
	
	app = QtGui.QApplication(sys.argv)

	window = CalibrationWindow()
	window.show()
	app.exec_()
