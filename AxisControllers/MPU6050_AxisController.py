# -*- coding: utf-8 -*-
"""
    MPU6050 module for Joyspyck
 
	Under MIT License

    Copyright (c) 2019 Guillermo Climent <willyneutron2@gmail.com>
 
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

import math
import smbus
import logging

from .AxisManager import AxisController

module_logger = logging.getLogger('Joyspyck.AxisControllers.MPU6050_AxisController')

# MPU6050 I2C addresses
# https://www.invensense.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
ACCEL_CONFIG = 0x1C
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F

# Check how to get tilt info from accelerometer
# https://www.analog.com/media/en/technical-documentation/application-notes/AN-1057.pdf (page 7)
def _get_y_rotation(x, y, z):
	radians = math.atan2(_dist(y,z), x)
	return math.degrees(radians)

def _get_x_rotation(x, y, z):
	radians = math.atan2(_dist(x,z), y)
	return math.degrees(radians)

def _get_z_rotation(x, y, z):
	radians = math.atan2(_dist(x,y), z)
	return math.degrees(radians)

def _dist(a,b):
	return math.sqrt((a*a)+(b*b))

# Main class
class MPU6050_AxisController (AxisController):

	def __init__(self, config):
		super().__init__(config)
		
		# Set logger
		self._logger = logging.getLogger('Joyspyck.AxisControllers.MPU6050_AxisController')
		
		# Set config
		self._num_axis = 3 # X, Y and Z

		if 'busnum' not in self._config['options']:
			self._config['options']['busnum'] = 1

		self._busnum = self._config['options']['busnum'] \
		if isinstance(self._config['options']['busnum'], int) \
		else int(self._config['options']['busnum'], base=10)

		if 'address' not in self._config['options']:
			self._config['options']['address'] = 0x68

		self._address = self._config['options']['address'] \
		if isinstance(self._config['options']['address'], int) \
		else int(self._config['options']['address'], base=16)

		if 'calibration_threshold' not in self._config['options']:
			self._config['options']['calibration_threshold'] = 0.009

		self._calibration_threshold = self._config['options']['calibration_threshold'] \
		if isinstance(self._config['options']['calibration_threshold'], float) \
		else float(self._config['options']['calibration_threshold'])

		# Extreme values are 180° and -180° due to the limitations of using one single
		# sensor: the acceleration generated at an inclination of N° is the same as the acceleration generated at an 
		# inclination of 180° − N°
		# https://www.analog.com/media/en/technical-documentation/application-notes/AN-1057.pdf (page 4)
		self._calibration_max = 180
		self._calibration_min = 0

	def connect(self):
		try:
			# Initialize smbus object.
			self._bus = smbus.SMBus(self._busnum)

			# Check i2c register map:
			# https://www.invensense.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf

			# Set device config
			self._bus.write_byte_data(self._address, SMPLRT_DIV, 7)	# Set sample rate divider to 7
			self._bus.write_byte_data(self._address, PWR_MGMT_1, 1) # Clock source set to PLL with X axis gyroscope reference
			self._bus.write_byte_data(self._address, CONFIG, 0)		# Disable FSYNC function
			self._bus.write_byte_data(self._address, INT_ENABLE, 1)	# FIFO_OFLOW_EN Enabled
			
			# Set gyro and accel configuration
			self._bus.write_byte_data(self._address, GYRO_CONFIG, 24)	# 0x18 sets FS_SEL (gyro sentitivity) to ± 1000 °/s
			self._bus.write_byte_data(self._address, ACCEL_CONFIG, 0)	# 0x00 sets AFS_SEL (accel0 sentitivity) to ± 2g

			self._logger.info("[connect] MPU6050 initialized on address {} in bus {}".format(self._address, self._bus))

		except Exception as ex:
			self._logger.error("[connect] Error connecting to device on address {}:\n{}".format(self._address, str(ex)))
			return False
		return True

	def axis_value(self, index):

		# Check valid axis index
		if index < 0 or index > (self._num_axis - 1):
			return None

		# Get value for accelerometer for every axis. Normalizing with 16384 because accel sensitivity is set to ± 2g
		# Mode info on that in https://store.invensense.com/datasheets/invensense/MPU-6050_DataSheet_V3%204.pdf (page 13)
		accel_x = self._read_word_2c(ACCEL_XOUT_H) / 16384.0
		accel_y = self._read_word_2c(ACCEL_YOUT_H) / 16384.0
		accel_z = self._read_word_2c(ACCEL_ZOUT_H) / 16384.0

		# Apply normalization function. Expand range.
		if index == 0:
			read_value = _get_x_rotation(accel_x, accel_y, accel_z)
		elif index == 1:
			read_value = _get_y_rotation(accel_x, accel_y, accel_z)
		else:
			read_value = _get_z_rotation(accel_x, accel_y, accel_z)
		
		translated_value = self._post_calibration_min + ((read_value) * (self._post_calibration_max - self._post_calibration_min)) / (self._calibration_max - self._calibration_min)

		# Apply zero zone percentage.
		zero_min = -(self._post_calibration_max - self._post_calibration_min) * self._calibration_threshold
		zero_max = -zero_min

		if zero_min < translated_value < zero_max:
			return 0
		else:
			return translated_value

	# SMBUS auxiliary functions 
	def _read_byte(self, reg):
		return self._bus.read_byte_data(self._address, reg)
	
	def _read_word(self, reg):
		h = self._bus.read_byte_data(self._address, reg)
		l = self._bus.read_byte_data(self._address, reg+1)
		value = (h << 8) + l
		return value
	
	def _read_word_2c(self, reg):
		val = self._read_word(reg)

		# Transform it in a signed number
		if (val >= 0x8000):
			return -((65535 - val) + 1)
		else:
			return val

