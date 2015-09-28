import platform, time
from PySide import QtGui, QtCore

def play(sound):
	if platform.system() == "Linux":
		return
		
	f = "assets/sounds/%s" % sound
	QtGui.QSound.play(f)

if __name__ == '__main__':
	for i in range(3):
		play("drop.wav")
		play("release.wav")
		play("select.wav")
		play("bummer.wav")

