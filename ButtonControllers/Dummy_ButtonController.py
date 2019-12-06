# -*- coding: utf-8 -*-
"""
    Dummy ButtonController for Joyspyck
 
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

import random

from .ButtonManager import ButtonController, ButtonStatus

class Dummy_ButtonController (ButtonController):

    def __init__(self, config):
        super().__init__(config)
        self._button_status = ButtonStatus.UNKNOWN
        self._num_buttons = 16

    def num_buttons(self):
        return self._num_buttons

    def button_status(self, index):
        if index < 0 or index > (self._num_buttons - 1):
            return None
        return random.randint(0, 1)
