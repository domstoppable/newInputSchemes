from math import atan2, degrees, pi, sqrt, pow
import logging

from PySide import QtGui, QtCore

instructions = '''
	Please sit comfortably.
	A target will appear on the screen.
	Follow the target with your eyes.
	
	Press any key to begin gaze calibration
'''.replace('\n', '<br>')

class CalibrationWindow(QtGui.QWidget):
	def __init__(self, device=None):
		super().__init__()
		if device is None:
			pass
			from GazeDevice import GazeDevice
			self.gazeTracker = GazeDevice()
		else:
			self.gazeTracker = device
			
		self.setStyleSheet("background-color: #888;");
			
		self.movementTime = 1000 / 2
		self.pointCaptureDelay = 500 / 2
		self.pointCaptureDuration = 2000 / 2

		self.started = False
		self.eyes = EyeballWidget(self)
		self.label = QtGui.QLabel('<font size="50">%s</font>' % instructions, self)
		self.label.setStyleSheet("background-color: transparent;");
		self.target = TargetWidget(parent=self)
		self.target.hide()

		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.pulsate()
		self.showFullScreen()
		self.centerChildAt(self.eyes)
		
		self.gazeTracker.eyesAppeared.connect(self.setEyesGood)
		self.gazeTracker.eyesDisappeared.connect(self.setEyesBad)
		
		self.eyeTimer = QtCore.QTimer()
		self.eyeTimer.setSingleShot(False)
		self.eyeTimer.timeout.connect(self.moveEyes)
		self.eyeTimer.start(1.0/60)
		self.gazeTracker.startPolling()
		
	def setEyesBad(self):
		self.eyes.ok = False
		
	def setEyesGood(self):
		self.eyes.ok = True
		
	def trackGaze(self):
		self.gazeTimer = QtCore.QTimer()
		self.gazeTimer.setSingleShot(False)
		self.gazeTimer.timeout.connect(self.trackGazeWithTarget)
		self.gazeTimer.start(1.0/60)
		
	def trackGazeWithTarget(self):
		gaze = self.gazeTracker.getGaze()
		self.centerChildAt(self.target, gaze)
		
	def moveEyes(self):
		if self.eyes.ok:
			gaze = self.gazeTracker.getEyePositions()
			x1, x2 = gaze[0][0], gaze[1][0]
			y1, y2 = gaze[0][1], gaze[1][1]
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
		if not self.started:
			self.started = True
			self.startCalibration()
			self.eyes.opacity = 0.15
		
	def startCalibration(self, points=None):
		self.label.hide()

		desktopSize = QtGui.QDesktopWidget().screenGeometry()
		self.centerChildAt(self.target)
		self.target.show()
		if points is None:
			self.goToPoint(self.gazeTracker.startCalibration(4, 4, desktopSize.width(), desktopSize.height()))
		else:
			self.goToPoint(self.gazeTracker.redoCalibration(points))
		
	def pulsate(self):
		animation = QtCore.QPropertyAnimation(self.target, 'scale');
		animation.setDuration(1000)
		animation.setStartValue(1.0)
		animation.setKeyValueAt(0.5, 0.5)
		animation.setEndValue(1.0)
		animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
		animation.setLoopCount(-1)
		self.pulseAnimation = animation
		
	def centerChildAt(self, child, pos=None):
		if pos is None:
			pos = [self.width()/2, self.height()/2]
		child.move(
			pos[0] - child.width()/2,
			pos[1] - child.height()/2
		)

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.centerChildAt(self.label)
		
	def goToPoint(self, point):
		animation = QtCore.QPropertyAnimation(self.target, 'pos');
		animation.setDuration(self.movementTime)
		animation.setStartValue(self.target.pos())
		animation.setEndValue(QtCore.QPoint(
			point[0] - self.target.width()/2,
			point[1] - self.target.height()/2
		))
		animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
		animation.finished.connect(self.startPointCaptureSoon)
		animation.start()
		
		# maintain a handle on the animation to prevent GC
		self.animation = animation
		
	def startPointCaptureSoon(self):
		QtCore.QTimer.singleShot(self.pointCaptureDelay, self.startPointCapture)

	def startPointCapture(self):
		self.gazeTracker.beginPointCapture()
		self.pulseAnimation.start()

		QtCore.QTimer.singleShot(self.pointCaptureDuration, self.endPointCapture)
		
	def endPointCapture(self):
		self.pulseAnimation.stop()
		nextPoint = self.gazeTracker.endPointCapture()
		if nextPoint != None:
			self.goToPoint(nextPoint)
		else:
			calibration = self.gazeTracker.getCalibration()
			badPoints = []
			for point in calibration.points:
				if point.state < 2 or point.asd > 50:
					badPoints.append([point.cp.x, point.cp.y])
					logging.debug("Bad Coordinates : %s" % point.cp)
					logging.debug("\taccuracy  : %d" % point.ad)
					logging.debug("\tmean error: %d" % point.mep)
					logging.debug("\tstd dev   : %d" % point.asd)
				
			if len(badPoints) > 0:
				logging.debug("%d bad points during gaze calibration" % len(badPoints))
				self.pointCaptureDuration = self.pointCaptureDuration * 1.5
				self.pulseAnimation.setDuration(self.pointCaptureDuration / 3)
				self.startCalibration(badPoints)
			else:
				self.pulseAnimation.start()
				self.trackGaze()
				
				for point in calibration.points:
					text = '''
						accuracy  : %d
						mean error: %d
						std dev   : %d
					''' % (point.ad, point.mep, point.asd)
					label = QtGui.QLabel('<font size="14">%s</font>' % text.replace('\n', '<br>'), self)
					label.setAlignment(QtCore.Qt.AlignCenter)
					label.setStyleSheet("background-color: transparent;");
					label.show()
					self.centerChildAt(label, [point.cp.x, point.cp.y])
					logging.debug("Calibration point : %s" % point.cp)
					logging.debug("\taccuracy  : %d" % point.ad)
					logging.debug("\tmean error: %d" % point.mep)
					logging.debug("\tstd dev   : %d" % point.asd)
	
	def targetScaled(self):
		self.centerChildAt(self.target)
		
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
		painter.setBrush(QtGui.QColor(255, 255, 255))
		size = self.width() * self.scale
		painter.drawEllipse(
			(self.width() - size)/2+1,
			(self.height() - size)/2+1,
			size-2,
			size-2
		)
		colors = [QtGui.QColor(0, 0, 0),QtGui.QColor(255, 255, 255)]
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
