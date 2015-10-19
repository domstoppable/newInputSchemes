#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os, time, inspect, random, subprocess
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))



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
