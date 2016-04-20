import logging

from PySide import QtCore

_settings = None

_gestureDefaults = {
	'scaling': 10.0,
	'grabThreshold': 96.0,
	'releaseThreshold': 94.0,
	'minGrab': 30,
	'maxGrab': 450,
	'dwellDuration': 0.1,
	'dwellRange': 2,
	'attentionPeriod': 1.0,
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
	
def gestureValue(key):
	return settings.value('GestureTracker/%s' % key, _gestureDefaults[key])
	
def gazeValue(key):
	return settings.value('GazeTracker/%s' % key, _gazeDefaults[key])
	
def setGestureValue(key, value):
	_setValue('GestureTracker', key, value)
	
def setGazeValue(key, value):
	_setValue('GazeTracker', key, value)

def _setValue(section, key, value):
	global settings
	
	settings.beginGroup(section)
	settings.setValue(key, value)
	settings.endGroup()
	
