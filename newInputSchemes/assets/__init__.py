import sys, os, platform
from PySide import QtGui

try:
	basePath = sys._MEIPASS
except:
	basePath = os.path.abspath('.')
	
basePath = os.path.join(basePath, 'assets')



def getFileList(path):
	path = os.path.join(basePath, path)
	return [ f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) ]

def getPathToAsset(path):
	return os.path.join(basePath, path)
	
def getQImage(path):
	return QtGui.QImage(getPathToAsset(path))
	
def getQPixmap(path):
	return QtGui.QPixmap.fromImage(getQImage(path))
	

def play(sound):
	f = getPathToAsset('sounds/%s.wav' % sound)
	if platform.system() == 'Linux':
		os.system('aplay "%s" >/dev/null 2>&1 &' % f)
	else:
		QtGui.QSound.play(f)

if __name__ == '__main__':
	for i in range(3):
		play('drop')
		play('release')
		play('select')
		play('bummer')



