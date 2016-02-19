#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
import InputScheme


def main(args=None, schemeName=None, app=None):
	try:
		if app is None:
			app = QtGui.QApplication(sys.argv)

		window = DragDropTaskWindow()
		
		def imageMoved(imageName, destination):
			print("Moved %s to %s" % (imageName, destination))
			
			if window.getRemainingImageCount() < 1:
				QtCore.QTimer.singleShot(1000, app.exit)
			
		if schemeName is None:
			schemeName = args[1]

		scheme = getattr(InputScheme, schemeName)(window)
		scheme.imageMoved.connect(imageMoved)

		window.showFullScreen()
		window.tileSubWindows()

		if schemeName in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'LeapOnlyScheme']:
			window.optionsWindow = LeapOptionsWindow(scheme)
			window.optionsWindow.scalingChanged.connect(scheme.setScaling)
			window.optionsWindow.grabThresholdChanged.connect(scheme.setGrabThreshold)
			window.optionsWindow.releaseThresholdChanged.connect(scheme.setReleaseThreshold)

		app.exec_()
		scheme.quit()
	except Exception as exc:
		print(exc)
		msgBox = QtGui.QMessageBox()
		msgBox.setText("ERROR: %s" % exc);
		msgBox.exec();
		sys.exit(1)

if __name__ == '__main__':
	sys.exit(main(sys.argv))
