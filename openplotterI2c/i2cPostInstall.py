#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-i2c>

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

import os, subprocess
from openplotterSettings import conf
from openplotterSettings import language
from .version import version

def main():
	conf2 = conf.Conf()
	currentdir = os.path.dirname(os.path.abspath(__file__))
	currentLanguage = conf2.get('GENERAL', 'lang')
	language.Language(currentdir,'openplotter-i2c',currentLanguage)

	print(_('Installing python packages...'))
	try:
		subprocess.call(['pip3', 'install', 'websocket-client', 'adafruit-blinka','adafruit-circuitpython-tca9548a','adafruit-circuitpython-bme680','adafruit-circuitpython-ads1x15', 'adafruit-circuitpython-htu21d', 'adafruit-circuitpython-bmp280', 'adafruit-circuitpython-bme280', 'adafruit-circuitpython-bmp3xx', 'adafruit-circuitpython-ina260', 'adafruit-circuitpython-ina219', 'adafruit-circuitpython-lps35hw', 'adafruit-circuitpython-bh1750', '-U'])
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Checking access to Signal K server...'))
	try:
		from openplotterSignalkInstaller import connections
		skConnections = connections.Connections('I2C')
		result = skConnections.checkConnection()
		if result[1]: print(result[1])
		else: print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Setting version...'))
	try:
		conf2.set('APPS', 'i2c', version)
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))
	
if __name__ == '__main__':
	main()
