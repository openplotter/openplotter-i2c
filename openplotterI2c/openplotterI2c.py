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

import wx, os, webbrowser, subprocess, time, smbus, sys, ujson
import wx.richtext as rt

from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import ports
from openplotterSettings import platform
from openplotterSettings import selectKey
from openplotterSettings import selectConnections
from .startup import Check
from .version import version

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-i2c',self.currentLanguage)

		self.i2c_sensors_def = {}
		self.i2c_sensors_def['ADS1115'] = {'magnitudes': ['A0','A1','A2','A3'], 'SKkeys': ['','','',''],'sensorSettings':{'gain':'1'}, 'magnitudeSettings':{'range1':'0|26400 -> 0|16'}}
		self.i2c_sensors_def['BME280'] = {'magnitudes': [_('pressure'),_('temperature'),_('humidity')], 'SKkeys': ['environment.outside.pressure','','environment.inside.relativeHumidity']}
		self.i2c_sensors_def['BMP280'] = {'magnitudes': [_('pressure'),_('temperature')], 'SKkeys': ['environment.outside.pressure','']}
		self.i2c_sensors_def['LPS3X'] = {'magnitudes': [_('pressure'),_('temperature')], 'SKkeys': ['environment.outside.pressure','']}
		self.i2c_sensors_def['BMP3XX'] = {'magnitudes': [_('pressure'),_('temperature')], 'SKkeys': ['environment.outside.pressure',''], 'sensorSettings': {'pressure_oversampling':'8', 'temperature_oversampling':'2'}}
		self.i2c_sensors_def['HTU21D'] = {'magnitudes': [_('humidity'),_('temperature')], 'SKkeys': ['environment.inside.relativeHumidity','']}
		self.i2c_sensors_def['MS5607-02BA03'] = {'magnitudes': [_('pressure'),_('temperature')], 'SKkeys': ['environment.outside.pressure','']}
		self.i2c_sensors_def['INA260'] = {'magnitudes': [_('voltage'),_('current'),_('power')], 'SKkeys': ['','','']}
		
		wx.Frame.__init__(self, None, title='I2C '+version, size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-i2c.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)
		
		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		toolAddresses = self.toolbar1.AddTool(103, _('I2C Addresses'), wx.Bitmap(self.currentdir+"/data/check.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolAddresses, toolAddresses)
		self.toolbar1.AddSeparator()
		self.refreshButton = self.toolbar1.AddTool(104, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.OnRefreshButton, self.refreshButton)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.i2c = wx.Panel(self.notebook)
		self.connections = wx.Panel(self.notebook)
		self.output = wx.Panel(self.notebook)
		self.notebook.AddPage(self.i2c, _('Sensors'))
		self.notebook.AddPage(self.connections, _('Connections'))
		self.notebook.AddPage(self.output, '')
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/i2c.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/connections.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/output.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageI2c()
		self.pageConnections()
		self.pageOutput()
		self.checkInterface()
		self.readSensors()
		
		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()
		
		self.Centre()

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0))

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:pass

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/i2c/i2c_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def OnRefreshButton(self, e):
		self.readSensors()

	def pageOutput(self):
		self.logger = rt.RichTextCtrl(self.output, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		self.logger.SetMargins((10,10))
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.logger, 1, wx.EXPAND, 0)
		self.output.SetSizer(sizer)

	def OnToolAddresses(self,e):
		addresses = ''
		try:
			addresses = subprocess.check_output(['i2cdetect', '-y', '0']).decode(sys.stdin.encoding)
		except:
			try:
				addresses = subprocess.check_output(['i2cdetect', '-y', '1']).decode(sys.stdin.encoding)
			except: pass
		self.logger.Clear()
		self.notebook.ChangeSelection(2)
		if addresses:
			self.logger.BeginTextColour((55, 55, 55))
			self.logger.WriteText(addresses)
		else:
			self.logger.BeginTextColour((130, 0, 0))
			self.logger.WriteText(_('Failed'))
		self.checkInterface()

	def checkInterface(self):
		cheking = Check(self.conf,self.currentLanguage )
		result = cheking.check()
		if result['red']: self.ShowStatusBarRED(result['red'])
		elif result['black']: self.ShowStatusBarBLACK(result['black'])

	def pageI2c(self):
		self.listSensors = wx.ListCtrl(self.i2c, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listSensors.InsertColumn(0, ' ', width=16)
		self.listSensors.InsertColumn(1, _('Name'), width=120)
		self.listSensors.InsertColumn(2, _('Address'), width=60)
		self.listSensors.InsertColumn(3, _('Magnitude'), width=90)
		self.listSensors.InsertColumn(4, _('Signal K key'), width=220)
		self.listSensors.InsertColumn(5, _('Rate'), width=40)
		self.listSensors.InsertColumn(6, _('Offset'), width=50)
		self.listSensors.InsertColumn(7, _('Raw'), width=40)
		self.listSensors.InsertColumn(8, _('Sensor Settings'), width=200)
		self.listSensors.InsertColumn(9, _('Magnitude Settings'), width=200)
		self.listSensors.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListSensorsSelected)
		self.listSensors.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListSensorsDeselected)
		self.listSensors.SetTextColour(wx.BLACK)

		self.toolbar2 = wx.ToolBar(self.i2c, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addButton = self.toolbar2.AddTool(201, _('Add'), wx.Bitmap(self.currentdir+"/data/i2c.png"))
		self.Bind(wx.EVT_TOOL, self.OnAddButton, self.addButton)
		self.removeButton = self.toolbar2.AddTool(203, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.OnRemoveButton, self.removeButton)
		self.toolbar2.AddSeparator()
		self.editButton = self.toolbar2.AddTool(202, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditButton, self.editButton)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listSensors, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar2, 0)
		self.i2c.SetSizer(sizer)

	def readSensors(self):
		self.listSensors.DeleteAllItems()
		self.listConnections.DeleteAllItems()
		self.onListSensorsDeselected()
		self.onlistConnectionsDeselected()

		data = self.conf.get('I2C', 'sensors')
		try: self.i2c_sensors = eval(data)
		except: self.i2c_sensors = {}

		for name in self.i2c_sensors:
			if name in self.i2c_sensors_def: sensor = name
			else:
				x = name.split('-')
				sensor = x[0]
			address = self.i2c_sensors[name]['address']
			port = self.i2c_sensors[name]['port']
			magnitudes = []
			
			for i in self.i2c_sensors_def:
				if sensor in i: magnitudes = self.i2c_sensors_def[i]['magnitudes']
			c = 0
			for index, magnitude in enumerate(magnitudes):
				nameMagnitude = magnitude
				SKkey = self.i2c_sensors[name]['data'][index]['SKkey']
				rate = self.i2c_sensors[name]['data'][index]['rate']
				offset = self.i2c_sensors[name]['data'][index]['offset']
				if 'raw' in self.i2c_sensors[name]['data'][index]: raw = self.i2c_sensors[name]['data'][index]['raw']
				else: raw = False
				if raw: raw2 = _('yes')
				else: raw2 = _('no')
				if 'sensorSettings' in self.i2c_sensors[name]: sensorSettings = self.i2c_sensors[name]['sensorSettings']
				else: sensorSettings = ''
				if 'magnitudeSettings' in self.i2c_sensors[name]['data'][index]: magnitudeSettings = self.i2c_sensors[name]['data'][index]['magnitudeSettings']
				else: magnitudeSettings = ''
				self.listSensors.Append([str(c),name, address, nameMagnitude, SKkey, str(rate), str(offset), raw2, sensorSettings, magnitudeSettings])
				c = c + 1
				if SKkey: self.listSensors.SetItemBackgroundColour(self.listSensors.GetItemCount()-1,(255,215,0))
			self.listConnections.Append([name, str(port), ''])

		sklist = []
		if self.platform.skDir:
			from openplotterSignalkInstaller import editSettings
			skSettings = editSettings.EditSettings()
			if 'pipedProviders' in skSettings.data:
				for i in skSettings.data['pipedProviders']:
					try:
						if i['pipeElements'][0]['options']['type']=='SignalK':
							if i['pipeElements'][0]['options']['subOptions']['type']=='udp':
								sklist.append([i['id'],i['enabled'],i['pipeElements'][0]['options']['subOptions']['port']])
					except Exception as e: print(str(e))
		for i in sklist:
			exists = False
			for ii in range(self.listConnections.GetItemCount()):
				if i[2] == self.listConnections.GetItemText(ii, 1):
					exists = True
					self.listConnections.SetItem(ii, 2, i[0])
			if not exists: self.listConnections.Append(['', i[2], i[0]])

		for i in range(self.listConnections.GetItemCount()):
			if self.listConnections.GetItemText(i, 0) and self.listConnections.GetItemText(i, 1) and self.listConnections.GetItemText(i, 2):
				for ii in sklist:
					if self.listConnections.GetItemText(i, 2) == ii[0] and ii[1]:
						self.listConnections.SetItemBackgroundColour(i,(255,215,0))

	def OnAddButton(self,e):
		try:
			dlg = addI2c(self.i2c_sensors_def)
		except:
			self.checkInterface()
			return
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			sensor = str(dlg.sensorSelect.GetValue())
			if not sensor:
				self.ShowStatusBarRED(_('Failed. You must select a sensor.'))
				dlg.Destroy()
				return
			address = dlg.addressSelect.GetValue()
			if not address:
				self.ShowStatusBarRED(_('Failed. You must provide an address.'))
				dlg.Destroy()
				return
			for i in self.i2c_sensors:
				if address == self.i2c_sensors[i]['address']:
					self.ShowStatusBarRED(_('Failed. This address is already being used.'))
					dlg.Destroy()
					return
			sensorSettings = dlg.settings.GetValue()
			sensorSettings2 = {}
			if sensorSettings:
				x0 = sensorSettings.split('\n')
				for i in x0:
					try:
						x1 = i.split('=')
						x2 = x1[0].replace(' ','')
						x3 = x1[1].replace(' ','')
						sensorSettings2[x2] = x3
					except: pass
			name = sensor
			if name in self.i2c_sensors:
				c = 1
				name = sensor+'-'+str(c)
				while True:
					if name in self.i2c_sensors:
						name = sensor+'-'+str(c)
						c = c + 1
					else: break
			magnitudeSettings = ''
			if 'magnitudeSettings' in self.i2c_sensors_def[sensor]: magnitudeSettings = self.i2c_sensors_def[sensor]['magnitudeSettings']
			data = []
			for SKkey in self.i2c_sensors_def[sensor]['SKkeys']:
				data.append({'SKkey': SKkey, 'rate': 1.0, 'offset': 0.0, 'raw': False, 'magnitudeSettings':magnitudeSettings})
			new_sensor = {'address': address, 'port': 51000, 'sensorSettings':sensorSettings2, 'data': data}
			self.i2c_sensors[name] = new_sensor
			self.OnApply()
			self.readSensors()
		dlg.Destroy()

	def OnEditButton(self,e):
		selected = self.listSensors.GetFirstSelected()
		if selected == -1: return
		name = self.listSensors.GetItem(selected, 1)
		name = name.GetText()
		index = self.listSensors.GetItem(selected, 0)
		index = index.GetText()
		magn = self.listSensors.GetItem(selected, 3)
		magn = magn.GetText()
		sk = self.listSensors.GetItem(selected, 4)
		sk = sk.GetText()
		rate = self.listSensors.GetItem(selected, 5)
		rate = rate.GetText()
		offset = self.listSensors.GetItem(selected, 6)
		offset = offset.GetText()
		raw = False
		if 'raw' in self.i2c_sensors[name]['data'][int(index)]:
			raw = self.i2c_sensors[name]['data'][int(index)]['raw']
		magnitudeSettings = ''
		if 'magnitudeSettings' in self.i2c_sensors[name]['data'][int(index)]:
			magnitudeSettings = self.i2c_sensors[name]['data'][int(index)]['magnitudeSettings']
		dlg = editI2c(name,magn,sk,rate,offset,raw,magnitudeSettings)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			sk = str(dlg.SKkey.GetValue())
			rate = dlg.rate.GetValue()
			if not rate: rate = 1.0
			offset = dlg.offset.GetValue()
			if not offset: offset = 0.0
			raw = dlg.raw.GetValue()
			magnitudeSettings = dlg.settings.GetValue()
			magnitudeSettings2 = {}
			if magnitudeSettings:
				x0 = magnitudeSettings.split('\n')
				for i in x0:
					try:
						x1 = i.split('=')
						x2 = x1[0].replace(' ','')
						x3 = x1[1].lstrip()
						magnitudeSettings2[x2] = x3
					except: pass
			self.i2c_sensors[name]['data'][int(index)] = {'SKkey': sk, 'rate': float(rate), 'offset': float(offset), 'raw': raw, 'magnitudeSettings': magnitudeSettings2}
			self.OnApply()
			self.readSensors()
		dlg.Destroy()

	def OnRemoveButton(self,e):
		selected = self.listSensors.GetFirstSelected()
		if selected == -1: return
		name = self.listSensors.GetItem(selected, 1)
		name = name.GetText()
		del self.i2c_sensors[name]
		self.OnApply()
		self.readSensors()

	def OnApply(self):
		self.conf.set('I2C', 'sensors', str(self.i2c_sensors))
		try:
			i2c_sensors = eval(self.conf.get('I2C', 'sensors'))
		except: i2c_sensors = []
		if i2c_sensors:
			subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'enable'])
			self.ShowStatusBarGREEN(_('I2C service is enabled'))
		else:
			subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'disable'])
			self.ShowStatusBarYELLOW(_('There is nothing to send. I2C service is disabled'))

	def onListSensorsSelected(self,e):
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		self.toolbar2.EnableTool(202,True)
		self.toolbar2.EnableTool(203,True)

	def onListSensorsDeselected(self,e=0):
		self.toolbar2.EnableTool(201,True)
		self.toolbar2.EnableTool(202,False)
		self.toolbar2.EnableTool(203,False)

	###########################################################################

	def pageConnections(self):
		self.listConnections = wx.ListCtrl(self.connections, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listConnections.InsertColumn(0, _('Sensor'), width=220)
		self.listConnections.InsertColumn(1, _('Port'), width=100)
		self.listConnections.InsertColumn(2, _('SK connection ID'), width=240)
		self.listConnections.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onlistConnectionsSelected)
		self.listConnections.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onlistConnectionsDeselected)
		self.listConnections.SetTextColour(wx.BLACK)

		self.toolbar4 = wx.ToolBar(self.connections, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.editConnButton = self.toolbar4.AddTool(402, _('Edit Port'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditConnButton, self.editConnButton)
		self.toolbar4.AddSeparator()
		skConnections = self.toolbar4.AddTool(403, _('Add Connection'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.OnSkConnections, skConnections)
		self.editSKButton = self.toolbar4.AddTool(401, _('Edit connection'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditSKButton, self.editSKButton)
		self.removeConnButton = self.toolbar4.AddTool(404, _('Remove connection'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.OnRemoveConnButton, self.removeConnButton)

		vbox = wx.BoxSizer(wx.HORIZONTAL)
		vbox.Add(self.listConnections, 1, wx.EXPAND, 0)
		vbox.Add(self.toolbar4, 0, wx.EXPAND, 0)

		self.connections.SetSizer(vbox)

	def onlistConnectionsSelected(self,e):
		i = e.GetIndex()
		valid = e and i >= 0
		self.onlistConnectionsDeselected()
		if not valid: return
		sensor = self.listConnections.GetItemText(i, 0)
		port = self.listConnections.GetItemText(i, 1)
		connection = self.listConnections.GetItemText(i, 2)
		if connection:
			self.toolbar4.EnableTool(401,True)
			self.toolbar4.EnableTool(404,True)
		else: self.toolbar4.EnableTool(403,True)
		if port and sensor: self.toolbar4.EnableTool(402,True)

	def onlistConnectionsDeselected(self,e=0):
		self.toolbar4.EnableTool(401,False)
		self.toolbar4.EnableTool(402,False)
		self.toolbar4.EnableTool(403,False)
		self.toolbar4.EnableTool(404,False)

	def OnEditConnButton(self,e):
		selected = self.listConnections.GetFirstSelected()
		if selected == -1: return
		sensor = self.listConnections.GetItemText(selected, 0)
		port = self.listConnections.GetItemText(selected, 1)
		dlg = editPort(port)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			if sensor in self.i2c_sensors:
				port2 = dlg.port.GetValue()
				if not port2: port2 = 51000
				self.i2c_sensors[sensor]['port'] = port2
				self.OnApply()
				self.readSensors()
		dlg.Destroy()

	def OnSkConnections(self,e):
		if self.platform.skPort:
			selected = self.listConnections.GetFirstSelected()
			if selected == -1: return
			port = self.listConnections.GetItemText(selected, 1)
			from openplotterSignalkInstaller import editSettings
			skSettings = editSettings.EditSettings()
			ID = 'I2C'
			c = 0
			while True:
				if skSettings.connectionIdExists(ID):
					ID = ID+str(c)
					c = c + 1
				else: break
			if skSettings.setNetworkConnection(ID,'SignalK','UDP','localhost',port):
				self.restart_SK(0)
				self.readSensors()
			else: self.ShowStatusBarRED(_('Failed. Error creating connection in Signal K'))
		else: 
			self.ShowStatusBarRED(_('Please install "Signal K Installer" OpenPlotter app'))
			self.OnToolSettings()

	def OnEditSKButton(self,e):
		selected = self.listConnections.GetFirstSelected()
		if selected == -1: return
		skId = self.listConnections.GetItemText(selected, 2)
		url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/connections/'+skId
		webbrowser.open(url, new=2)

	def OnRemoveConnButton(self,e):
		selected = self.listConnections.GetFirstSelected()
		if selected == -1: return
		skId = self.listConnections.GetItemText(selected, 2)
		from openplotterSignalkInstaller import editSettings
		skSettings = editSettings.EditSettings()
		if skSettings.removeConnection(skId): 
			self.restart_SK(0)
			self.readSensors()
		else: self.ShowStatusBarRED(_('Failed. Error removing connection in Signal K'))

	def restart_SK(self, msg):
		if msg == 0: msg = _('Restarting Signal K server... ')
		seconds = 12
		subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'restart'])
		for i in range(seconds, 0, -1):
			self.ShowStatusBarYELLOW(msg+str(i))
			time.sleep(1)
		self.ShowStatusBarGREEN(_('Signal K server restarted'))

################################################################################

class addI2c(wx.Dialog):
	def __init__(self, i2c_sensors_def):

		self.i2c_sensors_def = i2c_sensors_def
		title = _('Add I2C sensor')

		wx.Dialog.__init__(self, None, title=title, size=(610,360))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		sensorLabel = wx.StaticText(panel, label=_('Supported sensors'))
		listSensors = []
		for i in self.i2c_sensors_def:
			listSensors.append(i)
		self.sensorSelect = wx.ComboBox(panel, choices=listSensors, style=wx.CB_READONLY)
		self.sensorSelect.Bind(wx.EVT_COMBOBOX, self.onSelectSensor)

		settingsLabel = wx.StaticText(panel, label=_('Settings'))
		self.settings = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.HSCROLL)

		addressesLabel = wx.StaticText(panel, label=_('Detected addresses'))
		listAddresses = []
		bus = smbus.SMBus(1)
		for addr in range(3, 178):
			try:
				bus.write_quick(addr)
				addr = hex(addr)
				listAddresses.append(addr)
			except IOError: pass
		self.addressSelect = wx.ComboBox(panel, choices=listAddresses, style=wx.CB_READONLY)

		detectedI2c = rt.RichTextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		detectedI2c.SetMargins((10,10))
		try:
			addresses = subprocess.check_output(['i2cdetect', '-y', '0']).decode(sys.stdin.encoding)
		except: addresses = subprocess.check_output(['i2cdetect', '-y', '1']).decode(sys.stdin.encoding)

		detectedI2c.WriteText(addresses)

		hline1 = wx.StaticLine(panel)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		vbox1 = wx.BoxSizer(wx.VERTICAL)
		vbox1.Add(sensorLabel, 0, wx.ALL | wx.EXPAND, 5)
		vbox1.Add(self.sensorSelect, 0, wx.ALL | wx.EXPAND, 5)
		vbox1.Add(settingsLabel, 0, wx.ALL | wx.EXPAND, 5)
		vbox1.Add(self.settings, 1, wx.ALL | wx.EXPAND, 5)

		vbox2 = wx.BoxSizer(wx.VERTICAL)
		vbox2.Add(addressesLabel, 0, wx.ALL | wx.EXPAND, 5)
		vbox2.Add(self.addressSelect, 0, wx.ALL | wx.EXPAND, 5)
		vbox2.Add(detectedI2c, 1, wx.ALL | wx.EXPAND, 5)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(vbox1, 1, wx.EXPAND, 0)
		hbox1.Add(vbox2, 1, wx.EXPAND, 0)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.ALL | wx.EXPAND, 5)
		hbox.Add(okBtn, 0, wx.ALL | wx.EXPAND, 5)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbox1, 1, wx.EXPAND, 0)
		vbox.AddSpacer(5)
		vbox.Add(hline1, 0, wx.EXPAND, 0)
		vbox.Add(hbox, 0, wx.ALL  | wx.EXPAND, 5)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onSelectSensor(self,e):
		if 'sensorSettings' in self.i2c_sensors_def[self.sensorSelect.GetValue()]:
			sensorSettings = self.i2c_sensors_def[self.sensorSelect.GetValue()]['sensorSettings']
			if sensorSettings:
				settings2 = ''
				for i in sensorSettings:
					settings2 += i+' = '+str(sensorSettings[i])+'\n'
				self.settings.SetValue(settings2)
			else: self.settings.SetValue('')
		else: self.settings.SetValue('')

