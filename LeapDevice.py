import sys, os, inspect

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

from PySide import QtGui, QtCore

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class LeapDevice(QtCore.QObject):
	handAppeared = QtCore.Signal(object)
	handDisappeared = QtCore.Signal(object)
	grabbed = QtCore.Signal(object)
	released = QtCore.Signal(object)	
	moved = QtCore.Signal(object)
	
	def __init__(self):
		super().__init__()
		self.controller = controller
		self.listener = listener

		self.controller.add_listener(self.listener)
		self.listener.signaler = self
		
	def exit(self):
		self.controller.remove_listener(self.listener)
		
class HandyHand():
	def __init__(self):
		self.hand = None
		self.grabbing = False
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
		
class Connector(Leap.Listener):
	def __init__(self):
		super().__init__()
		self.grabThreshold = 0.75
		self.releaseThreshold = 0.70
	
		self.signaler = None
		
		self.leftHand = HandyHand()
		self.rightHand = HandyHand()
		
	def on_connect(self, controller):
		print("Gesture tracker connected!")
		
	def on_frame(self, controller):
		frame = controller.frame()
		hands = frame.hands
		numHands = len(hands)

		for hand in hands:
			if hand.is_left:
				if not self.leftHand.isHand(hand):
					self.signaler.handAppeared.emit(hand)

				self.leftHand.setHand(hand)
				metaHand = self.leftHand
			else:
				if not self.rightHand.isHand(hand):
					self.signaler.handAppeared.emit(hand)
				
				self.rightHand.setHand(hand)
				metaHand = self.rightHand

			if not metaHand.grabbing:
				if hand.pinch_strength >= self.grabThreshold:
					metaHand.grabbing = True
					self.signaler.grabbed.emit(hand)
			else:
				if hand.pinch_strength <= self.releaseThreshold:
					metaHand.grabbing = False
					self.signaler.released.emit(hand)
					
			delta = metaHand.updatePosition()
			if delta[0] != 0 or delta[1] != 0 or delta[2] != 0:
				self.signaler.moved.emit(delta)

controller = Leap.Controller()
controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES);
listener = Connector()
