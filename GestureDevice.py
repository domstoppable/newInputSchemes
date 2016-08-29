import logging, settings, time, math
from PySide import QtGui, QtCore

import LeapPython
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

from selectionDetector import DwellSelect, Point

class GestureDevice(QtCore.QObject):
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
	fixated = QtCore.Signal(object)
	fixationInvalidated = QtCore.Signal(object)
	reachingBounds = QtCore.Signal(object, object)
	
	def __init__(self):
		super().__init__()
		self.controller = Leap.Controller()
		self.controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES);
		
		self.calibrating = False
		
		self.prescale = float(settings.gestureValue('prescale'))
		self.acceleration = float(settings.gestureValue('acceleration'))
		self.minGrab = float(settings.gestureValue('minGrab'))
		self.maxGrab = float(settings.gestureValue('maxGrab'))
		
		self.grabThreshold = float(settings.gestureValue('grabThreshold'))
		self.releaseThreshold = float(settings.gestureValue('releaseThreshold'))
		
		self.pinchThreshold = 0.85
		self.unpinchThreshold = 0.70
	
		self.leftHand = HandyHand()
		self.rightHand = HandyHand()
		
		self.leftHand.fixated.connect(self.fixated.emit)
		self.leftHand.fixationInvalidated.connect(self.fixationInvalidated.emit)
		self.rightHand.fixated.connect(self.fixated.emit)
		self.rightHand.fixationInvalidated.connect(self.fixationInvalidated.emit)
		
		self.listening = True
		self.timer = QtCore.QTimer()
		self.timer.setSingleShot(False)
		self.timer.timeout.connect(self.poll)
		self.timer.start(1.0/30.0)
		
		self.sawHandLastTime = False
		
		self.boundsReached = {
			'left': False,
			'right': False,
			'top': False,
			'bottom': False,
		}
    
	def poll(self):
		frame = self.controller.frame()
		hands = frame.hands
		numHands = len(hands)
		
		if len(hands) == 0:
			if self.sawHandLastTime:
				self.noHands.emit()
			self.sawHandLastTime = False
		else:
			metaHand = None
			boundsCheck = {
				'left': False,
				'right': False,
				'top': False,
				'bottom': False,
			}
			for hand in hands:
				# check for edges
				box = frame.interaction_box
				pos = box.normalize_point(hand.palm_position, False)
				ignoreThreshold = 1.2
				warnThreshold = 1.0
				if pos.x > warnThreshold:
					boundsCheck['right'] = True
				elif pos.x < 1-warnThreshold:
					boundsCheck['left'] = True
				if pos.z > warnThreshold:
					boundsCheck['bottom'] = True
				elif pos.z < 1-warnThreshold:
					boundsCheck['top'] = True
				
				okToEmit = True
				if pos.x > ignoreThreshold or pos.x < 1-ignoreThreshold:
					okToEmit = False
				if pos.z > ignoreThreshold or pos.z < 1-ignoreThreshold:
					okToEmit = False

				if hand.is_left:
					if not okToEmit:
						self.handDisappeared.emit(hand)
						self.leftHand.setHand(None)
					else:
						if not self.leftHand.isHand(hand) and not self.sawHandLastTime:
							self.handAppeared.emit(hand)

						self.leftHand.setHand(hand)
						metaHand = self.leftHand
						self.sawHandLastTime = True
				else:
					if not okToEmit:
						self.handDisappeared.emit(hand)
						self.rightHand.setHand(None)
					else:
						if not self.rightHand.isHand(hand) and not self.sawHandLastTime:
							self.handAppeared.emit(hand)
						
						self.rightHand.setHand(hand)
						metaHand = self.rightHand
						self.sawHandLastTime = True
						
				if metaHand is not None:
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
							if grabStrength >= self.grabThreshold / 100.0:
								metaHand.grabbing = True
								self.grabbed.emit(hand)
						else:
							if grabStrength <= self.releaseThreshold / 100.0:
								metaHand.grabbing = False
								self.released.emit(hand)
								
						if not metaHand.pinching:
							if hand.pinch_strength >= self.pinchThreshold / 100.0:
								metaHand.pinching = True
								self.pinched.emit(hand)
						else:
							if hand.pinch_strength <= self.unpinchThreshold / 100.0:
								metaHand.pinching = False
								self.unpinched.emit(hand)
								
						delta = metaHand.updatePosition()
						if delta[0]!=0 or delta[1]!=0 or delta[2]!=0: #if any of these are nonzero
							for index, param in enumerate(delta):
								# absolute value first, otherwise you may end up withi a complex number
								delta[index] = abs(pow(abs(param) * self.prescale, self.acceleration))
								if param < 0:
									delta[index] *= -1

							self.moved.emit(delta)
					
			for direction,warn in boundsCheck.items():
				if warn != self.boundsReached[direction]:
					self.boundsReached[direction] = warn
					self.reachingBounds.emit(direction, warn)
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
		settings.setGestureValue('grabThreshold', threshold)

	def getGrabThreshold(self):
		return self.grabThreshold
		
	def setReleaseThreshold(self, threshold):
		self.releaseThreshold = threshold
		settings.setGestureValue('releaseThreshold', threshold)
		
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
		
	def setPrescale(self, prescale):
		self.prescale = prescale
		settings.setGestureValue('prescale', prescale)
		
	def getPrescale(self):
		return self.prescale
		
	def setAcceleration(self, acceleration):
		self.acceleration = acceleration
		settings.setGestureValue('acceleration', acceleration)
		
	def getAcceleration(self):
		return self.acceleration
		
	def getDwellDuration(self):
		return self.leftHand.getDwellDuration()
		
	def getDwellRange(self):
		return self.leftHand.getDwellRange()
		
	def setDwellDuration(self, duration):
		self.leftHand.setDwellDuration(duration)
		self.rightHand.setDwellDuration(duration)
		settings.setGestureValue('dwellDuration', duration)
		
	def setDwellRange(self, rangeInPixels):
		self.leftHand.setDwellRange(rangeInPixels)
		self.rightHand.setDwellRange(rangeInPixels)
		settings.setGestureValue('dwellRange', rangeInPixels)
		
	def setAttentionStalePeriod(self, duration):
		self.leftHand.setAttentionStalePeriod(duration)
		self.rightHand.setAttentionStalePeriod(duration)
		settings.setGestureValue('attentionPeriod', duration)
		
	def getAttentionStalePeriod(self):
		return self.leftHand.getAttentionStalePeriod()
		
	def getLastFixation(self):
		left = self.leftHand.getLastFixation()
		right = self.rightHand.getLastFixation()
		if left is None and right is None:
			return None
		elif left is None:
			return right
		elif right is None:
			return left
		elif left.time < right.time:
			return right
		else:
			return left
			
	def clearLastFixation(self):
		self.leftHand.clearLastFixation()
		self.rightHand.clearLastFixation()
		self.fixationInvalidated.emit(None)

	def getAttentivePosition(self, clear=False):
		left = self.leftHand.getAttentivePosition(clear)
		right = self.rightHand.getAttentivePosition(clear)
		
		return whichIsLater(left, right)

	def stop(self):
		self.timer.stop()

