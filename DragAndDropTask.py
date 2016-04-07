#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, logging

from PySide import QtGui, QtCore

from DragDropUI import *
from InputScheme import *

from GazeCalibrationWindow import CalibrationWindow

window = None
gazeCalibrationWindow = None
scheme = None
def main(selectedScheme, app=None):
	global window, gazeCalibrationWindow, scheme
	
	scheme = selectedScheme
	
	forceStart = app is None
	if forceStart:
		app = QtGui.QApplication(sys.argv)

	window = DragDropTaskWindow()
	
	def imageMoved(imageName, destination):
		logging.info('Moved %s to %s', imageName, destination)
		
		if window.getRemainingImageCount() < 1:
			QtCore.QTimer.singleShot(1000, app.exit)
		
	scheme.imageMoved.connect(imageMoved)

	if type(scheme).__name__ in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'LeapOnlyScheme']:
		window.optionsWindow = LeapOptionsWindow(scheme)
		window.optionsWindow.scalingChanged.connect(scheme.setScaling)
		window.optionsWindow.grabThresholdChanged.connect(scheme.setGrabThreshold)
		window.optionsWindow.releaseThresholdChanged.connect(scheme.setReleaseThreshold)
		
	if type(scheme).__name__ in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'GazeOnlyScheme', 'GazeAndKeyboardScheme']:
		gazeCalibrationWindow = CalibrationWindow()
		gazeCalibrationWindow.closed.connect(showMainWindow)
		gazeCalibrationWindow.show()
	else:
		showMainWindow()

	if forceStart:
		app.exec_()
	return window
	
def showMainWindow():
	global window, scheme
	scheme.setWindow(window)
	window.showFullScreen()
	window.tileSubWindows()
	scheme.start()

if __name__ == '__main__':
	scheme = getattr(InputScheme, sys.argv[0])()
	sys.exit(main(scheme))
