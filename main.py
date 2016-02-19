#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from PySide import QtGui, QtCore
from DragDropUI import *
from InputScheme import *

app = QtGui.QApplication(sys.argv)

def schemeSelected(schemeName):
	app.exit()
	outputFilename = 'output.txt'
	with open(outputFilename, 'w') as f:
		subprocess.call(['pythonw.exe', 'DragAndDropTask.py', schemeName], stdout=f)
	subprocess.call(['cat', outputFilename])

def main(args):
	window = SchemeSelector()
	window.show()
	window.selected.connect(schemeSelected)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
