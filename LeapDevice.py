import sys, os, inspect
import logging

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

import LeapPython

from PySide import QtGui, QtCore

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class LeapDevice(QtCore.QObject):
	handAppeared = QtCore.Signal(object)
	handDisappeared = QtCore.Signal(object)
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
		self.minGrab = 0
		self.maxGrab = 200
		
		self.grabThreshold = 0.85
		self.releaseThreshold = 0.70
	
		self.pinchThreshold = 0.85
		self.unpinchThreshold = 0.70
	
		self.leftHand = HandyHand()
		self.rightHand = HandyHand()
		
		self.listening = True
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self.poll)
		self.timer.start(1.0/30.0)
    
	def poll(self):
		frame = self.controller.frame()
		hands = frame.hands
		numHands = len(hands)
		
		if len(hands) == 0:
			self.noHands.emit()

		for hand in hands:
			if hand.is_left:
				if not self.leftHand.isHand(hand):
					self.handAppeared.emit(hand)

				self.leftHand.setHand(hand)
				metaHand = self.leftHand
			else:
				if not self.rightHand.isHand(hand):
					self.handAppeared.emit(hand)
				
				self.rightHand.setHand(hand)
				metaHand = self.rightHand

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
				self.maxGrab = 250
	
	def exit(self):
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
		
