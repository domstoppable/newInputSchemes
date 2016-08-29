#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os, inspect
import signal
import logging, time, settings

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

from PySide import QtGui, QtCore

from DragDropUI import *
import InputScheme
import DragAndDropTask

QtGui.QApplication.setStyle('Cleanlooks')
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

def schemeSelected(schemeName, participantID, practiceOnly):
	global app, appWindow, scheme
	# need to keep a handle on the window, or else it will be garbage collected
	
	participantPath = 'logs/%s' % participantID
	if not os.path.isdir(participantPath):
		os.makedirs(participantPath)

	if practiceOnly:
		logFile = '%s/%d-%s-practice.log' % (participantPath, int(time.time()), schemeName)
	else:
		logFile = '%s/%d-%s.log' % (participantPath, int(time.time()), schemeName)
		
	logging.basicConfig(
		format='%(levelname)-8s %(asctime)s %(message)s',
		filename=logFile,
		level=logging.DEBUG,
	)
	settings.loadPersonalSettings(participantID)

	try:
		scheme = getattr(InputScheme, schemeName)()
		if scheme.isReady():
			schemeLoaded()
		else:
			scheme.ready.connect(schemeLoaded)
			scheme.error.connect(appWindow.displayError)
		
		if practiceOnly:
			logging.debug('Loaded PRACTICE scheme %s for participant %s' % (schemeName, participantID))
		else:
			logging.debug('Loaded scheme %s for participant %s' % (schemeName, participantID))
	except Exception as exc:
		QtGui.QMessageBox.critical(None, 'An error has occurred :(', '%s' % exc)
		QtGui.QApplication.closeAllWindows()
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		logging.error('%s:%d - %s' % (fname, exc_tb.tb_lineno, exc))
		raise
		sys.exit(1)

def main(args):
	global app, appWindow

	appWindow = InputScheme.SchemeSelector()
	appWindow.show()
	appWindow.selected.connect(schemeSelected)
	appWindow.closed.connect(bailOut)
	try:
		app.exec_()
	except Exception as exc:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		logging.error('%s:%d - %s' % (fname, exc_tb.tb_lineno, exc))
		sys.exit(1)
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