class HandyHand(QtCore.QObject):
	fixated = QtCore.Signal(object)
	fixationInvalidated = QtCore.Signal(object)

	def __init__(self):
		super().__init__()
		self.hand = None
		self.grabbing = False
		self.pinching = False
		self.rawPositionHistory = [[], [], []]
		self.smoothRange = 4
		self.position = [-1, -1, -1]
		self.lastFixation = None
		self.staleTimerStart = None
		self.attentionStalePeriod = float(settings.gestureValue('attentionPeriod'))
		
		self.detector = DwellSelect(
			float(settings.gestureValue('dwellDuration')),
			float(settings.gestureValue('dwellRange'))
		)
		
	def setHand(self, hand):
		if self.hand is None or hand is None or self.hand.id != hand.id:
			self.hand = hand
			for i in range(3):
				self.rawPositionHistory[i] = []
				
			self.updatePosition()
		else:
			self.hand = hand
		
	def updatePosition(self):
		if self.hand is None:
			return
			
		self.rawPositionHistory[0].insert(0, self.hand.palm_position.x)
		self.rawPositionHistory[1].insert(0, self.hand.palm_position.y)
		self.rawPositionHistory[2].insert(0, self.hand.palm_position.z)
		newPos = []
		delta = []
		for i,history in enumerate(self.rawPositionHistory):
			self.rawPositionHistory[i] = history[0:self.smoothRange]
			newPos.append(sum(self.rawPositionHistory[i]) / len(self.rawPositionHistory[i]))
			delta.append(newPos[i] - self.position[i])
			self.position[i] = newPos[i]
		
		wasInsideDwell = self.detector.inDwell
		self.detector.addPoint(Point(
			newPos[0],
			newPos[1],
			newPos[2],
			time.time(),
			self.hand
		))
		if self.detector.selection != None:
			self.lastFixation = self.detector.clearSelection()
			self.fixated.emit(self.lastFixation)
			wasInsideDwell = False
			self.staleTimerStart = None
		
		if wasInsideDwell and not self.detector.inDwell:
			self.staleTimerStart = time.time()
		elif self.staleTimerStart is not None and (time.time() - self.staleTimerStart) > self.attentionStalePeriod:
			self.staleTimerStart = None
			self.fixationInvalidated.emit(self.lastFixation)

		return delta
		
	def isHand(self, hand):
		if self.hand is None and hand is not None: return False
		if self.hand == hand: return True
		if self.hand is None or hand is None: return False
		return self.hand.id == hand.id
		
	def getDwellDuration(self):
		return self.detector.minimumDelay
		
	def getDwellRange(self):
		return self.detector.range
		
	def setDwellDuration(self, duration):
		self.detector.setDuration(duration)
		
	def setDwellRange(self, rangeInPixels):
		self.detector.setRange(rangeInPixels)

	def getLastFixation(self):
		return self.lastFixation
		
	def clearLastFixation(self):
		self.staleTimer = None
		self.lastFixation = None
		
	def setAttentionStalePeriod(self, duration):
		self.attentionStalePeriod = duration
		
	def getAttentionStalePeriod(self):
		return self.attentionStalePeriod
		
	def getAttentivePosition(self, clear=False):
		position = self.position
		if self.lastFixation is not None:
			if self.staleTimerStart is None or (time.time() - self.staleTimerStart) < self.attentionStalePeriod:
				position = [self.lastFixation.x, self.lastFixation.y, self.lastFixation.z]
			
		if clear:
			self.lastFixation = None
			self.staleTimerStart = None
			
		return position

def whichIsLater(left, right):
	if left is None and right is None:
		return None
	elif left is None:
		return right
	elif right is None:
		return left
	elif left.time < right.time:
		return right
	else:
		return left
