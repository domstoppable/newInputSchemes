#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

def main(args):
	app = QtGui.QApplication(sys.argv)

	#scheme = LookGrabLookDropScheme()
	scheme = LeapMovesMeScheme()
	#scheme = MouseOnlyScheme()

	container = DragDropTaskWindow()
	container.showFullScreen()
	container.tileSubWindows()

	app.exec_()
	
	scheme.quit()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
