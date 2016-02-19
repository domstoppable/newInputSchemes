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
	errorFilename = 'error.txt'
	with open(outputFilename, 'w') as f:
		with open(errorFilename, 'w') as e:
			subprocess.call([sys.executable, 'DragAndDropTask.py', schemeName], stdout=f, stderr=e)

	print("\n*** OUTPUT *** ")
	subprocess.call(['cat', outputFilename])

	print("\n\n*** ERRORS *** ")
	subprocess.call(['cat', errorFilename])

def main(args):
	window = SchemeSelector()
	window.show()
	window.selected.connect(schemeSelected)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
