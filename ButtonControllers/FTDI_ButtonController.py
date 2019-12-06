# -*- coding: utf-8 -*-
"""
    FTDI module for Joyspyck
 
	Under MIT License

    Copyright (c) 2019 Guillermo Climent  <willyneutron2@gmail.com>

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

import logging

from pyftdi.gpio import GpioController, GpioException
from .ButtonManager import ButtonStatus, ButtonController

module_logger = logging.getLogger('Joyspyck.ButtonControllers.FTDI_ButtonController')
class FTDI_ButtonController (ButtonController):

	def __init__(self, config):
		super().__init__(config)

		self._logger = logging.getLogger('Joyspyck.ButtonControllers.FTDI_ButtonController')

		if 'ftdi_url' not in self._config['options']:
			self._config['options']['ftdi_url'] = ''

		self._ftdi_url = self._config['options']['ftdi_url']

	def connect(self):
		try:
			# Initialize FTDI device in GPIO mode
			self._gpio = GpioController()
			self._gpio.open_from_url(self._ftdi_url)
			self._logger.info("[connect] FTDI GPIO opened from {}.".format(self._ftdi_url))

			# Get the GPIO port length
			self._num_buttons = self._gpio.pins.bit_length()
			self._logger.info("[connect] Detected {} inputs.".format(self._num_buttons))

			# Set input direction for all pins.
			self._gpio.set_direction(self._gpio.pins, 0x0000)

			# Get initial state of the pins
			self._buttons = self._gpio.read()

		except Exception as ex:
			self._logger.error("[connect] Error connecting to device on address {}:\n{}".format(self._ftdi_url, str(ex)))
			return False
		return True

	def num_buttons(self):
		return self._num_buttons

	def button_status(self, index):
		self._buttons = self._gpio.read()

		# Buttons are PULL DOWN, pressed when connected to GND, low logic level.
		return ButtonStatus.UNPRESSED if (self._buttons) >> index & 0x01 else ButtonStatus.PRESSED
