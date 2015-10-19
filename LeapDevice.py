import sys, os, inspect

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

from PySide import QtGui, QtCore

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class LeapDevice(QtCore.QObject):
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
		
class Connector(Leap.Listener):
	def __init__(self):
		super().__init__()
		self.grabThreshold = 0.75
		self.releaseThreshold = 0.70
	
		self.currentlyGrabbing = False
		
		self.grabHand = None
		self.grabHandStart = None
		
		self.signaler = None
		
		self.usePalm = True
	
	def on_connect(self, controller):
		print("Gesture tracker connected!")

	def on_frame(self, controller):
		frame = controller.frame()
		hands = frame.hands
		numHands = len(hands)

		if numHands >= 1:
			for hand in hands:
				if not self.currentlyGrabbing:
					if hand.pinch_strength >= self.grabThreshold:
						self.currentlyGrabbing = True
						self.grabHand = hand
						
						if self.usePalm:
							self.grabHandStart = hand.stabilized_palm_position
						else:
							thumb = hand.fingers.finger_type(Leap.Finger.TYPE_INDEX)[0]
							self.grabHandStart = thumb.stabilized_tip_position

						if self.signaler != None:
							self.signaler.grabbed.emit(hand)
				else:
					if hand.pinch_strength <= self.releaseThreshold:
						self.currentlyGrabbing = False
						self.grabHand = None

						if self.signaler != None:
							self.signaler.released.emit(hand)
					elif hand.id == self.grabHand.id:
						thumb = hand.fingers.finger_type(Leap.Finger.TYPE_INDEX)[0]
						
						if self.usePalm:
							pos = hand.stabilized_palm_position
						else:
							pos = thumb.stabilized_tip_position

						delta = [
							int(10 * (pos.x - self.grabHandStart.x)),
							int(10 * (pos.y - self.grabHandStart.y)),
							int(10 * (pos.z - self.grabHandStart.z))
						]
						
						if self.signaler != None:
							self.signaler.moved.emit(delta)


controller = Leap.Controller()
controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES);
listener = Connector()
