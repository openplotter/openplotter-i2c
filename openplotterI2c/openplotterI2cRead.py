#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-i2c>
#                       e-sailing <https://github.com/e-sailing/openplotter-i2c>
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

import time, board, json, ssl
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection
from collections import OrderedDict

def getPaths(Erg,value,value2,key,offset,factor,raw):
	if value2: Erg.append({"path":key,"value":offset+(value2*factor)})
	else: Erg.append({"path":key,"value":None})
	if raw:
		if value: Erg.append({"path":key+'.raw',"value":value})
		else: Erg.append({"path":key+'.raw',"value":None})
	return Erg

def getPaths2(Erg,ranges,value,voltage,key,offset,factor,raw):
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
		if result: Erg.append({"path":key,"value":offset+(result*factor)})
		else: Erg.append({"path":key,"value":None})
	if raw and voltage and value:
		if voltage: rawvoltage = voltage
		else: rawvoltage = None
		if value: rawvalue = value
		else: rawvalue = None
		rawresult = {"value":rawvalue,"voltage":rawvoltage}
		Erg.append({"path": key+".raw","value": rawresult}) 
	return Erg

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

def main():
	conf2 = conf.Conf()
	platform2 = platform.Platform()
	if conf2.get('GENERAL', 'debug') == 'yes': debug = True
	else: debug = False
	try: i2c_sensors=eval(conf2.get('I2C', 'sensors'))
	except: i2c_sensors=[]
	instances = []
	muxInstances = {}
	i2c = board.I2C()

	if i2c_sensors:
		#set multiplexers
		for i in i2c_sensors:
			try:
				if i2c_sensors[i]['channel'] != 0:
					if i2c_sensors[i]['address']:
						import adafruit_tca9548a
						if not i2c_sensors[i]['address'] in muxInstances:
							muxInstances[i2c_sensors[i]['address']] = adafruit_tca9548a.TCA9548A(i2c,address=int(i2c_sensors[i]['address'], 16))
			except Exception as e:
				if debug: print('Error processing Multiplexer: '+str(e))

		#set sensors
		now = time.time()
		for i in i2c_sensors:
			try:
				
				if i2c_sensors[i]['type'] == 'BME680/688':
					import adafruit_bme680
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BME680/688','tick':[now,now,now,now], 'sensor':i2c_sensors[i],'object':adafruit_bme680.Adafruit_BME680_I2C(i2c, address=int(i2c_sensors[i]['address'], 16), debug=False)})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BME680/688','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':adafruit_bme680.Adafruit_BME680_I2C(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1], debug=False)})

				elif i2c_sensors[i]['type'] == 'BME280':
					from adafruit_bme280 import basic as adafruit_bme280
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BME280','tick':[now,now,now],'sensor':i2c_sensors[i],'object':adafruit_bme280.Adafruit_BME280_I2C(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BME280','tick':[now,now,now],'sensor':i2c_sensors[i],'object':adafruit_bme280.Adafruit_BME280_I2C(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'BMP280':
					import adafruit_bmp280
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BMP280','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BMP280','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_bmp280.Adafruit_BMP280_I2C(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'BMP3XX':
					import adafruit_bmp3xx
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BMP3XX','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_bmp3xx.BMP3XX_I2C(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BMP3XX','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_bmp3xx.BMP3XX_I2C(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})
					pressure_oversampling = 8
					temperature_oversampling = 2
					if 'sensorSettings' in instances[-1]['sensor']:
						if 'pressure_oversampling' in instances[-1]['sensor']['sensorSettings']:
							try: pressure_oversampling = int(instances[-1]['sensor']['sensorSettings']['pressure_oversampling'])
							except: pass
						if 'temperature_oversampling' in instances[-1]['sensor']['sensorSettings']:
							try: temperature_oversampling = int(instances[-1]['sensor']['sensorSettings']['temperature_oversampling'])
							except: pass
					instances[-1]['object'].pressure_oversampling = pressure_oversampling
					instances[-1]['object'].temperature_oversampling = temperature_oversampling

				elif i2c_sensors[i]['type'] == 'HTU21D':
					from adafruit_htu21d import HTU21D
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'HTU21D','tick':[now,now],'sensor':i2c_sensors[i],'object':HTU21D(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'HTU21D','tick':[now,now],'sensor':i2c_sensors[i],'object':HTU21D(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'LPS3X':
					import adafruit_lps35hw
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'LPS3X','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_lps35hw.LPS35HW(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'LPS3X','tick':[now,now],'sensor':i2c_sensors[i],'object':adafruit_lps35hw.LPS35HW(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'MS5607-02BA03':
					from .ms5607 import Ms5607
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'MS5607-02BA03','tick':[now,now],'sensor':i2c_sensors[i],'object':Ms5607(i2c_sensors[i]['address'])})
					else:
						if debug: print('MS5607-02BA03 sensors can not be multiplexed')

				elif i2c_sensors[i]['type'] == 'BH1750':
					import adafruit_bh1750
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BH1750','tick':[now],'sensor':i2c_sensors[i],'object':adafruit_bh1750.BH1750(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'BH1750','tick':[now],'sensor':i2c_sensors[i],'object':adafruit_bh1750.BH1750(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'INA260':
					import adafruit_ina260
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'INA260','tick':[now,now,now],'sensor':i2c_sensors[i],'object':adafruit_ina260.INA260(i2c, address=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'INA260','tick':[now,now,now],'sensor':i2c_sensors[i],'object':adafruit_ina260.INA260(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})

				elif i2c_sensors[i]['type'] == 'INA219':
					import adafruit_ina219
					if i2c_sensors[i]['channel'] == 0:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'INA219','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':adafruit_ina219.INA219(i2c, addr=int(i2c_sensors[i]['address'], 16))})
					else:
						if i2c_sensors[i]['address']:
							instances.append({'name':i,'type':'INA219','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':adafruit_ina219.INA219(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})
					if 'sensorSettings' in instances[-1]['sensor']:
						if 'current_lsb' in instances[-1]['sensor']['sensorSettings']:
							current_lsb = float(instances[-1]['sensor']['sensorSettings']['current_lsb'])
						if 'cal_value' in instances[-1]['sensor']['sensorSettings']:
							cal_value = int(instances[-1]['sensor']['sensorSettings']['cal_value'])
						if 'power_lsb' in instances[-1]['sensor']['sensorSettings']:
							power_lsb = float(instances[-1]['sensor']['sensorSettings']['power_lsb'])

						if 'bus_voltage_range' in instances[-1]['sensor']['sensorSettings']:
							bus_voltage_range = instances[-1]['sensor']['sensorSettings']['bus_voltage_range']
						if 'gain' in instances[-1]['sensor']['sensorSettings']:
							gain = instances[-1]['sensor']['sensorSettings']['gain']
						if 'bus_adc_resolution' in instances[-1]['sensor']['sensorSettings']:
							bus_adc_resolution = instances[-1]['sensor']['sensorSettings']['bus_adc_resolution']
						if 'shunt_adc_resolution' in instances[-1]['sensor']['sensorSettings']:
							shunt_adc_resolution = instances[-1]['sensor']['sensorSettings']['shunt_adc_resolution']
						if 'mode' in instances[-1]['sensor']['sensorSettings']:
							mode = instances[-1]['sensor']['sensorSettings']['mode']
						instances[-1]['object']._current_lsb = current_lsb
						instances[-1]['object']._cal_value = cal_value
						instances[-1]['object']._power_lsb = power_lsb
						instances[-1]['object']._raw_calibration = instances[-1]['object']._cal_value
						BusVoltageRangeC = adafruit_ina219.BusVoltageRange()
						GainC = adafruit_ina219.Gain()
						ADCResolutionC = adafruit_ina219.ADCResolution()
						ModeC = adafruit_ina219.Mode()
						instances[-1]['object'].bus_voltage_range = eval('BusVoltageRangeC.'+bus_voltage_range)
						instances[-1]['object'].gain = eval('GainC.'+gain)
						instances[-1]['object'].bus_adc_resolution = eval('ADCResolutionC.'+bus_adc_resolution)
						instances[-1]['object'].shunt_adc_resolution = eval('ADCResolutionC.'+shunt_adc_resolution)
						instances[-1]['object'].mode = eval('ModeC.'+mode)


				elif i2c_sensors[i]['type'] == 'ADS1115' or i2c_sensors[i]['type'] == 'ADS1015':
					from adafruit_ads1x15.analog_in import AnalogIn
					if i2c_sensors[i]['type'] == 'ADS1115':
						import adafruit_ads1x15.ads1115 as ADS11
						if i2c_sensors[i]['channel'] == 0:
							if i2c_sensors[i]['address']:
								instances.append({'name':i,'type':'ADS1115','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':ADS11.ADS1115(i2c, address=int(i2c_sensors[i]['address'], 16))})
						else:
							if i2c_sensors[i]['address']:
								instances.append({'name':i,'type':'ADS1115','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':ADS11.ADS1115(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})
						if instances[-1]['sensor']['data'][0]['SKkey']: instances[-1]['sensor']['data'][0]['object'] = AnalogIn(instances[-1]['object'], ADS11.P0)
						if instances[-1]['sensor']['data'][1]['SKkey']: instances[-1]['sensor']['data'][1]['object'] = AnalogIn(instances[-1]['object'], ADS11.P1)
						if instances[-1]['sensor']['data'][2]['SKkey']: instances[-1]['sensor']['data'][2]['object'] = AnalogIn(instances[-1]['object'], ADS11.P2)
						if instances[-1]['sensor']['data'][3]['SKkey']: instances[-1]['sensor']['data'][3]['object'] = AnalogIn(instances[-1]['object'], ADS11.P3)

					elif i2c_sensors[i]['type'] == 'ADS1015':
						import adafruit_ads1x15.ads1015 as ADS10
						if i2c_sensors[i]['channel'] == 0:
							if i2c_sensors[i]['address']:
								instances.append({'name':i,'type':'ADS1015','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':ADS10.ADS1015(i2c, address=int(i2c_sensors[i]['address'], 16))})
						else:
							if i2c_sensors[i]['address']:
								instances.append({'name':i,'type':'ADS1015','tick':[now,now,now,now],'sensor':i2c_sensors[i],'object':ADS10.ADS1015(muxInstances[i2c_sensors[i]['address']][i2c_sensors[i]['channel']-1])})
						if instances[-1]['sensor']['data'][0]['SKkey']: instances[-1]['sensor']['data'][0]['object'] = AnalogIn(instances[-1]['object'], ADS10.P0)
						if instances[-1]['sensor']['data'][1]['SKkey']: instances[-1]['sensor']['data'][1]['object'] = AnalogIn(instances[-1]['object'], ADS10.P1)
						if instances[-1]['sensor']['data'][2]['SKkey']: instances[-1]['sensor']['data'][2]['object'] = AnalogIn(instances[-1]['object'], ADS10.P2)
						if instances[-1]['sensor']['data'][3]['SKkey']: instances[-1]['sensor']['data'][3]['object'] = AnalogIn(instances[-1]['object'], ADS10.P3)

					gain = 1
					if 'sensorSettings' in instances[-1]['sensor']:
						if 'gain' in instances[-1]['sensor']['sensorSettings']:
							try: gain = int(instances[-1]['sensor']['sensorSettings']['gain'])
							except: pass
					instances[-1]['object'].gain = gain

					for ii in range(4):
						if 'magnitudeSettings' in instances[-1]['sensor']['data'][ii]:
							instances[-1]['sensor']['data'][ii]['ranges'] = getRanges(instances[-1]['sensor']['data'][ii]['magnitudeSettings'])

			except Exception as e:
				if debug: print('Error processing '+i+': '+str(e))


		#read sensors
		if not instances:
			if debug: print('Nothing to send, closing openplotter-i2c-read')
			return
		token = conf2.get('I2C', 'token')
		ws = False
		if token:
			while True:
				time.sleep(0.1)
				if not ws:
					try:
						uri = platform2.ws+'localhost:'+platform2.skPort+'/signalk/v1/stream?subscribe=none'
						headers = {'Authorization': 'Bearer '+token}
						ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
					except Exception as e:
						if debug: print('Error connecting to Signal K server:'+str(e))
						if ws: ws.close()
						ws = False
						time.sleep(5)
				else:
					for index, i in enumerate(instances):
						Erg = []
						try:
							if i['type'] == 'BME680/688':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								humidityKey = i['sensor']['data'][2]['SKkey']
								gasKey = i['sensor']['data'][3]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										try: pressureValue = round(i['object'].pressure,2)
										except: pressureValue = i['object'].pressure
										try: pressureValue2 = float(pressureValue)*100
										except: pressureValue2 = ''
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()
								if humidityKey:
									humidityRaw = i['sensor']['data'][2]['raw']
									humidityRate = i['sensor']['data'][2]['rate']
									humidityOffset = i['sensor']['data'][2]['offset']
									humidityFactor = i['sensor']['data'][2]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][2] > humidityRate:
										try: humidityValue = round(i['object'].humidity,2)
										except: humidityValue = i['object'].humidity
										humidityValue2 = humidityValue
										Erg = getPaths(Erg,humidityValue,humidityValue2,humidityKey,humidityOffset,humidityFactor,humidityRaw)
										instances[index]['tick'][2] = time.time()
								if gasKey:
									gasRaw = i['sensor']['data'][3]['raw']
									gasRate = i['sensor']['data'][3]['rate']
									gasOffset = i['sensor']['data'][3]['offset']
									gasFactor = i['sensor']['data'][3]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][3] > gasRate:
										try: gasValue = round(i['object'].gas,2)
										except: gasValue = i['object'].gas
										gasValue2 = gasValue
										Erg = getPaths(Erg,gasValue,gasValue2,gasKey,gasOffset,gasFactor,gasRaw)
										instances[index]['tick'][3] = time.time()
							
							elif i['type'] == 'BME280':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								humidityKey = i['sensor']['data'][2]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										try: pressureValue = round(i['object'].pressure,2)
										except: pressureValue = i['object'].pressure
										try: pressureValue2 = float(pressureValue)*100
										except: pressureValue2 = ''
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()
								if humidityKey:
									humidityRaw = i['sensor']['data'][2]['raw']
									humidityRate = i['sensor']['data'][2]['rate']
									humidityOffset = i['sensor']['data'][2]['offset']
									humidityFactor = i['sensor']['data'][2]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][2] > humidityRate:
										try: humidityValue = round(i['object'].humidity,1)
										except: humidityValue = i['object'].humidity
										humidityValue2 = humidityValue
										Erg = getPaths(Erg,humidityValue,humidityValue2,humidityKey,humidityOffset,humidityFactor,humidityRaw)
										instances[index]['tick'][2] = time.time()

							elif i['type'] == 'BMP280':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										try: pressureValue = round(i['object'].pressure,2)
										except: pressureValue = i['object'].pressure
										try: pressureValue2 = float(pressureValue)*100
										except: pressureValue2 = ''
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()

							elif i['type'] == 'BMP3XX':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										try: pressureValue = round(i['object'].pressure,2)
										except: pressureValue = i['object'].pressure
										try: pressureValue2 = float(pressureValue)*100
										except: pressureValue2 = ''
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()

							elif i['type'] == 'HTU21D':
								humidityKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								if humidityKey:
									humidityRaw = i['sensor']['data'][0]['raw']
									humidityRate = i['sensor']['data'][0]['rate']
									humidityOffset = i['sensor']['data'][0]['offset']
									humidityFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > humidityRate:
										try: humidityValue = round(i['object'].relative_humidity,1)
										except: humidityValue = i['object'].relative_humidity
										humidityValue2 = humidityValue
										Erg = getPaths(Erg,humidityValue,humidityValue2,humidityKey,humidityOffset,humidityFactor,humidityRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try:temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()

							elif i['type'] == 'LPS3X':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										try: pressureValue = round(i['object'].pressure,2)
										except: pressureValue = i['object'].pressure
										try: pressureValue2 = float(pressureValue)*100
										except: pressureValue2 = ''
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].temperature,1)
										except: temperatureValue = i['object'].temperature
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()

							elif i['type'] == 'MS5607-02BA03':
								pressureKey = i['sensor']['data'][0]['SKkey']
								temperatureKey = i['sensor']['data'][1]['SKkey']
								if pressureKey:
									pressureRaw = i['sensor']['data'][0]['raw']
									pressureRate = i['sensor']['data'][0]['rate']
									pressureOffset = i['sensor']['data'][0]['offset']
									pressureFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > pressureRate:
										dig_temperature = i['object'].getDigitalTemperature()
										dig_pressure = i['object'].getDigitalPressure()
										pressure = i['object'].convertPressureTemperature(dig_pressure, dig_temperature)
										try: pressureValue = round(pressure,2)
										except: pressureValue = pressure
										pressureValue2 = pressureValue
										Erg = getPaths(Erg,pressureValue,pressureValue2,pressureKey,pressureOffset,pressureFactor,pressureRaw)
										instances[index]['tick'][0] = time.time()
								if temperatureKey:
									temperatureRaw = i['sensor']['data'][1]['raw']
									temperatureRate = i['sensor']['data'][1]['rate']
									temperatureOffset = i['sensor']['data'][1]['offset']
									temperatureFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > temperatureRate:
										try: temperatureValue = round(i['object'].getTemperature(),1)
										except: temperatureValue = i['object'].getTemperature()
										try: temperatureValue2 = float(temperatureValue)+273.15
										except: temperatureValue2 = ''
										Erg = getPaths(Erg,temperatureValue,temperatureValue2,temperatureKey,temperatureOffset,temperatureFactor,temperatureRaw)
										instances[index]['tick'][1] = time.time()

							elif i['type'] == 'BH1750':
								illuminanceKey = i['sensor']['data'][0]['SKkey']
								if illuminanceKey:
									illuminanceRaw = i['sensor']['data'][0]['raw']
									illuminanceRate = i['sensor']['data'][0]['rate']
									illuminanceOffset = i['sensor']['data'][0]['offset']
									illuminanceFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > illuminanceRate:
										try: illuminanceValue = round(i['object'].lux,2)
										except: illuminanceValue = i['object'].lux
										illuminanceValue2 = illuminanceValue
										Erg = getPaths(Erg,illuminanceValue,illuminanceValue2,illuminanceKey,illuminanceOffset,illuminanceFactor,illuminanceRaw)
										instances[index]['tick'][0] = time.time()

							elif i['type'] == 'INA260':
								voltageKey = i['sensor']['data'][0]['SKkey']
								currentKey = i['sensor']['data'][1]['SKkey']
								powerKey = i['sensor']['data'][2]['SKkey']
								if voltageKey:
									voltageRaw = i['sensor']['data'][0]['raw']
									voltageRate = i['sensor']['data'][0]['rate']
									voltageOffset = i['sensor']['data'][0]['offset']
									voltageFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > voltageRate:
										try: voltageValue = round(i['object'].voltage,2)
										except: voltageValue = i['object'].voltage
										voltageValue2 = voltageValue
										Erg = getPaths(Erg,voltageValue,voltageValue2,voltageKey,voltageOffset,voltageFactor,voltageRaw)
										instances[index]['tick'][0] = time.time()
								if currentKey:
									currentRaw = i['sensor']['data'][1]['raw']
									currentRate = i['sensor']['data'][1]['rate']
									currentOffset = i['sensor']['data'][1]['offset']
									currentFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > currentRate:
										try: currentValue = round(i['object'].current,2)
										except: currentValue = i['object'].current
										try: currentValue2 = float(currentValue)/1000
										except: currentValue2 = ''
										Erg = getPaths(Erg,currentValue,currentValue2,currentKey,currentOffset,currentFactor,currentRaw)
										instances[index]['tick'][1] = time.time()
								if powerKey:
									powerRaw = i['sensor']['data'][2]['raw']
									powerRate = i['sensor']['data'][2]['rate']
									powerOffset = i['sensor']['data'][2]['offset']
									powerFactor = i['sensor']['data'][2]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][2] > powerRate:
										try: powerValue = round(i['object'].power,2)
										except: powerValue = i['object'].power
										try: powerValue2 = float(powerValue)/1000
										except: powerValue2 = ''
										Erg = getPaths(Erg,powerValue,powerValue2,powerKey,powerOffset,powerFactor,powerRaw)
										instances[index]['tick'][2] = time.time()

							elif i['type'] == 'INA219':
								busvoltageKey = i['sensor']['data'][0]['SKkey']
								shuntvoltageKey = i['sensor']['data'][1]['SKkey']
								currentKey = i['sensor']['data'][2]['SKkey']
								powerKey = i['sensor']['data'][3]['SKkey']
								if busvoltageKey:
									busvoltageRaw = i['sensor']['data'][0]['raw']
									busvoltageRate = i['sensor']['data'][0]['rate']
									busvoltageOffset = i['sensor']['data'][0]['offset']
									busvoltageFactor = i['sensor']['data'][0]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][0] > busvoltageRate:
										try: busvoltageValue = round(i['object'].bus_voltage,2)
										except: busvoltageValue = i['object'].bus_voltage
										busvoltageValue2 = busvoltageValue
										Erg = getPaths(Erg,busvoltageValue,busvoltageValue2,busvoltageKey,busvoltageOffset,busvoltageFactor,busvoltageRaw)
										instances[index]['tick'][0] = time.time()
								if shuntvoltageKey:
									shuntvoltageRaw = i['sensor']['data'][1]['raw']
									shuntvoltageRate = i['sensor']['data'][1]['rate']
									shuntvoltageOffset = i['sensor']['data'][1]['offset']
									shuntvoltageFactor = i['sensor']['data'][1]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][1] > shuntvoltageRate:
										try: shuntvoltageValue = round(i['object'].shunt_voltage,2)
										except: shuntvoltageValue = i['object'].shunt_voltage
										shuntvoltageValue2 = shuntvoltageValue
										Erg = getPaths(Erg,shuntvoltageValue,shuntvoltageValue2,shuntvoltageKey,shuntvoltageOffset,shuntvoltageFactor,shuntvoltageRaw)
										instances[index]['tick'][1] = time.time()
								if currentKey:
									currentRaw = i['sensor']['data'][2]['raw']
									currentRate = i['sensor']['data'][2]['rate']
									currentOffset = i['sensor']['data'][2]['offset']
									currentFactor = i['sensor']['data'][2]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][2] > currentRate:
										try: currentValue = round(i['object'].current,2)
										except: currentValue = i['object'].current
										try: currentValue2 = float(currentValue)/1000
										except: currentValue2 = ''
										Erg = getPaths(Erg,currentValue,currentValue2,currentKey,currentOffset,currentFactor,currentRaw)
										instances[index]['tick'][2] = time.time()
								if powerKey:
									powerRaw = i['sensor']['data'][3]['raw']
									powerRate = i['sensor']['data'][3]['rate']
									powerOffset = i['sensor']['data'][3]['offset']
									powerFactor = i['sensor']['data'][3]['factor']
									tick0 = time.time()
									if tick0 - i['tick'][3] > powerRate:
										try: powerValue = round(i['object'].power,2)
										except: powerValue = i['object'].power
										try: powerValue2 = float(powerValue)/1000
										except: powerValue2 = ''
										Erg = getPaths(Erg,powerValue,powerValue2,powerKey,powerOffset,powerFactor,powerRaw)
										instances[index]['tick'][3] = time.time()

							elif i['type'] == 'ADS1115' or i['type'] == 'ADS1015':
								for ii in range(4):
									A0key = i['sensor']['data'][ii]['SKkey']
									if A0key:
										A0raw = i['sensor']['data'][ii]['raw']
										A0Rate = i['sensor']['data'][ii]['rate']
										A0offset = i['sensor']['data'][ii]['offset']
										A0factor = i['sensor']['data'][ii]['factor']
										A0Ranges = i['sensor']['data'][ii]['ranges']
										tick0 = time.time()
										if tick0 - i['tick'][ii] > A0Rate:
											A0value = i['sensor']['data'][ii]['object'].value
											A0voltage = i['sensor']['data'][ii]['object'].voltage
											Erg = getPaths2(Erg, A0Ranges, A0value, A0voltage, A0key, A0offset, A0factor, A0raw)
											instances[index]['tick'][ii] = time.time()

						except Exception as e:
							if debug: print('Error reading '+i['name']+': '+str(e))
						if Erg:		
							SignalK = {"updates":[{"$source":"OpenPlotter.I2C."+i['name'],"values":Erg}]}
							SignalK = json.dumps(SignalK)
							try: ws.send(SignalK+'\r\n')
							except Exception as e:
								if debug: print('Error sending data to Signal K server:'+str(e))
								if ws: ws.close()
								ws = False


if __name__ == '__main__':
	main()
	