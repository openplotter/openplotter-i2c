#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-i2c>
# 
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

class Gpio:
	def __init__(self,conf):
		self.conf = conf
		self.used = [] # {'app':'xxx', 'id':'xxx', 'physical':'n'}

	def usedGpios(self):
		try: sensors = eval(self.conf.get('I2C', 'sensors'))
		except: sensors = []
		exist = False
		for i in sensors:
			if 'data' in sensors[i]:
				exist2 = False
				for ii in sensors[i]['data']:
					if ii:
						exist = True
						exist2 = True
				if exist2:
					self.used.append({'app':'I2C', 'id':i, 'physical':'3'})
					self.used.append({'app':'I2C', 'id':i, 'physical':'5'})
		if exist:
			self.used.append({'app':'I2C', 'id':'power', 'physical':'1'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'6'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'9'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'14'})
			self.used.append({'app':'I2C', 'id':'power', 'physical':'17'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'20'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'25'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'30'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'34'})
			self.used.append({'app':'I2C', 'id':'ground', 'physical':'39'})
		return self.used