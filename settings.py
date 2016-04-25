import logging

from PySide import QtCore

_settings = None

_systemDefaults = {
	'syncGestureAndGaze': True,
}

_gestureDefaults = {
	'prescale': 3.0,
	'acceleration': 1.45,
	'grabThreshold': 96.0,
	'releaseThreshold': 94.0,
	'dwellDuration': 0.5,
	'dwellRange': 2,
	'attentionPeriod': .7,
	'minGrab': 30,
	'maxGrab': 450,
}

_gazeDefaults = {
	'dwellDuration': 0.5,
	'dwellRange': 75,
	'attentionPeriod': 1,
}

def load(userID):
	global settings
	settings = QtCore.QSettings('logs/%s/preferences.ini' % userID, QtCore.QSettings.IniFormat)
	logging.debug('Loaded settings')
	
def systemValue(key):
	return settings.value('System/%s' % key, _systemDefaults[key])
	
def gestureValue(key):
	return settings.value('GestureTracker/%s' % key, _gestureDefaults[key])
	
def gazeValue(key):
	return settings.value('GazeTracker/%s' % key, _gazeDefaults[key])
	
def setSystemValue(key, value):
	_setValue('System', key, value)
	
def setGestureValue(key, value):
	_setValue('GestureTracker', key, value)
	
def setGazeValue(key, value):
	_setValue('GazeTracker', key, value)

def _setValue(section, key, value):
	settings.beginGroup(section)
	settings.setValue(key, value)
	settings.endGroup()
	
def checkBool(value):
	return value in [ True, 'True', 'true', 't', 1, '1' ]
