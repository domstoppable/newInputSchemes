#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os, inspect
import logging, time

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

from PySide import QtGui, QtCore

from DragDropUI import *
import InputScheme
import DragAndDropTask

logging.basicConfig(
	format='%(levelname)-8s %(asctime)s %(message)s',
	filename='logs/%d.log' % int(time.time()),
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
		
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		logging.error(exc_type, fname, exc_tb.tb_lineno)
		    
		sys.exit(1)

def main(args):
	global app
	logging.info('Main app started')
	window = InputScheme.SchemeSelector()
	window.show()
	window.selected.connect(schemeSelected)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
