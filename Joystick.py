# -*- coding: utf-8 -*-
"""
    Joystick for Joyspyck
 
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

import uinput
import logging

from AxisControllers.AxisManager import get_axis_controller
from ButtonControllers.ButtonManager import get_button_controller, ButtonStatus

module_logger = logging.getLogger('Joyspyck.Joystick')
# Joystick class models a uinput virtual device (/dev/input/jsX)
#
# Contains arrays of axis and button controllers and is in charge of managing them
# and updating the virtual device with the information it gets from them.
class Joystick:

	def __init__(self, joystick_conf):

		# Store info
		self._logger = logging.getLogger('Joyspyck.Joystick')
		self._button_controllers = []
		self._num_button_controllers = 0
		self._axis_controllers = []
		self._num_axis_controllers = 0
		self._device = None
		self._last_button_state = []
		events = []

		if 'waitTimeButtons' not in joystick_conf:
			self.wait_time_buttons = 0.05
		else:
			self.wait_time_buttons = joystick_conf['waitTimeButtons'] \
				if isinstance(joystick_conf['waitTimeButtons'], float) \
				else int(joystick_conf['waitTimeButtons'], 10)

		if 'waitTimeAxis' not in joystick_conf:
			self.wait_time_axis = 0.05
		else:
			self.wait_time_axis = joystick_conf['waitTimeAxis'] \
				if isinstance(joystick_conf['waitTimeAxis'], float) \
				else int(joystick_conf['waitTimeAxis'], 10)

		# Create button controllers
		for button_controller_conf in joystick_conf["buttonControllers"]:

			button_controller = get_button_controller(button_controller_conf)
			if button_controller is not None:
				self._button_controllers.append(button_controller)
				events = events + button_controller.get_events()
				self._last_button_state.append([ButtonStatus.UNPRESSED for i in range(button_controller.num_buttons())])
			else:
				self._logger.error("[init] Not button controller found.")
		
		self._num_button_controllers = len(self._button_controllers)

		# Create axis controllers
		for axis_controller_conf in joystick_conf["axisControllers"]:
			axis_controller = get_axis_controller(axis_controller_conf)
			if axis_controller is not None:
				self._axis_controllers.append(axis_controller)
				events = events + axis_controller.get_events()
			else:
				self._logger.error("[init] Not axis controller found")
		
		self._num_axis_controllers = len(self._axis_controllers)

		# Create uinput device 
		self._device = uinput.Device(events)

	def update(self):
		# Update axis and buttons
		self.update_axis()
		self.update_buttons()

	def num_axis_controllers (self):
		return self._num_axis_controllers

	def update_axis(self):
		# For each axis controller, update the value of the axis in uinput device
		for axis_controller in self._axis_controllers:
			num_axis = axis_controller.num_mapped_axis()
			for i in range(num_axis):
				try:
					axis_value = int(axis_controller.axis_value(i))
				except:
					axis_controller.connect() # if connection lost, retry connect
					continue
				
				event = axis_controller.get_events()[i][:-4] #- (-32766, 32766, 0, 0)
				self._device.emit(event, axis_value, syn=True if i == (num_axis-1) else False)
				

	def num_button_controllers (self):
		return self._num_button_controllers

	def update_buttons(self):
		# For each button controller, update button status of uinput device
		for i in range(self._num_button_controllers):
			button_controller = self._button_controllers[i]
			num_buttons = button_controller.num_mapped_buttons()
			for j in range(num_buttons):
				value = button_controller.button_status(j)
				try:
					event = button_controller.get_events()[j]
				except:
					button_controller.connect() # if connection lost, retry connect
					continue
				if value == ButtonStatus.PRESSED and self._last_button_state[i][j] == ButtonStatus.UNPRESSED:
					self._device.emit(event, 1)
					self._last_button_state[i][j] = ButtonStatus.PRESSED
				elif value == ButtonStatus.UNPRESSED and self._last_button_state[i][j] == ButtonStatus.PRESSED:
					self._device.emit(event, 0)
					self._last_button_state[i][j] = ButtonStatus.UNPRESSED					
