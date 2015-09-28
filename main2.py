import os, sys, inspect, time, _thread
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

from peyetribe import EyeTribe
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

def main(args):
	print("Test...")
	gestureTracker = Leap.Controller()

	# Keep this process running until Enter is pressed
	print("Press Enter to quit...")
	gestureTracker.add_listener(GestureListener())
	while True:
		pass

class GestureListener(Leap.Listener):
	def __init__(self):
		super().__init__()
		
	def on_connect(self, controller):
		print("Gesture tracker connected!")

	def on_frame(self, controller):
		print(gestureTracker.frame())


def main2(args):
	eyeTracker = EyeTribe()
	gestureTracker = Leap.Controller()

	# Keep this process running until Enter is pressed
	print("Press Enter to quit...")
	try:
		sys.stdin.readline()
	except KeyboardInterrupt:
		pass
		 
		 
	#eyeTracker.connect()
	#n = eyeTracker.next()

	print("eT;dT;aT;Fix;State;Rwx;Rwy;Avx;Avy;LRwx;LRwy;LAvx;LAvy;RSz;LCx;LCy;RRwx;RRwy;RAvx;RAvy;RS;RCx;RCy\n")

	tracker.pushmode()
	count = 0
	while count < 100:
		n = tracker.next()
		p = n.avg
		print("%d, %d" % (p.x, p.y))
		count += 1

	tracker.pullmode()
	tracker.close()
	return 0

if __name__ == '__main__':
	print("hi")
	sys.exit(main(sys.argv))
