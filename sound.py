import platform, os
from PySide import QtGui, QtCore

def play(sound):
	f = "assets/sounds/%s" % sound
	if platform.system() == "Linux":
		os.system('aplay "%s" >/dev/null 2>&1 &' % f)
	else:
		QtGui.QSound.play(f)

if __name__ == '__main__':
	for i in range(3):
		play("drop.wav")
		play("release.wav")
		play("select.wav")
		play("bummer.wav")

