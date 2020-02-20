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
import os
from openplotterSettings import language

class Ports:
	def __init__(self,conf,currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-i2c',currentLanguage)
		self.connections = []

	def usedPorts(self):
		try:
			i2c_sensors = eval(self.conf.get('I2C', 'sensors'))
		except: i2c_sensors = []
		if i2c_sensors:
			for i in i2c_sensors:
				self.connections.append({'id':i, 'description':_('I2C Sensors'), 'data':'Signal K', 'direction':'2', 'type':'UDP', 'mode':'client', 'address':'localhost', 'port':i2c_sensors[i]['port'], 'editable':'1'})
		return self.connections