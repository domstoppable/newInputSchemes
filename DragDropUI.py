from PySide import QtGui, QtCore

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
