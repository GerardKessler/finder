from os import path, getcwd, walk, scandir, environ
import wx
import gui
from comtypes.client import CreateObject as COMCreate
import globalPluginHandler
import controlTypes
import api
from scriptHandler import script
from ui import message, browseableMessage

import re
from subprocess import run

def getDocName():
	docPath = ""
	fg = api.getForegroundObject()
	if fg.role != api.controlTypes.Role.PANE and fg.appModule.appName != "explorer":
		return
	shell = COMCreate("shell.application")
	for window in shell.Windows():
		try:
			if window.hwnd and window.hwnd == fg.windowHandle:
				focusedItem=window.Document.FocusedItem
				break
		except:
			pass
	else:
		desktop_path = path.join(path.join(environ['USERPROFILE']), 'Desktop')
		docPath = '\"' + desktop_path + '\\' + api.getDesktopObject().objectWithFocus().name + '\"'
		return
	targetFile= focusedItem.path
	docPath = path.split(str(targetFile))[0]
	return docPath

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(gesture="kb:NVDA+control+shift+p")
	def script_getPath(self, gesture):
		newSearch = NewSearch(gui.mainFrame, _('Nueva búsqueda'))
		gui.mainFrame.prePopup()
		newSearch.Show()

class NewSearch(wx.Dialog):

	def __init__(self, parent, new_title):
		super(NewSearch, self).__init__(parent, -1, title= new_title)
		self.path_folder = getDocName()
		self.pattern = re.compile(r"/feeds/")
		self.scope = "t"
		self.panel = wx.Panel(self, wx.ID_ANY)

		sizer = wx.BoxSizer(wx.VERTICAL)

		label_1 = wx.StaticText(self.panel, wx.ID_ANY, _("Ruta acttual"))
		sizer.Add(label_1, 0, 0, 0)

		self.text_ctrl_1 = wx.TextCtrl(self.panel, wx.ID_ANY, self.path_folder)
		sizer.Add(self.text_ctrl_1, 0, 0, 0)

		self.browse_button = wx.Button(self.panel, wx.ID_ANY, _(u"Examinar"))
		sizer.Add(self.browse_button, 0, 0, 0)

		self.scope = wx.RadioBox(self.panel, wx.ID_ANY, _(u"Selecciona el alcance de la búsqueda"), choices=[_("Recursiva en todas las carpetas"), _(u"Solo en la raíz de la carpeta actual")], majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.scope.SetSelection(0)
		sizer.Add(self.scope, 0, 0, 0)

		label_2 = wx.StaticText(self.panel, wx.ID_ANY, _(u"Cadena o expresión regular a buscar"))
		sizer.Add(label_2, 0, 0, 0)

		self.string_search = wx.TextCtrl(self.panel, wx.ID_ANY, "")
		sizer.Add(self.string_search, 0, 0, 0)

		self.start_button = wx.Button(self.panel, wx.ID_ANY, _(u"Iniciar la búsqueda"))
		sizer.Add(self.start_button, 0, 0, 0)

		self.cancel_button = wx.Button(self.panel, wx.ID_ANY, _("Cancelar y cerrar"))
		sizer.Add(self.cancel_button, 0, 0, 0)

		self.panel.SetSizer(sizer)

	def onPass(self, event):
		pass

	def onSalir(self, event):
		if event.GetEventType() == 10012:
			self.Destroy()
			gui.mainFrame.postPopup()
		elif event.GetActive() == False:
			self.Destroy()
			gui.mainFrame.postPopup()
		event.Skip()

	def get_files(self):
		if self.scope == "a":
			files = [file.path for file in scandir(self.path_folder) if file.is_file()]
		elif self.scope == "t":
			files = []
			for (absolute_path, folder_name, file_list) in walk(self.path_folder):
				for file in file_list:
					files.append(path.join(absolute_path, file))
		self.startSearch(files)

	def startSearch(self, files):
		for file in files:
			result = self.search_string(file)
			if result:
				print(f"Encontrado en el archivo {path.split(file)[1]}, en la línea {result}")

	def search_string(self, file_path):
		index = 0
		try:
			with open(file_path) as f:
				for line in f:
					index+=1
					if self.pattern.search(line):
						return index
		except (PermissionError, TypeError, UnicodeDecodeError):
			pass
		return False

