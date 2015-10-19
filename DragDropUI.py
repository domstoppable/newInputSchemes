import os, random
from PySide import QtGui, QtCore
from FlowLayout import *

class IconLayout(QtGui.QWidget):
	highlight = QtCore.Signal()
	unhighlight = QtCore.Signal()
	blink = QtCore.Signal()

	def __init__(self, image, text):
		super().__init__()
		self.image = image
		self.text = text
		self.highlighted = False

		self.highlight.connect(self._highlight)
		self.unhighlight.connect(self._unhighlight)
		self.blink.connect(self._blink)

		self.imageWidget = QtGui.QLabel()
		self.imageWidget.setAlignment(QtCore.Qt.AlignCenter)
		self.imageWidget.setPixmap(QtGui.QPixmap.fromImage(self.image))

		self.labelWidget = QtGui.QLabel()
		self.labelWidget.setText('<font size="32"><center>%s</center></font>' % self.text)
		
		self.selectionEffect = QtGui.QGraphicsColorizeEffect(self)
		self.setGraphicsEffect(self.selectionEffect)
		self.selectionEffect.setEnabled(False)

		glow = QtGui.QGraphicsDropShadowEffect(self)
		glow.setColor(QtGui.QColor(255, 255, 255))
		glow.setOffset(0, 0)
		glow.setBlurRadius(15)
		self.labelWidget.setGraphicsEffect(glow)

		self.initUI()

	def initUI(self):
		layout = QtGui.QVBoxLayout()
		layout.setSpacing(0)
		self.setLayout(layout)
		
		layout.addWidget(self.imageWidget)
		layout.addWidget(self.labelWidget)
		
		self.setHighlight(False)
		
	@QtCore.Slot()
	def _highlight(self):
		self.setHighlight(True)
		
	@QtCore.Slot()
	def _unhighlight(self):
		self.setHighlight(False)
		
	def toggleHighlight(self):
		self.setHighlight(not self.graphicsEffect().isEnabled())
		
	def setHighlighted(self):
		self.setHighlight(True)
		
	def setUnhighlighted(self):
		self.setHighlight(False)
		
	def setHighlight(self, enabled):
		self.graphicsEffect().setEnabled(enabled)
		self.update()
		
	def _blink(self):
		self.setHighlight(True)
		QtCore.QTimer.singleShot(250, self.setUnhighlighted)

class FolderIcon(IconLayout):
	def initUI(self):
		layout = QtGui.QStackedLayout()
		layout.setStackingMode(layout.StackAll)
		self.setLayout(layout)
		
		layout.addWidget(self.labelWidget)
		layout.addWidget(self.imageWidget)
		
		self.setHighlight(False)

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
