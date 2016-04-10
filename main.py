#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os, inspect
import signal
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

def bailOut(*args):
	global app
	
	try:
		if scheme is not None:
			scheme.stop()
		app.exit()
	except Exception as exc:
		print(exc)
		pass
	sys.exit(1)
	
signal.signal(signal.SIGTERM, bailOut)
signal.signal(signal.SIGINT, bailOut)


def schemeLoaded():
	global app, appWindow, scheme
	appWindow.hide()
	appWindow = DragAndDropTask.main(scheme, app=app)

def schemeSelected(schemeName):
	global app, appWindow, scheme
	# need to keep a handle on the window, or else it will be garbage collected
	try:
		scheme = getattr(InputScheme, schemeName)()
		if scheme.isReady():
			schemeLoaded()
		else:
			scheme.ready.connect(schemeLoaded)
			scheme.error.connect(appWindow.displayError)
		
		logging.debug('Loaded scheme %s', schemeName)
	except Exception as exc:
		msgBox = QtGui.QMessageBox()
		msgBox.setText("An error has occurred :(\n\n%s" % exc);
		msgBox.exec();
		
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		logging.error(exc_type, fname, exc_tb.tb_lineno)
		    
		sys.exit(1)

def main(args):
	global app, appWindow
	logging.info('Main app started')
	appWindow = InputScheme.SchemeSelector()
	appWindow.show()
	appWindow.selected.connect(schemeSelected)
	appWindow.closed.connect(bailOut)
	app.exec_()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
