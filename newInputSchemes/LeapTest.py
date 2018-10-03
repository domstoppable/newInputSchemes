import sys, os, time, inspect, random, subprocess

src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

import Leap

class LeapListener(Leap.Listener):
	def __init__(self):
		super().__init__()

	def on_connect(self, controller):
		print("Connected")
		
	def on_disconnect(self, controller):
		print("Disconnected")
		
	def on_frame(self, controller):
		print(controller.frame())

controller = Leap.Controller()
listener = LeapListener()
def main():
	controller.set_policy_flags(Leap.Controller.POLICY_BACKGROUND_FRAMES)
	controller.add_listener(listener)

if __name__ == "__main__":
	main()
	while True:
		print("Test")
		time.sleep(.1)

