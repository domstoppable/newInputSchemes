#!/usr/bin/python3
# -*- coding: utf-8 -*-

from subprocess import Popen

import sys
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

app = QtGui.QApplication(sys.argv)

def schemeSelected(schemeName):
	app.exit()
	Popen( [ 'pythonw.exe', 'drag-and-drop-task.py', schemeName])

def main(args):
	window = SchemeSelector()
	window.show()
	window.selected.connect(schemeSelected)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
