# -*- coding: utf-8 -*-
"""
    MCP23017 module for Joyspyck
 
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

import board
import busio
import logging
import digitalio

from adafruit_mcp230xx.mcp23017 import MCP23017
from .ButtonManager import ButtonStatus, ButtonController

module_logger = logging.getLogger('Joyspyck.ButtonControllers.MCP23017_ButtonController')
class MCP23017_ButtonController (ButtonController):

	def __init__(self, config):
		super().__init__(config)

		self._logger = logging.getLogger('Joyspyck.ButtonControllers.MCP23017_ButtonController')

		# Specific of that MCP
		self._num_buttons = 16

		if 'address' not in self._config['options']:
			self._config['options']['address'] = 0x20

		self._address = self._config['options']['address'] \
			if isinstance(self._config['options']['address'], int) \
			else int(self._config['options']['address'], 16)

	def connect(self):
		try:
			# Initialize MCP object
			self._i2c = busio.I2C(board.SCL, board.SDA)
			self._mcp = MCP23017(self._i2c, address=self._address)

			self._buttons = []
			for i in range(0, self._num_buttons):
				self._buttons.append(self._mcp.get_pin(i))
				self._buttons[i].direction = digitalio.Direction.INPUT
				self._buttons[i].pull = digitalio.Pull.UP

			self._logger.info("[connect] MCP23017 initialized on address {}".format(self._address))

		except Exception as ex:
			self._logger.error("[connect] Error connecting to device on address {}:\n{}".format(self._address, str(ex)))
			return False
		return True

	def num_buttons(self):
		return self._num_buttons

	def button_status(self, index):
		if index >=0 and index < self._num_buttons:
			return  ButtonStatus.UNPRESSED if self._buttons[index].value else ButtonStatus.PRESSED
		return ButtonStatus.UNKNOWN
