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

import subprocess, os, sys, ujson
from openplotterSettings import language
from openplotterSettings import platform

class Start():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		self.initialMessage = ''
		
	def start(self):
		green = ''
		black = ''
		red = ''

		return {'green': green,'black': black,'red': red}

class Check():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-i2c',currentLanguage)
		self.initialMessage = _('Checking I2C sensors...')


	def check(self):
		platform2 = platform.Platform()
		green = ''
		black = ''
		red = ''

		data = self.conf.get('I2C', 'sensors')
		try: i2c_sensors = eval(data)
		except: i2c_sensors = {}

		try:
			out = subprocess.check_output('ls /dev/i2c*', shell=True).decode(sys.stdin.encoding)
			if '/dev/i2c-0' in out: red = _('Your Raspberry Pi is too old.')
			if '/dev/i2c-1' in out: black = _('I2C enabled')
		except:
			if i2c_sensors: red = _('Please enable I2C interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
			else: black = _('Please enable I2C interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
				
		try:
			subprocess.check_output(['systemctl', 'is-active', 'openplotter-i2c-read.service']).decode(sys.stdin.encoding)
			green = _('running')
		except: black += _(' | not running')

		try:
			setting_file = platform2.skDir+'/settings.json'
			with open(setting_file) as data_file:
				skdata = ujson.load(data_file)
		except: skdata = {}

		for i in i2c_sensors:
			exists = False
			if 'pipedProviders' in skdata:
				for ii in skdata['pipedProviders']:
					if ii['pipeElements'][0]['options']['type']=='SignalK':
						if ii['pipeElements'][0]['options']['subOptions']['type']=='udp':
							if ii['pipeElements'][0]['options']['subOptions']['port'] == str(i2c_sensors[i]['port']): exists = True
			if not exists: 
				if not red: red = _('There is no Signal K connection for sensor: ')+ i
				else: red += '\n'+_('There is no Signal K connection for sensor: ')+ i

		return {'green': green,'black': black,'red': red}

