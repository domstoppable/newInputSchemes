#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, logging, time

from PySide import QtGui, QtCore

from DragDropUI import *
from InputScheme import *

from GazeCalibrationWindow import CalibrationWindow

window = None
loadingWindow = None
gazeCalibrationWindow = None
scheme = None

startTime = None
correct = 0
incorrect = 0
def main(selectedScheme, app=None):
	global window, gazeCalibrationWindow, scheme, startTime, correct, incorrect
	
	scheme = selectedScheme
	
	forceStart = app is None
	if forceStart:
		app = QtGui.QApplication(sys.argv)

	window = DragDropTaskWindow()
	window.closed.connect(closeDown)
	
	def imageMoved(imageName, destination):
		global window, gazeCalibrationWindow, scheme, startTime, correct, incorrect
		logging.info('Moved %s to %s', imageName, destination)
		
		if startTime is None:
			startTime = time.time()
		animalType = imageName.split('_')[0]
		if animalType.lower() in destination.lower():
			correct += 1
		else:
			incorrect += 1
			
		if window.getRemainingImageCount() < 1:
			try:
				score = 8000.0 * pow(correct / (correct + incorrect), 3) / pow(time.time() - startTime, 0.5)
			except Exception as exc:
				logging.error('Error calculating score')
				logging.error('%s' % exc)
				score = -1
				
			logging.info('Score: %d' % score)
			closeDown()
			window.hide()
			box = QtGui.QMessageBox(QtGui.QMessageBox.Information, 'Done!', 'Score: %d' % score, QtGui.QMessageBox.Ok, window)
			box.finished.connect(window.close)
			box.show()
		
	scheme.imageMoved.connect(imageMoved)

	window.optionsWindow = DeviceOptionsWindow()
	if hasattr(scheme, 'gestureTracker'):
		window.optionsWindow.addGestureControls(scheme)
		
	if hasattr(scheme, 'gazeTracker'):
		gazeCalibrationWindow = CalibrationWindow(scheme.gazeTracker)
		gazeCalibrationWindow.closed.connect(showMainWindow)
		gazeCalibrationWindow.show()
		
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
	scheme.start()

if __name__ == '__main__':
	scheme = getattr(InputScheme, sys.argv[0])()
	sys.exit(main(scheme))
