# -*- coding: utf-8 -*-
"""
    ADS1115 module for Joyspyck
 
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

import adafruit_ads1x15.ads1115 as ADS

from .AxisManager import AxisController
from adafruit_ads1x15.analog_in import AnalogIn

module_logger = logging.getLogger('Joyspyck.AxisControllers.ADS1115_AxisController')
class ADS1115_AxisController (AxisController):
	
	def __init__(self, config):
		super().__init__(config)
		
		self._logger = logging.getLogger('Joyspyck.AxisControllers.ADS1115_AxisController')

		# Specific of that ADS
		self._num_axis = 4

		# Set defaults in config if keys not present
		if 'gain' not in self._config['options']:
			self._config['options']['gain'] = 0

		self._gain = self._config['options']['gain'] \
		if isinstance(self._config['options']['gain'], int) \
		else int(self._config['options']['gain'], base=10)

		if 'address' not in self._config['options']:
			self._config['options']['address'] = 0x48

		self._address = self._config['options']['address'] \
		if isinstance(self._config['options']['address'], int) \
		else int(self._config['options']['address'], base=16)

		if 'calibration_max' not in self._config['options']:
			self._config['options']['calibration_max'] = 32766

		self._calibration_max = self._config['options']['calibration_max'] \
		if isinstance(self._config['options']['calibration_max'], int) \
		else int(self._config['options']['calibration_max'], base=10)

		if 'calibration_min' not in self._config['options']:
			self._config['options']['calibration_min'] = -32766

		self._calibration_min = self._config['options']['calibration_min'] \
		if isinstance(self._config['options']['calibration_min'], int) \
		else int(self._config['options']['calibration_min'],base=10)

		if 'calibration_threshold' not in self._config['options']:
			self._config['options']['calibration_threshold'] = 0.009

		self._calibration_threshold = self._config['options']['calibration_threshold'] \
		if isinstance(self._config['options']['calibration_threshold'], float) \
		else float(self._config['options']['calibration_threshold'])

	def connect(self):
		try:
			# Initialize ADS object
			self._i2c = busio.I2C(board.SCL, board.SDA)
			self._adc = ADS.ADS1115(self._i2c, address=self._address)

			# Set gain
			self._adc.gain = self._gain

			# Create input in channels
			self._channels = [
				AnalogIn(self._adc, ADS.P0),
				AnalogIn(self._adc, ADS.P1),
				AnalogIn(self._adc, ADS.P2),
				AnalogIn(self._adc, ADS.P3),
			]

			self._logger.info("[connect] ADS1115 initialized on address {}".format(self._address))

		except Exception as ex:
			self._logger.error("[connect] Error connecting to device on address {}:\n{}".format(self._address, str(ex)))
			return False
		return True

	def axis_value(self, index):

		# Check valid axis index
		if index < 0 or index > (self._num_axis - 1):
			return None

		# Apply normalization function
		read_value = self._channels[index].value
		translated_value = self._post_calibration_min + ((read_value - 10) * (self._post_calibration_max - self._post_calibration_min)) / (self._calibration_max - self._calibration_min)

		# Apply zero zone
		zero_min = -(self._post_calibration_max - self._post_calibration_min) * self._calibration_threshold
		zero_max = -zero_min

		if zero_min < translated_value < zero_max:
			return 0
		else:
			return translated_value
