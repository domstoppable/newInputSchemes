#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

def main(args):
	app = QtGui.QApplication(sys.argv)

	if args[1] == 'LookGrabLookDropScheme':
		scheme = LookGrabLookDropScheme()
	elif args[1] == 'LeapMovesMeScheme':
		scheme = LeapMovesMeScheme()
	elif args[1] == 'MouseOnlyScheme':
		scheme = MouseOnlyScheme()
	elif args[1] == 'LeapOnlyScheme':
		scheme = LeapOnlyScheme()

	window = DragDropTaskWindow()
	window.showFullScreen()
	window.tileSubWindows()

	app.exec_()

	scheme.quit()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
