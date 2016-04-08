import logging
import time, random
import threading, subprocess, signal

from PySide import QtGui, QtCore

from peyetribe import EyeTribe
from selectionDetector import DwellSelect, Point

STATES = {
	'STATE_TRACKING_GAZE': 0x01,
	'STATE_TRACKING_EYES': 0x02,
	'STATE_TRACKING_PRESENCE': 0x04,
	'STATE_TRACKING_FAIL': 0x08,
	'STATE_TRACKING_LOST': 0x10,
}

_instance = None
def getGazeDevice():
	global _instance
	if _instance is None:
		_instance = _GazeDevice()
		
	return _instance
	
class EyeTribeServer(QtCore.QObject):
	outputGenerated = QtCore.Signal(object)
	ready = QtCore.Signal()
	error = QtCore.Signal(object)
	
	def __init__(self):
		super().__init__()
		self.thread = threading.Thread(target=self._go)
		self._ready = False
		self._running = False
		
	def __del__(self):
		self.stop()
		
	def start(self):
		if not self._running:
			self.thread.start()
	
	def stop(self):
		self.process.kill()
		
	def isReady(self):
		return self._ready
		
	def isRunning(self):
		return self._running
		
	def _go(self):
		goodText = 'The Eye Tribe Tracker stands ready!'
		runningText = 'The Eye Tribe Tracker is already running!'
		
		exe = 'C:\\Program Files (x86)\\EyeTribe\\Server\\EyeTribe.exe'
		self.process = subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
		self._running = True
		while not self.process.poll():
			line = self.process.stdout.readline().decode("utf-8")
			if line != '':
				logging.debug("Eyetribe server: %s" % line)
				self.outputGenerated.emit(line)
				if goodText in line:
					self._ready = True
					self.ready.emit()
					
		for line in self.process.stderr.readlines():
			self.error.emit(line)
			if not self._ready and  l in runningText:
				self._ready = True
				self.ready.emit()

class _GazeDevice(QtCore.QObject):
	ready = QtCore.Signal()
	eyesAppeared = QtCore.Signal(object)
	eyesDisappeared = QtCore.Signal()
	fixated = QtCore.Signal(object) # @TODO: make this work
	
	def __init__(self):
		super().__init__()

		self.detector = DwellSelect(.33, 75)
		self.gazePosition = [-99, -99]
		self.eyePositions = [[-99, -99], [-99, -99]]
		self.lastFixation = None
		self.sawEyesLastTime = None
		
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self._poll)
		
		self.pointStarted = False
		
		self.tracker = EyeTribe()
		self.server = EyeTribeServer()
		self.server.ready.connect(self.connectToServer)
#		self.tracker.pullmode()
		self.server.start()
		self.isReady = self.server.isReady


	def connectToServer(self):
		logging.debug("Eyetribe server ready - connecting tracker!")
		self.tracker.connect()
		self.ready.emit()
		
	def getDwellDuration(self):
		return self.detector.minimumDelay
		
	def getDwellRange(self):
		return self.detector.range
		
	def setDwellDuration(self, duration):
		self.detector.setDuration(duration)
		
	def setDwellRange(self, rangeInPixels):
		self.detector.setRange(rangeInPixels)
		
	def isRunning(self):
		return self.timer.isActive()
		
	def startPolling(self):
		if self.server.isReady():
			self._startPolling()
		else:
			self.server.ready.connect(self._startPolling)
			self.server.start()

	def _startPolling(self):
		if not self.isRunning():
			self.timer.start(1000/30)
		
	def _poll(self):
		try:
			gazeFrame = self.tracker.next()
			if (gazeFrame.state & STATES['STATE_TRACKING_GAZE']) != 0:
				self.eyePositions = [
					[gazeFrame.lefteye.pcenter.x, gazeFrame.lefteye.pcenter.y],
					[gazeFrame.righteye.pcenter.x, gazeFrame.righteye.pcenter.y]
				]

				if gazeFrame.raw.x == 0 and gazeFrame.raw.y == 0:
					logging.debug('stuck : %s' % gazeFrame)
					logging.debug('stuck : %s' % gazeFrame.state)
					#raise(Exception('frame stuck'))
				else:
					logging.debug('good  : %s' % gazeFrame)
					logging.debug('good  : %s' % gazeFrame.state)
				if True:
					self.gazePosition = [gazeFrame.avg.x, gazeFrame.avg.y]
					if not self.sawEyesLastTime or self.sawEyesLastTime is None:
						self.eyesAppeared.emit(self.gazePosition)
					self.sawEyesLastTime = True
						
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
						self.lastFixation = self.detector.clearSelection()
						self.fixated.emit(self.lastFixation)
			else:
				raise(Exception('not tracking: %d' % gazeFrame.state))
		except Exception as exc:
			if self.sawEyesLastTime:
				self.eyesDisappeared.emit()
			self.sawEyesLastTime = False
			
	def getGaze(self):
		return self.gazePosition
		
	def getEyePositions(self):
		return self.eyePositions
		
	def exit(self):
		self.timer.stop()

	def redoCalibration(self, points):
		self.points = points
		return self.points[-1]
		
	def cancelCalibration(self):
		if self.tracker.is_calibrating():
			logging.debug("sending abort")
			self.tracker.calibration_abort()
			
	def isCalibrating(self):
		return self.tracker.is_calibrating()
		
	def startCalibration(self, xPoints, yPoints, screenWidth, screenHeight):
		self.points = []
		margin = 100
		for y in range(yPoints):
			for x in range(xPoints):
				self.points.append([
					x * ((screenWidth-margin*2) / (xPoints-1)) + margin,
					y * ((screenHeight-margin*2) / (yPoints-1)) + margin
				])
		random.shuffle(self.points)
		self.tracker.calibration_clear()
		self.tracker.calibration_start(xPoints * yPoints)
		
		return self.points[-1]
	
	def beginPointCapture(self):
		point = self.points.pop()
		try:
			self.tracker.calibration_point_start(point[0], point[1])
			self.pointStarted = True
		except Exception as exc:
			logging.error(exc)

	def endPointCapture(self):
		if self.pointStarted:
			self.tracker.calibration_point_end()
		
		self.pointStarted = False
		if len(self.points) > 0:
			return self.points[-1]
	
	def getCalibration(self):
		return self.tracker.latest_calibration_result()
		
	def stop(self):
		self.timer.stop()
		self.tracker.close()
		time.sleep(8)
		self.server.stop()
