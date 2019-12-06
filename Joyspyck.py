# -*- coding: utf-8 -*-
"""
    Joyspyck for Joyspyck
 
	Under MIT License

    Copyright (c) 2019 Noemi Escudero del Olmo <noemi.escudero.del.olmo@gmail.com>
 
	Permission is hereby granted, free of charge, to any person obtaining a copy of this software
	and associated documentation files (the “Software”), to deal in the Software without restriction,
	including without limitation the rights to use, copy, modify, merge, publish, distribute,
	sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or 
	substantial portions of the Software.

	THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
	NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
	IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
	SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import time
import json
import signal
import logging
import argparse
import threading
import Joystick

# Possible returns of the main python app
JSON_FILE_NOT_OPEN = -1
JSON_FILE_PATH_NOT_PROVIDED = -2
JSON_NOT_LOAD = -3

_joysticks = []				# Array of created joysticks
_update_workers = []		# Array of workers (threads) in charge of updating the joysticks

logger = logging.getLogger('Joyspyck')

# This signal handler is called when SIGINT is received when in threaded mode
# This way, all thread can be cleaned before exiting.
def signal_handler(sig, frame):
	logger.info("[signal_handler] Stopping workers...")
	for w in _update_workers:
		w.stop()


class UpdatingThreadType:
	BUTTON_THREAD = 0
	AXIS_THREAD = 1


# Definition of the threads in charge of updating uinput devices with the
# information gathered from hardware devices. Depending on the type, one worker
# will update all ButtonControllers or all AxisControllers contained inside a
# joystick.
class UpdateWorker (threading.Thread):
	def __init__(self, worker_joystick, worker_type):
		threading.Thread.__init__(self)
		self._joysticks = worker_joystick
		self._type = worker_type
		self._working = False

	def stop (self):
		self._working = False

	def run(self):
		self._working = True
		if self._type == UpdatingThreadType.BUTTON_THREAD:
			self.update_buttons()
		else:
			self.update_axis()

	def update_buttons (self):
		while self._working:
			for self._joystick in _joysticks:
				self._joystick.update_buttons()
			time.sleep(self._joystick.wait_time_buttons)

	def update_axis (self):
		while self._working:
			for self._joystick in _joysticks:
				self._joystick.update_axis()
			time.sleep(self._joystick.wait_time_axis)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Joyspyck')
	parser.add_argument('config_file', metavar='JSON Config file',
						help='JSON containing the Joystick configuration.')
	parser.add_argument('--wait_time', metavar='sleep between polling', type=float,
						help='JSON containing the Joystick configuration.')
	parser.add_argument('-v', action='store_true', required=False, 
						help='Activate verbose.')

	args = parser.parse_args()

	# Set logger    
	log_formatter = logging.Formatter('%(asctime)s.%(msecs)06d [%(name)s] [%(levelname)-5.5s] %(message)s', datefmt='%H:%M:%S')
	if (args.v):
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.INFO)
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(log_formatter)
	logger.addHandler(console_handler)

	if args.config_file:
		# Check file existence
		json_file = None
		try:
			json_file = open(args.config_file, "r+")
		except IOError:
			logger.error("[main] Could not open config file.")
			exit(JSON_FILE_NOT_OPEN)

		# Load json and create all joysticks
		with json_file:
			try:
				data = json.load(json_file)
				for joystick_conf in data:
					_joysticks.append(Joystick.Joystick(joystick_conf))
			except Exception as ex:
				logger.error("[main] Exception when loading config json: {0}".format(str(ex)))
				exit(JSON_NOT_LOAD)

		# Loop over Joysticks updating states. SINGLE THREADED MODE.
		if args.wait_time:
			while True:
				for joystick in _joysticks:
					joystick.update()
				time.sleep(args.wait_time)

		# MULTI THREADED MODE.
		else:

			# Capture SIGINT to exit
			signal.signal(signal.SIGINT, signal_handler)

			# Create workers
			for joystick in _joysticks:
				if joystick.num_axis_controllers() > 0:
					axis_worker = UpdateWorker(joystick, UpdatingThreadType.AXIS_THREAD)
					axis_worker.start()
					_update_workers.append(axis_worker)

				if joystick.num_button_controllers() > 0:
					button_worker = UpdateWorker(joystick, UpdatingThreadType.BUTTON_THREAD)
					button_worker.start()
					_update_workers.append(button_worker)

			for worker in _update_workers:
				while worker.isAlive():
					worker.join(timeout=1)

	else:
		logger.error("[main] Supply a path for the config file.")
		exit(JSON_FILE_PATH_NOT_PROVIDED)