################################################################################

class editI2c(wx.Dialog):
	def __init__(self,name,magn,sk,rate,offset,raw,magnitudeSettings):
		self.platform = platform.Platform()
		title = _('Edit')+(' '+name+' - '+magn)

		wx.Dialog.__init__(self, None, title=title, size=(500, 350))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		titl = wx.StaticText(panel, label=_('Signal K key'))
		self.SKkey = wx.TextCtrl(panel)
		self.SKkey.SetValue(sk)

		self.edit_skkey = wx.Button(panel, label=_('Edit'))
		self.edit_skkey.Bind(wx.EVT_BUTTON, self.onEditSkkey)

		if not self.platform.skDir:
			self.SKkey.Disable()
			self.edit_skkey.Disable()

		self.raw = wx.CheckBox(panel, label=_('Add raw values'))
		if raw: self.raw.SetValue(True)

		self.rate_list = ['0.1', '0.25', '0.5', '0.75', '1.0', '5.0', '30.0', '60.0', '300.0']
		self.rate_label = wx.StaticText(panel, label=_('Rate (seconds)'))
		self.rate = wx.ComboBox(panel, choices=self.rate_list, style=wx.CB_READONLY)
		self.rate.SetValue(rate)

		self.offset_label = wx.StaticText(panel, label=_('Offset'))
		self.offset = wx.TextCtrl(panel)
		self.offset.SetValue(offset)

		self.settingsLabel = wx.StaticText(panel, label=_('Settings'))
		self.settings = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.HSCROLL)
		if magnitudeSettings:
			settings2 = ''
			for i in magnitudeSettings:
				settings2 += i+' = '+str(magnitudeSettings[i])+'\n'
			self.settings.SetValue(settings2)
		else: self.settings.SetValue('')
		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(self.SKkey, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		hbox2.Add(self.edit_skkey, 0, wx.RIGHT | wx.EXPAND, 5)

		vbox1 = wx.BoxSizer(wx.VERTICAL)
		vbox1.Add(self.rate_label, 0, wx.ALL | wx.EXPAND, 5)
		vbox1.Add(self.rate, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox1.AddSpacer(10)
		vbox1.Add(self.offset_label, 0, wx.ALL| wx.EXPAND, 5)
		vbox1.Add(self.offset, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)

		vbox2 = wx.BoxSizer(wx.VERTICAL)
		vbox2.Add(self.settingsLabel, 0, wx.ALL | wx.EXPAND, 5)
		vbox2.Add(self.settings, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)	

		hbox5 = wx.BoxSizer(wx.HORIZONTAL)
		hbox5.Add(vbox1, 0, wx.EXPAND, 0)
		hbox5.AddSpacer(5)
		hbox5.Add(vbox2, 1, wx.EXPAND, 0)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.EXPAND, 0)
		hbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(titl, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.AddSpacer(5)
		vbox.Add(hbox2, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(5)
		vbox.Add(self.raw, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(hbox5, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(5)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onEditSkkey(self,e):
		dlg = selectKey.SelectKey(self.SKkey.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.SKkey.SetValue(key)
		dlg.Destroy()

################################################################################

class editPort(wx.Dialog):
	def __init__(self, port):
		wx.Dialog.__init__(self, None, title=_('Port'), size=(200,150))
		panel = wx.Panel(self)
		self.port = wx.SpinCtrl(panel, 101, min=4000, max=65536, initial=51000)
		self.port.SetValue(int(port))

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(cancelBtn, 1, wx.ALL | wx.EXPAND, 10)
		hbox.Add(okBtn, 1, wx.ALL | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.port, 1, wx.ALL | wx.EXPAND, 10)
		vbox.Add(hbox, 0, wx.EXPAND, 0)

		panel.SetSizer(vbox)
		self.Centre() 

################################################################################

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'i2c'):
			subprocess.Popen(['openplotterPostInstall', platform2.admin+' i2cPostInstall'])
			return
	except: pass

	app = wx.App()
	MyFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
