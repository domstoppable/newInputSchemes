from PySide import QtGui, QtCore

import sys, os, inspect
import logging, time

from peyetribe import EyeTribe
from selectionDetector import DwellSelect, Point

STATES = {
	'STATE_TRACKING_GAZE': 0x01,
	'STATE_TRACKING_EYES': 0x02,
	'STATE_TRACKING_PRESENCE': 0x04,
	'STATE_TRACKING_FAIL': 0x08,
	'STATE_TRACKING_LOST': 0x10,
}

class GazeDevice(QtCore.QObject):
	eyesAppeared = QtCore.Signal(object)
	eyesDisappeared = QtCore.Signal()
	fixated = QtCore.Signal(object) # @TODO: make this work
	
	def __init__(self):
		super().__init__()
		
		self.tracker = EyeTribe()
		self.tracker.connect()
		self.tracker.pullmode()

		self.detector = DwellSelect(.33, 75)
		self.gazePosition = [-1, -1]
		self.eyePositions = [[-1, -1], [-1, -1]]
		self.lastFixation = None
		self.sawEyesLastTime = False
		
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self.poll)
		
	def isRunning(self):
		return self.timer.isActive()
		
	def startPolling(self):
		if not self.isRunning():
			self.timer.start(1.0/60.0)
		
	def poll(self):
		try:
			gazeFrame = self.tracker.next()
			if (gazeFrame.state & (STATES['STATE_TRACKING_GAZE'] | STATES['STATE_TRACKING_EYES'] | STATES['STATE_TRACKING_PRESENCE'])  != 0):
				self.gazePosition = [gazeFrame.avg.x, gazeFrame.avg.y]
				if not self.sawEyesLastTime:
					self.eyesAppeared.emit(self.gazePosition)
					
				currentTime = time.time()
				point = Point(
					gazeFrame.avg.x,
					gazeFrame.avg.y,
					0,
					currentTime,
					gazeFrame.avg
				)
				self.eyePositions = [
					[gazeFrame.lefteye.pcenter.x, gazeFrame.lefteye.pcenter.y],
					[gazeFrame.righteye.pcenter.x, gazeFrame.righteye.pcenter.y]
				]
				self.detector.addPoint(point)
				if self.detector.selection != None:
					self.lastFixation = self.detector.clearSelection()
					self.fixated.emit(self.lastFixation)

				self.sawEyesLastTime = True
			else:
				raise(Exception('not tracking'))
		except:
			if self.sawEyesLastTime:
				self.eyesDisappeared.emit()
			self.sawEyesLastTime = False
			
	def getGaze(self):
		return self.gazePosition
		
	def getEyePositions(self):
		return self.eyePositions
		
	def exit(self):
		self.timer.stop()

	def redoCalibration(points):
		self.points = points
		random.shuffle(self.points)
		
		return self.points[-1]
		
	def startCalibration(self, xPoints, yPoints, screenWidth, screenHeight):
		import random
		
		self.points = []
		margin = 32
		for y in range(yPoints):
			for x in range(xPoints):
				self.points.append([
					x * ((screenWidth-margin*2) / (xPoints-1)) + margin,
					y * ((screenHeight-margin*2) / (yPoints-1)) + margin
				])
		random.shuffle(self.points)
		self.tracker.calibration_start(xPoints * yPoints)
		
		return self.points[-1]
	
	def beginPointCapture(self):
		point = self.points.pop()
		print("Starting point", point)
		self.tracker.calibration_point_start(point[0], point[1])

	def endPointCapture(self):
		print("Ending point")
		self.tracker.calibration_point_end()
		if len(self.points) > 0:
			return self.points[-1]
	
	def getCalibration(self):
		return self.tracker.latest_calibration_result()
