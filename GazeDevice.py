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
		self.lastFixation = None
		self.sawEyesLastTime = False
		
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self.poll)
		self.timer.start(1.0/30.0)
		
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
		
	def exit(self):
		self.timer.stop()
