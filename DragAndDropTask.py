#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, logging

from PySide import QtGui, QtCore

from DragDropUI import *
from InputScheme import *

def main(scheme, app=None):
	forceStart = app is None
	if forceStart:
		app = QtGui.QApplication(sys.argv)

	window = DragDropTaskWindow()
	
	def imageMoved(imageName, destination):
		logging.info('Moved %s to %s', imageName, destination)
		
		if window.getRemainingImageCount() < 1:
			QtCore.QTimer.singleShot(1000, app.exit)
		
	scheme.setWindow(window)
	scheme.imageMoved.connect(imageMoved)

	window.showFullScreen()
	window.tileSubWindows()

	if type(scheme).__name__ in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'LeapOnlyScheme']:
		window.optionsWindow = LeapOptionsWindow(scheme)
		window.optionsWindow.scalingChanged.connect(scheme.setScaling)
		window.optionsWindow.grabThresholdChanged.connect(scheme.setGrabThreshold)
		window.optionsWindow.releaseThresholdChanged.connect(scheme.setReleaseThreshold)

	if forceStart:
		app.exec_()
	return window

if __name__ == '__main__':
	scheme = getattr(InputScheme, sys.argv[0])()
	sys.exit(main(scheme))
