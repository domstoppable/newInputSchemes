#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

def main(args):
	try:
		app = QtGui.QApplication(sys.argv)

		window = DragDropTaskWindow()

		if args[1] == 'LookGrabLookDropScheme':
			scheme = LookGrabLookDropScheme(window)
		elif args[1] == 'LeapMovesMeScheme':
			scheme = LeapMovesMeScheme(window)
		elif args[1] == 'MouseOnlyScheme':
			scheme = MouseOnlyScheme(window)
		elif args[1] == 'LeapOnlyScheme':
			scheme = LeapOnlyScheme(window)
		else:
			raise Exception("Unknown scheme %s" % args[1])

		window.showFullScreen()
		window.tileSubWindows()

		if args[1] in ['LookGrabLookDropScheme', 'LeapMovesMeScheme', 'LeapOnlyScheme']:
			window.optionsWindow = LeapOptionsWindow(scheme)
			window.optionsWindow.scalingChanged.connect(scheme.setScaling)
			window.optionsWindow.grabThresholdChanged.connect(scheme.setGrabThreshold)
			window.optionsWindow.releaseThresholdChanged.connect(scheme.setReleaseThreshold)

		app.exec_()
		scheme.quit()
	except Exception as exc:
		msgBox = QtGui.QMessageBox()
		msgBox.setText("ERROR: %s" % exc);
		msgBox.exec();
		sys.exit(1)
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
