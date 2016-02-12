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
		
		if schemeName is None:
			schemeName = args[1]

#		try:
		scheme = getattr(InputScheme, schemeName)(window)
#		except:
#			raise Exception("Unknown scheme %s" % schemeName)

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
