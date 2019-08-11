#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2019 by sailoog <https://github.com/sailoog/openplotter>
#                     e-sailing <https://github.com/e-sailing/openplotter>
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import time, subprocess, os
from openplotterSettings import language

#TODO set network startup
class Start():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		self.initialMessage = ''

		
	def start(self):
		green = ''
		black = ''
		red = ''

		time.sleep(2)
		return {'green': green,'black': black,'red': red}

class Check():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(__file__)
		language.Language(currentdir,'openplotter-i2c',currentLanguage)
		self.initialMessage = _('Checking I2C...')


	def check(self):
		green = ''
		black = ''
		red = ''

		try:
			subprocess.check_output(['i2cdetect', '-y', '0']).decode('utf-8')
			black = _('I2C enabled')
			red = _('Your Raspberry Pi is too old.')
		except:
			try:
				#TODO add running checkimg
				subprocess.check_output(['i2cdetect', '-y', '1']).decode('utf-8')
				black = _('I2C enabled')
			except:
				red = _('Please enable I2C interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
		

		return {'green': green,'black': black,'red': red}

