#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys, os, time, inspect, random, subprocess
from PySide import QtGui, QtCore
from FlowLayout import FlowLayout
from IconLayout import *
from InputScheme import *

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))


class ImagesWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout(spacing=15)
		container.setLayout(layout)
	
		imagePath = './assets/animals/'
		images = [ f for f in os.listdir(imagePath) if os.path.isfile(os.path.join(imagePath,f)) ]
		random.shuffle(images)
		for imageName in images:
			image = QtGui.QImage(os.path.join(imagePath, imageName)).scaled(150, 150)

			w = IconLayout(image, imageName)
			layout.addWidget(w)


		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Images')
		
class FoldersWindow(QtGui.QScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.initUI()

	def initUI(self):
		container = QtGui.QWidget()
		layout = FlowLayout()
		
		image = QtGui.QImage('assets/folder.svg').scaled(150, 150)
		folderNames = [
			'Cats', 'Cows', 'Dogs', 'Pigs',
			'Rabbits', 'Birds', 'Bugs', 'Vacation',
			'Unsorted', 'Misc.', 'Kids', 'Art',
			'Trip', 'Backup', 'Old', 'Save',
		]
		folderNames = sorted(folderNames)
		for i in range(len(folderNames)):
			w = FolderIcon(image, folderNames[i])
			layout.addWidget(w)

		container.setLayout(layout)
		self.setWidget(container)
		self.setWindowTitle('Folders')


class DragDropTaskWindow(QtGui.QMdiArea):
	mousePressed = QtCore.Signal(object, object)
	mouseReleased = QtCore.Signal(object, object)
	mouseMoved = QtCore.Signal(object, object)
	
	def __init__(self):
		super().__init__()
		self.setBackground(QtGui.QColor.fromRgb(0, 0, 0))
		self.addSubWindow(ImagesWindow())
		self.addSubWindow(FoldersWindow())
		
		self.setMouseTracking(True)
		
	def setMouseTracking(self, flag):
		def recursive_set(parent):
			for child in parent.findChildren(QtCore.QObject):
				try:
					child.setMouseTracking(flag)
				except:
					pass
				recursive_set(child)
		QtGui.QWidget.setMouseTracking(self, flag)
		recursive_set(self)
		
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.Type.MouseMove:
			self.mouseMoved.emit(obj, event)
		elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
			self.mousePressed.emit(obj, event)
		elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
			self.mouseReleased.emit(obj, event)
			
		return False

def main(args):
	app = QtGui.QApplication(sys.argv)

	#scheme = LookGrabLookDropScheme()
	#scheme = LeapMovesMeScheme()
	#scheme = MouseOnlyScheme()

	container = DragDropTaskWindow()
	container.showFullScreen()
	container.tileSubWindows()

	app.exec_()
	
	scheme.quit()
	
if __name__ == '__main__':
	sys.exit(main(sys.argv))
