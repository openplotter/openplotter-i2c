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

import socket, time, threading, board, busio
from openplotterSettings import conf
from .ms5607 import Ms5607

def work_BME280(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	pressureKey = data['data'][0]['SKkey']
	temperatureKey = data['data'][1]['SKkey']
	humidityKey = data['data'][2]['SKkey']

	if pressureKey or temperatureKey or humidityKey:
		import adafruit_bme280

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=int(address, 16))

		if pressureKey: 
			pressureRaw = data['data'][0]['raw']
			pressureRate = data['data'][0]['rate']
			pressureOffset = data['data'][0]['offset']
		if temperatureKey: 
			temperatureRaw = data['data'][1]['raw']
			temperatureRate = data['data'][1]['rate']
			temperatureOffset = data['data'][1]['offset']
		if humidityKey: 
			humidityRaw = data['data'][2]['raw']
			humidityRate = data['data'][2]['rate']
			humidityOffset = data['data'][2]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		tick3 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if pressureKey:
					tick0 = time.time()
					if tick0 - tick1 > pressureRate:
						try: pressureValue = round(sensor.pressure,2)
						except: pressureValue = sensor.pressure
						try: pressureValue2 = float(pressureValue)*100
						except: pressureValue2 = ''
						Erg += getPaths(pressureValue,pressureValue2,pressureKey,pressureOffset,pressureRaw)
						tick1 = time.time()
				if temperatureKey:
					tick0 = time.time()
					if tick0 - tick2 > temperatureRate:
						try: temperatureValue = round(sensor.temperature,1)
						except: temperatureValue = sensor.temperature
						try: temperatureValue2 = float(temperatureValue)+273.15
						except: temperatureValue2 = ''
						Erg += getPaths(temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureRaw)
						tick2 = time.time()
				if humidityKey:
					tick0 = time.time()
					if tick0 - tick3 > humidityRate:
						try: humidityValue = round(sensor.humidity,1)
						except: humidityValue = sensor.humidity
						try: humidityValue2 = float(humidityValue)
						except: humidityValue2 = ''
						Erg += getPaths(humidityValue,humidityValue2,humidityKey,humidityOffset,humidityRaw)
						tick3 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("BME280 reading failed: "+str(e))

def work_MS5607(MS5607,data):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	name = MS5607
	port = data['port']
	address = data['address']
	pressureSK = data['data'][0]['SKkey']
	pressureRate = data['data'][0]['rate']
	pressureOffset = data['data'][0]['offset']
	temperatureSK = data['data'][1]['SKkey']
	temperatureRate = data['data'][1]['rate']
	temperatureOffset = data['data'][1]['offset']
	MS = None
	tick1 = time.time()
	tick2 = tick1
	while True:
		time.sleep(0.1)
		try:
			if not MS:
				MS = Ms5607(address)
			dig_temperature = MS.getDigitalTemperature()
			dig_pressure = MS.getDigitalPressure()
			pressure = MS.convertPressureTemperature(dig_pressure, dig_temperature)
			temperature = MS.getTemperature()
			tick0 = time.time()
			Erg=''
			if pressureSK and pressure:
				if tick0 - tick1 > pressureRate:
					Erg += '{"path": "'+pressureSK+'","value":'+str(pressureOffset+(pressure))+'},'
					tick1 = tick0
			if temperatureSK and temperature:
				if tick0 - tick2 > temperatureRate:
					Erg += '{"path": "'+temperatureSK+'","value":'+str(temperatureOffset+(temperature+273.15))+'},'
					tick2 = tick0
			if Erg:		
				SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
				SignalK+=Erg[0:-1]+']}]}\n'		
				sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
		except Exception as e: print ("MS5607-02BA03 reading failed: "+str(e))
			
