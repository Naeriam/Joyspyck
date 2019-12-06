# -*- coding: utf-8 -*-
"""
    AxisManager for Joyspyck
 
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

from UInputEvents import UInputEvents

# Factory to generate AxisControllers depending on the supplied type.
def get_axis_controller(controller_config):
	ret = None

	if controller_config["type"] == "ADS1115":
		from .ADS1115_AxisController import ADS1115_AxisController
		ret = ADS1115_AxisController(controller_config)
	elif controller_config["type"] == "Dummy":
		from .Dummy_AxisController import Dummy_AxisController
		ret = Dummy_AxisController(controller_config)
	elif controller_config["type"] == "MPU6050":
		from .MPU6050_AxisController import MPU6050_AxisController
		ret = MPU6050_AxisController(controller_config)

	if ret is not None and ret.connect():
		return ret
	else:
		return None

class AxisController (object):

    _post_calibration_max = 32765
    _post_calibration_min = -32765

    def __init__(self, config):
        self._config = config
        self._events = []
        self._num_events = 0
        self._num_axis = 0

        # Check if config have all data
        if 'name' not in self._config:
            raise ValueError("AxisController have not a name.")
        if 'type' not in self._config:
            raise ValueError("AxisController {0} does not have a type.".format(self._config['name']))
        if 'options' not in self._config:
            raise ValueError("AxisController {0} does not have a options.".format(self._config['name']))
        if 'mapping' not in self._config:
            raise ValueError("AxisController {0} does not have a mapping.".format(self._config['name']))

        # Get events from UInputEvents
        for event in self._config['mapping']:
            if event in UInputEvents:
                self._events.append(UInputEvents[event] + (-32766, 32766, 0, 0))
            else:
                raise ValueError("Event {0} is not a valid UInputEvent".format(event))
        
        self._num_events = len(self._events)

    def num_axis(self):
        return self._num_axis

    def num_mapped_axis(self):
	    return self._num_events

    def axis_value(self, index):
        return 0

    def type(self):
        return self._config['type']

    def get_events(self):
        return self._events

    def connect(self):
        return True
