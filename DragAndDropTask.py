#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, logging

from PySide import QtGui, QtCore

from DragDropUI import *
from InputScheme import *

from GazeCalibrationWindow import CalibrationWindow

window = None
loadingWindow = None
gazeCalibrationWindow = None
scheme = None
def main(selectedScheme, app=None):
	global window, gazeCalibrationWindow, scheme
	
	scheme = selectedScheme
	
	forceStart = app is None
	if forceStart:
		app = QtGui.QApplication(sys.argv)

	window = DragDropTaskWindow()
	window.closed.connect(closeDown)
	
	def imageMoved(imageName, destination):
		logging.info('Moved %s to %s', imageName, destination)
		
		if window.getRemainingImageCount() < 1:
			QtCore.QTimer.singleShot(500, window.close)
		
	scheme.imageMoved.connect(imageMoved)

	window.optionsWindow = DeviceOptionsWindow()
	if hasattr(scheme, 'gestureTracker'):
		window.optionsWindow.addGestureControls(scheme)
		
	if hasattr(scheme, 'gazeTracker'):
		gazeCalibrationWindow = CalibrationWindow(scheme.gazeTracker)
		gazeCalibrationWindow.closed.connect(showMainWindow)
		gazeCalibrationWindow.show()
		
		window.optionsWindow.dwellDurationChanged.connect(scheme.gazeTracker.setDwellDuration)
		window.optionsWindow.dwellRangeChanged.connect(scheme.gazeTracker.setDwellRange)
		window.optionsWindow.addGazeControls(scheme.gazeTracker)
	else:
		showMainWindow()

	if forceStart:
		app.exec_()
		
	return window


def closeDown():
	if hasattr(scheme, 'gazeTracker'):
		scheme.gazeTracker.stop()
	
def showMainWindow():
	global window, scheme
	scheme.setWindow(window)
	window.showFullScreen()
	window.tileSubWindows()
	scheme.start()

if __name__ == '__main__':
	scheme = getattr(InputScheme, sys.argv[0])()
	sys.exit(main(scheme))
