#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import logging

from PySide import QtGui, QtCore

from DragDropUI import *
import InputScheme
import DragAndDropTask

logging.basicConfig(
	format='%(levelname)s %(asctime)s %(message)s',
	filename='example.log',
	level=logging.DEBUG,
)

app = QtGui.QApplication(sys.argv)
appWindow = None
scheme = None

def schemeSelected(schemeName):
	global app, appWindow, scheme
	# need to keep a handle on the window, or else it will be garbage collected
	try:
		scheme = getattr(InputScheme, schemeName)()
		logging.debug('Loaded scheme %s', schemeName)
		appWindow = DragAndDropTask.main(scheme, app=app)
	except Exception as exc:
		msgBox = QtGui.QMessageBox()
		msgBox.setText("An error has occurred :(\n\n%s" % exc);
		msgBox.exec();
		sys.exit(1)

def main(args):
	global app
	window = InputScheme.SchemeSelector()
	window.show()
	window.selected.connect(schemeSelected)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
