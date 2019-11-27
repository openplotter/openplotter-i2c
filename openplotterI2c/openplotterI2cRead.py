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

import socket, time, threading
from openplotterSettings import conf
from .bme280 import Bme280
from .ms5607 import Ms5607

def work_bme280(bme280,i2c_port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	name = bme280[0]
	address = bme280[1]
	pressureSK = bme280[2][0][0]
	pressureRate = bme280[2][0][1]
	pressureOffset = bme280[2][0][2]
	temperatureSK = bme280[2][1][0]
	temperatureRate = bme280[2][1][1]
	temperatureOffset = bme280[2][1][2]
	humiditySK = bme280[2][2][0]
	humidityRate = bme280[2][2][1]
	humidityOffset = bme280[2][2][2]
	try:
		bme = Bme280(address)
		tick1 = time.time()
		tick2 = tick1
		tick3 = tick1
		while True:
			time.sleep(0.1)
			temperature,pressure,humidity = bme.readBME280All()
			tick0 = time.time()
			Erg=''
			if pressureSK:
				if tick0 - tick1 > pressureRate:
					Erg += '{"path": "'+pressureSK+'","value":'+str(pressureOffset+(pressure*100))+'},'
					tick1 = tick0
			if temperatureSK:
				if tick0 - tick2 > temperatureRate:
					Erg += '{"path": "'+temperatureSK+'","value":'+str(temperatureOffset+(temperature+273.15))+'},'
					tick2 = tick0
			if humiditySK:
				if tick0 - tick3 > humidityRate:
					Erg += '{"path": "'+humiditySK+'","value":'+str(humidityOffset+(humidity))+'},'
					tick3 = tick0
			if Erg:		
				SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
				SignalK+=Erg[0:-1]+']}]}\n'		
				sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', i2c_port))
	except Exception as e: print ("BME280 reading failed: "+str(e))

def work_MS5607(MS5607,i2c_port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	name = MS5607[0]
	address = MS5607[1]
	pressureSK = MS5607[2][0][0]
	pressureRate = MS5607[2][0][1]
	pressureOffset = MS5607[2][0][2]
	temperatureSK = MS5607[2][1][0]
	temperatureRate = MS5607[2][1][1]
	temperatureOffset = MS5607[2][1][2]
	try:
		MS = Ms5607(address)
		tick1 = time.time()
		tick2 = tick1
		while True:
			time.sleep(0.1)
			dig_temperature = MS.getDigitalTemperature()
			dig_pressure = MS.getDigitalPressure()
			pressure = MS.convertPressureTemperature(dig_pressure, dig_temperature)
			temperature = MS.getTemperature()
			tick0 = time.time()
			Erg=''
			if pressureSK:
				if tick0 - tick1 > pressureRate:
					Erg += '{"path": "'+pressureSK+'","value":'+str(pressureOffset+(pressure))+'},'
					tick1 = tick0
			if temperatureSK:
				if tick0 - tick2 > temperatureRate:
					Erg += '{"path": "'+temperatureSK+'","value":'+str(temperatureOffset+(temperature+273.15))+'},'
					tick2 = tick0
			if Erg:		
				SignalK='{"updates":[{"$source":"OPsensors.I2C.'+name+'","values":['
				SignalK+=Erg[0:-1]+']}]}\n'		
				sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', i2c_port))
	except Exception as e: print ("MS5607-02BA03 reading failed: "+str(e))

def main():
	conf2 = conf.Conf()
	active = False
	try:
		i2c_sensors=eval(conf2.get('I2C', 'sensors'))
		i2c_port = int(conf2.get('I2C', 'i2cConn1'))
	except: i2c_sensors=[]

	if i2c_sensors and i2c_port:
		for i in i2c_sensors:
			if i[0] == 'BME280':
				x = threading.Thread(target=work_bme280, args=(i,i2c_port), daemon=True)
				x.start()
				active = True
			elif i[0] == 'MS5607-02BA03':
				x = threading.Thread(target=work_MS5607, args=(i,i2c_port), daemon=True)
				x.start()
				active = True
		while active:
			time.sleep(0.1)

if __name__ == '__main__':
	main()