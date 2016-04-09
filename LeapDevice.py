import logging

import LeapPython

from PySide import QtGui, QtCore

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class LeapDevice(QtCore.QObject):
	handAppeared = QtCore.Signal(object)
	handDisappeared = QtCore.Signal(object)	# @TODO make this work
	noHands = QtCore.Signal()
	grabbed = QtCore.Signal(object)
	pinched = QtCore.Signal(object)
	unpinched = QtCore.Signal(object)
	released = QtCore.Signal(object)	
	moved = QtCore.Signal(object)
	grabValued = QtCore.Signal(object)
	pinchValued = QtCore.Signal(object)
	
	def __init__(self):
		super().__init__()
		self.controller = Leap.Controller()
		self.controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES);
		
		self.calibrating = False
		
		self.scaling = 1.0
		
		self.minGrab = 30
		self.maxGrab = 450
		
		self.grabThreshold = 0.96
		self.releaseThreshold = 0.94
	
		self.pinchThreshold = 0.85
		self.unpinchThreshold = 0.70
	
		self.leftHand = HandyHand()
		self.rightHand = HandyHand()
		
		self.listening = True
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self.poll)
		self.timer.start(1.0/30.0)
		
		self.sawHandLastTime = False
    
	def poll(self):
		frame = self.controller.frame()
		hands = frame.hands
		numHands = len(hands)
		
		if len(hands) == 0:
			if self.sawHandLastTime:
				self.noHands.emit()
			self.sawHandLastTime = False
		else:
			for hand in hands:
				if hand.is_left:
					if not self.leftHand.isHand(hand) and not self.sawHandLastTime:
						self.handAppeared.emit(hand)

					self.leftHand.setHand(hand)
					metaHand = self.leftHand
				else:
					if not self.rightHand.isHand(hand) and not self.sawHandLastTime:
						self.handAppeared.emit(hand)
					
					self.rightHand.setHand(hand)
					metaHand = self.rightHand
				self.sawHandLastTime = True

				if self.calibrating:
					if self.minGrab is None or hand.sphere_radius < self.minGrab:
						self.minGrab = hand.sphere_radius
					if self.maxGrab is None or hand.sphere_radius > self.maxGrab:
						self.maxGrab = hand.sphere_radius					
				else:
					grabStrength = (self.maxGrab - hand.sphere_radius) / (self.maxGrab - self.minGrab)
					self.grabValued.emit(grabStrength)
					self.pinchValued.emit(hand.pinch_strength)
					if not metaHand.grabbing:
						if grabStrength >= self.grabThreshold:
							metaHand.grabbing = True
							self.grabbed.emit(hand)
					else:
						if grabStrength <= self.releaseThreshold:
							metaHand.grabbing = False
							self.released.emit(hand)
							
					if not metaHand.pinching:
						if hand.pinch_strength >= self.pinchThreshold:
							metaHand.pinching = True
							self.pinched.emit(hand)
					else:
						if hand.pinch_strength <= self.unpinchThreshold:
							metaHand.pinching = False
							self.unpinched.emit(hand)
							
					delta = metaHand.updatePosition()
					if delta[0] != 0 or delta[1] != 0 or delta[2] != 0:
						delta = [p * self.scaling for p in delta]
						self.moved.emit(delta)
					
	def toggleCalibration(self):
		self.setCalibrating(not self.calibrating)
		
	def setCalibrating(self, calibrationEnabled):
		self.calibrating = calibrationEnabled
		if self.calibrating:
			self.minGrab = None
			self.maxGrab = None
		else:
			if self.minGrab is None:
				self.minGrab = 0
			if self.maxGrab is None:
				self.maxGrab = 400
			logging.info("Calibrated to: %d - %d" % (self.minGrab, self.maxGrab))
	
	def setGrabThreshold(self, threshold):
		self.grabThreshold = threshold

	def getGrabThreshold(self):
		return self.grabThreshold
		
	def setReleaseThreshold(self, threshold):
		self.releaseThreshold = threshold

	def getReleaseThreshold(self):
		return self.releaseThreshold
		
	def setPinchThreshold(self, threshold):
		self.pinchThreshold = threshold

	def getPinchThreshold(self):
		return self.pinchThreshold
		
	def setUnpinchThreshold(self, threshold):
		self.unpinchThreshold = threshold

	def getUnpinchThreshold(self):
		return self.unpinchThreshold
		
	def setScaling(self, scaling):
		self.scaling = scaling

	def getScaling(self):
		return self.scaling
		
	def stop(self):
		self.timer.stop()

class HandyHand():
	def __init__(self):
		self.hand = None
		self.grabbing = False
		self.pinching = False
		self.position = [-1, -1, -1]
		
	def setHand(self, hand):
		if self.hand is None or self.hand.id != hand.id:
			self.hand = hand
			self.updatePosition()
		else:
			self.hand = hand
		
	def updatePosition(self):
		newPos = self.hand.stabilized_palm_position
		delta = [
			newPos.x - self.position[0],
			newPos.y - self.position[1],
			newPos.z - self.position[2],
		]
		
		self.position = [
			self.hand.stabilized_palm_position.x,
			self.hand.stabilized_palm_position.y,
			self.hand.stabilized_palm_position.z,
		]
	
		return delta
		
	def isHand(self, hand):
		if self.hand is None and hand is not None: return False
		if self.hand == hand: return True
		if self.hand is None or hand is None: return False
		return self.hand.id == hand.id
		
