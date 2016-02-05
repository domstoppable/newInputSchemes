#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

def main(args=None, scheme=None, app=None):
	try:
		if app is None:
			app = QtGui.QApplication(sys.argv)

		window = DragDropTaskWindow()
		
		if scheme is None:
			scheme = args[1]

		if scheme == 'LookGrabLookDropScheme':
			scheme = LookGrabLookDropScheme(window)
		elif scheme == 'LeapMovesMeScheme':
			scheme = LeapMovesMeScheme(window)
		elif scheme == 'MouseOnlyScheme':
			scheme = MouseOnlyScheme(window)
		elif scheme == 'LeapOnlyScheme':
			scheme = LeapOnlyScheme(window)
		else:
			raise Exception("Unknown scheme %s" % scheme)

		window.showFullScreen()
		window.tileSubWindows()

		if scheme in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'LeapOnlyScheme']:
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
