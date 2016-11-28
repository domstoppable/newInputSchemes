import logging

from PySide import QtCore

_systemSettings = QtCore.QSettings('Green Light Go', 'Alternative input schemes')
_personalSettings = None

_systemDefaults = {
	'participantID': 'test',
	'syncGestureAndGaze': True,
}

_gestureDefaults = {
	'prescale': 5.0,
	'acceleration': 2,
	'grabThreshold': 96.0,
	'releaseThreshold': 94.0,
	'dwellDuration': 0.35,
	'dwellRange': 2.2,
	'attentionPeriod': .2,
	'minGrab': 30,
	'maxGrab': 450,
}

_gazeDefaults = {
	'dwellDuration': 0.35,
	'dwellRange': 75,
	'attentionPeriod': .75,
}

def loadPersonalSettings(userID):
	global _personalSettings
	_personalSettings = QtCore.QSettings('logs/%s/preferences.ini' % userID, QtCore.QSettings.IniFormat)
	logging.debug('Loaded settings')
	
def systemValue(key):
	return _systemSettings.value('System/%s' % key, _systemDefaults[key])
	
def setSystemValue(key, value):
	_systemSettings.setValue('System/%s' % key, value)
	
def gestureValue(key):
	return _personalSettings.value('GestureTracker/%s' % key, _gestureDefaults[key])
	
def gazeValue(key):
	return _personalSettings.value('GazeTracker/%s' % key, _gazeDefaults[key])
	
def setGestureValue(key, value):
	_setValue('GestureTracker', key, value)
	
def setGazeValue(key, value):
	_setValue('GazeTracker', key, value)

def _setValue(section, key, value):
	_personalSettings.beginGroup(section)
	_personalSettings.setValue(key, value)
	_personalSettings.endGroup()
	
def checkBool(value):
	return value in [ True, 'True', 'true', 't', 1, '1' ]