def work_LPS3x(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	pressureKey = data['data'][0]['SKkey']
	temperatureKey = data['data'][1]['SKkey']

	if pressureKey or temperatureKey:
		import adafruit_lps35hw

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = adafruit_lps35hw.LPS35HW(i2c, address=int(address, 16))

		if pressureKey: 
			pressureRaw = data['data'][0]['raw']
			pressureRate = data['data'][0]['rate']
			pressureOffset = data['data'][0]['offset']
		if temperatureKey: 
			temperatureRaw = data['data'][1]['raw']
			temperatureRate = data['data'][1]['rate']
			temperatureOffset = data['data'][1]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		tick3 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if pressureKey:
					tick0 = time.time()
					if tick0 - tick1 > pressureRate:
						try: pressureValue = round(sensor.pressure,2)
						except: pressureValue = sensor.pressure
						try: pressureValue2 = float(pressureValue)*100
						except: pressureValue2 = ''
							Erg += getPaths(pressureValue,pressureValue2,pressureKey,pressureOffset,pressureRaw)
						tick1 = time.time()
				if temperatureKey:
					tick0 = time.time()
					if tick0 - tick2 > temperatureRate:
						try: temperatureValue = round(sensor.temperature,1)
						except: temperatureValue = sensor.temperature
							try: temperatureValue2 = float(temperatureValue)+273.15
						except: temperatureValue2 = ''
						Erg += getPaths(temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureRaw)
						tick2 = time.time()

				if Erg:
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("LPS35HW reading failed: "+str(e))


def work_ADS1115(name,data):

	def getRanges(settings):
		ranges = []
		b = OrderedDict(sorted(settings.items()))
		for i in b:
			if 'range' in i:
				c = b[i].split('->')
				if len(c) == 2:
					try:
						d = c[0].split('|')
						try:
							e = c[1].split('|')
							f = [float(e[0].lstrip()),float(e[1].lstrip())]
						except: f = c[1].lstrip()
						ranges.append([[int(d[0].lstrip()),int(d[1].lstrip())],f])
					except: pass
		return ranges

	def getPaths(ranges,value,voltage,key,offset,raw):
		Erg = ''
		if ranges:
			result = ''
			for i,v in enumerate(ranges):
				r1 = ranges[i][0]
				r2 = ranges[i][1]
				if value >= r1[0] and value <= r1[1]:
						if type(r2) == list:
							a = r1[1]-r1[0]
							b = value-r1[0]
							pc = b*100/a
							c = r2[1]-r2[0]
							d = c*pc/100
							result = r2[0]+d
						else: result = r2
			if result:
				try:
					result2 = float(result)
					Erg += '{"path": "'+key+'","value":'+str(offset+result2)+'},'
				except: Erg += '{"path": "'+key+'","value":"'+str(result)+'"},'
			else: Erg += '{"path": "'+key+'","value": null},'
		if raw and voltage and value:
			value = '{"value":'+str(value)+',"voltage":'+str(voltage)+'}'
			Erg += '{"path": "'+key+'.raw","value":'+value+'},'
		return Erg

	A0key = data['data'][0]['SKkey']
	A1key = data['data'][1]['SKkey']
	A2key = data['data'][2]['SKkey']
	A3key = data['data'][3]['SKkey']

	if A0key or A1key or A2key or A3key:
		import adafruit_ads1x15.ads1115 as ADS
		from adafruit_ads1x15.analog_in import AnalogIn
		from collections import OrderedDict

		address = data['address']
		gain = 1
		if 'sensorSettings' in data:
			if 'gain' in data['sensorSettings']:
				try: 
					gain = eval(data['sensorSettings']['gain'])
				except: pass
		i2c = busio.I2C(board.SCL, board.SDA)
		ads = ADS.ADS1115(i2c, address=int(address, 16), gain=gain)

		if A0key: 
			A0chan = AnalogIn(ads, ADS.P0)
			A0raw = data['data'][0]['raw']
			A0rate = data['data'][0]['rate']
			A0offset = data['data'][0]['offset']
			A0Ranges = []
			if 'magnitudeSettings' in data['data'][0]: 
				A0settings = data['data'][0]['magnitudeSettings']
				A0Ranges = getRanges(A0settings)
		if A1key: 
			A1chan = AnalogIn(ads, ADS.P1)
			A1raw = data['data'][1]['raw']
			A1rate = data['data'][1]['rate']
			A1offset = data['data'][1]['offset']
			A1Ranges = []
			if 'magnitudeSettings' in data['data'][1]: 
				A1settings = data['data'][1]['magnitudeSettings']
				A1Ranges = getRanges(A1settings)
		if A2key: 
			A2chan = AnalogIn(ads, ADS.P2)
			A2raw = data['data'][2]['raw']
			A2rate = data['data'][2]['rate']
			A2offset = data['data'][2]['offset']
			A2Ranges = []
			if 'magnitudeSettings' in data['data'][2]: 
				A2settings = data['data'][2]['magnitudeSettings']
				A2Ranges = getRanges(A2settings)
		if A3key: 
			A3chan = AnalogIn(ads, ADS.P3)
			A3raw = data['data'][3]['raw']
			A3rate = data['data'][3]['rate']
			A3offset = data['data'][3]['offset']
			A3Ranges = []
			if 'magnitudeSettings' in data['data'][3]: 
				A3settings = data['data'][3]['magnitudeSettings']
				A3Ranges = getRanges(A3settings)

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		tick3 = tick1
		tick4 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if A0key:
					tick0 = time.time()
					if tick0 - tick1 > A0rate:
						A0value = A0chan.value
						A0voltage = A0chan.voltage
						Erg += getPaths(A0Ranges,A0value,A0voltage,A0key,A0offset,A0raw)
						tick1 = time.time()
				if A1key:
					tick0 = time.time()
					if tick0 - tick2 > A1rate:
						A1value = A1chan.value
						A1voltage = A1chan.voltage
						Erg += getPaths(A1Ranges,A1value,A1voltage,A1key,A1offset,A1raw)
						tick2 = time.time()
				if A2key:
					tick0 = time.time()
					if tick0 - tick3 > A2rate:
						A2value = A2chan.value
						A2voltage = A2chan.voltage
						Erg += getPaths(A2Ranges,A2value,A2voltage,A2key,A2offset,A2raw)
						tick3 = time.time()
				if A3key:
					tick0 = time.time()
					if tick0 - tick4 > A3rate:
						A3value = A3chan.value
						A3voltage = A3chan.voltage
						Erg += getPaths(A3Ranges,A3value,A3voltage,A3key,A3offset,A3raw)
						tick4 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("ADS1115 reading failed: "+str(e))

def work_HTU21D(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	humidityKey = data['data'][0]['SKkey']
	temperatureKey = data['data'][1]['SKkey']

	if humidityKey or temperatureKey:
		from adafruit_htu21d import HTU21D

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = HTU21D(i2c, address=int(address, 16))

		if humidityKey: 
			humidityRaw = data['data'][0]['raw']
			humidityRate = data['data'][0]['rate']
			humidityOffset = data['data'][0]['offset']
		if temperatureKey: 
			temperatureRaw = data['data'][1]['raw']
			temperatureRate = data['data'][1]['rate']
			temperatureOffset = data['data'][1]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if humidityKey:
					tick0 = time.time()
					if tick0 - tick1 > humidityRate:
						try: humidityValue = round(sensor.relative_humidity,1)
						except: humidityValue = sensor.relative_humidity
						humidityValue2 = humidityValue
						Erg += getPaths(humidityValue,humidityValue2,humidityKey,humidityOffset,humidityRaw)
						tick1 = time.time()
				if temperatureKey:
					tick0 = time.time()
					if tick0 - tick2 > temperatureRate:
						try: temperatureValue = round(sensor.temperature,1)
						except: temperatureValue = sensor.temperature
						try:temperatureValue2 = float(temperatureValue)+273.15
						except: temperatureValue2 = ''
						Erg += getPaths(temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureRaw)
						tick2 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("HTU21D reading failed: "+str(e))

def work_BMP280(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	pressureKey = data['data'][0]['SKkey']
	temperatureKey = data['data'][1]['SKkey']

	if pressureKey or temperatureKey:
		import adafruit_bmp280

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=int(address, 16))

		if pressureKey: 
			pressureRaw = data['data'][0]['raw']
			pressureRate = data['data'][0]['rate']
			pressureOffset = data['data'][0]['offset']
		if temperatureKey: 
			temperatureRaw = data['data'][1]['raw']
			temperatureRate = data['data'][1]['rate']
			temperatureOffset = data['data'][1]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if pressureKey:
					tick0 = time.time()
					if tick0 - tick1 > pressureRate:
						try: pressureValue = round(sensor.pressure,2)
						except: pressureValue = sensor.pressure
						try: pressureValue2 = float(pressureValue)*100
						except: pressureValue2 = ''
						Erg += getPaths(pressureValue,pressureValue2,pressureKey,pressureOffset,pressureRaw)
						tick1 = time.time()
				if temperatureKey:
					tick0 = time.time()
					if tick0 - tick2 > temperatureRate:
						try: temperatureValue = round(sensor.temperature,1)
						except: temperatureValue = sensor.temperature
						try: temperatureValue2 = float(temperatureValue)+273.15
						except: temperatureValue2 = ''
						Erg += getPaths(temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureRaw)
						tick2 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("BMP280 reading failed: "+str(e))

def work_BMP3XX(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	pressureKey = data['data'][0]['SKkey']
	temperatureKey = data['data'][1]['SKkey']

	if pressureKey or temperatureKey:
		import adafruit_bmp3xx

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = adafruit_bmp3xx.BMP3XX_I2C(i2c, address=int(address, 16))

		pressure_oversampling = 8
		if 'sensorSettings' in data:
			if 'pressure_oversampling' in data['sensorSettings']:
				try: 
					pressure_oversampling = int(data['sensorSettings']['pressure_oversampling'])
				except: pass
		temperature_oversampling = 2
		if 'sensorSettings' in data:
			if 'temperature_oversampling' in data['sensorSettings']:
				try: 
					temperature_oversampling = int(data['sensorSettings']['temperature_oversampling'])
				except: pass
		sensor.pressure_oversampling = pressure_oversampling
		sensor.temperature_oversampling = temperature_oversampling

		if pressureKey: 
			pressureRaw = data['data'][0]['raw']
			pressureRate = data['data'][0]['rate']
			pressureOffset = data['data'][0]['offset']
		if temperatureKey: 
			temperatureRaw = data['data'][1]['raw']
			temperatureRate = data['data'][1]['rate']
			temperatureOffset = data['data'][1]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if pressureKey:
					tick0 = time.time()
					if tick0 - tick1 > pressureRate:
						try: pressureValue = round(sensor.pressure,2)
						except: pressureValue = sensor.pressure
						try: pressureValue2 = float(pressureValue)*100
						except: pressureValue2 = ''
						Erg += getPaths(pressureValue,pressureValue2,pressureKey,pressureOffset,pressureRaw)
						tick1 = time.time()
				if temperatureKey:
					tick0 = time.time()
					if tick0 - tick2 > temperatureRate:
						try: temperatureValue = round(sensor.temperature,1)
						except: temperatureValue = sensor.temperature
						try: temperatureValue2 = float(temperatureValue)+273.15
						except: temperatureValue2 = ''
						Erg += getPaths(temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureRaw)
						tick2 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("BMP3XX reading failed: "+str(e))

def work_INA260(name,data):

	def getPaths(value,value2,key,offset,raw):
		Erg = ''
		if value2:
			try:
				value3 = float(value2)
				Erg += '{"path": "'+key+'","value":'+str(offset+value3)+'},'
			except: Erg += '{"path": "'+key+'","value":"'+str(value2)+'"},'
		else: Erg += '{"path": "'+key+'","value": null},'
		if raw and value:
			try:
				value4 = float(value)
				Erg += '{"path": "'+key+'.raw","value":'+str(value4)+'},'
			except: Erg += '{"path": "'+key+'.raw","value":"'+str(value)+'"},'
		return Erg

	voltageKey = data['data'][0]['SKkey']
	currentKey = data['data'][1]['SKkey']
	powerKey = data['data'][2]['SKkey']

	if voltageKey or currentKey or powerKey:
		import adafruit_ina260

		address = data['address']
		i2c = busio.I2C(board.SCL, board.SDA)
		sensor = aadafruit_ina260.INA260(i2c, address=int(address, 16))

		if voltageKey: 
			voltageRaw = data['data'][0]['raw']
			voltageRate = data['data'][0]['rate']
			voltageOffset = data['data'][0]['offset']
		if currentKey: 
			currentRaw = data['data'][1]['raw']
			currentRate = data['data'][1]['rate']
			currentOffset = data['data'][1]['offset']
		if powerKey: 
			powerRaw = data['data'][2]['raw']
			powerRate = data['data'][2]['rate']
			powerOffset = data['data'][2]['offset']

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		port = data['port']
		tick1 = time.time()
		tick2 = tick1
		tick3 = tick1
		while True:
			time.sleep(0.1)
			try:
				Erg=''
				if voltageKey:
					tick0 = time.time()
					if tick0 - tick1 > voltageRate:
						try: voltageValue = round(sensor.voltage,4)
						except: voltageValue = sensor.voltage
						try: voltageValue2 = float(voltageValue)
						except: voltageValue2 = ''
						Erg += getPaths(voltageValue,voltageValue2,voltageKey,voltageOffset,voltageRaw)
						tick1 = time.time()
				if currentKey:
					tick0 = time.time()
					if tick0 - tick2 > currentRate:
						try: currentValue = round(sensor.current,2)
						except: currentValue = sensor.current
						try: currentValue2 = float(currentValue)/1000
						except: currentValue2 = ''
						Erg += getPaths(currentValue,currentValue2,currentKey,currentOffset,currentRaw)
						tick2 = time.time()
				if powerKey:
					tick0 = time.time()
					if tick0 - tick3 > powerRate:
						try: powerValue = round(sensor.power,2)
						except: powerValue = sensor.power
						try: powerValue2 = float(powerValue)/1000
						except: powerValue2 = ''
						Erg += getPaths(powerValue,powerValue2,powerKey,powerOffset,powerRaw)
						tick3 = time.time()
				if Erg:		
					SignalK='{"updates":[{"$source":"OpenPlotter.I2C.'+name+'","values":['
					SignalK+=Erg[0:-1]+']}]}\n'		
					sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))
			except Exception as e: print ("INA260 reading failed: "+str(e))

def main():
	conf2 = conf.Conf()
	active = False
	try: i2c_sensors=eval(conf2.get('I2C', 'sensors'))
	except: i2c_sensors=[]

	if i2c_sensors:
		for i in i2c_sensors:
			if 'BME280' in i:
				x1 = threading.Thread(target=work_BME280, args=(i,i2c_sensors[i]), daemon=True)
				x1.start()
				active = True
			elif 'MS5607-02BA03' in i:
				x2 = threading.Thread(target=work_MS5607, args=(i,i2c_sensors[i]), daemon=True)
				x2.start()
				active = True
			elif 'ADS1115' in i:
				x3 = threading.Thread(target=work_ADS1115, args=(i,i2c_sensors[i]), daemon=True)
				x3.start()
				active = True
			elif 'HTU21D' in i:
				x4 = threading.Thread(target=work_HTU21D, args=(i,i2c_sensors[i]), daemon=True)
				x4.start()
				active = True
			elif 'BMP280' in i:
				x5 = threading.Thread(target=work_BMP280, args=(i,i2c_sensors[i]), daemon=True)
				x5.start()
				active = True
			elif 'BMP3XX' in i:
				x6 = threading.Thread(target=work_BMP3XX, args=(i,i2c_sensors[i]), daemon=True)
				x6.start()
				active = True
			elif 'INA260' in i:
				x7 = threading.Thread(target=work_INA260, args=(i,i2c_sensors[i]), daemon=True)
				x7.start()
				active = True
			elif 'LPS3X' in i:
				x8 = threading.Thread(target=work_LPS3x, args=(i,i2c_sensors[i]), daemon=True)
				X8.start()
				active = True
		while active:
			time.sleep(0.1)

if __name__ == '__main__':
	main()
