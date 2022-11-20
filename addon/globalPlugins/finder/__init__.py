from os import path, getcwd, walk, scandir
import wx
import gui
from comtypes.client import CreateObject as COMCreate
import globalPluginHandler
import controlTypes
import api
from scriptHandler import script
from ui import message, browseableMessage
from threading import Thread
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
		self.path_folder = None
		self.pattern = None
		self.parent = parent
		self.panel = wx.Panel(self, wx.ID_ANY)

		sizer = wx.BoxSizer(wx.VERTICAL)

		label_1 = wx.StaticText(self.panel, wx.ID_ANY, _("Ruta acttual"))
		sizer.Add(label_1, 0, 0, 0)

		self.search_path = wx.TextCtrl(self.panel, wx.ID_ANY, getDocName())
		sizer.Add(self.search_path, 0, 0, 0)

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

		self.cancel_button = wx.Button(self.panel, wx.ID_CANCEL, _('&Cerrar'))
		sizer.Add(self.cancel_button, 0, 0, 0)

		self.panel.SetSizer(sizer)

		self.start_button.Bind(wx.EVT_BUTTON, self.get_files)
		self.cancel_button.Bind(wx.EVT_BUTTON, self.onSalir)
		self.search_path.Bind(wx.EVT_CONTEXT_MENU, self.onPass)
		self.string_search.Bind(wx.EVT_CONTEXT_MENU, self.onPass)
		self.Bind(wx.EVT_ACTIVATE, self.onSalir)
		self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)

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

	def verify(self):
		path_folder = self.search_path.GetValue()
		if path.exists(path_folder):
			self.path_folder = path_folder
		else:
			message(_('Ruta inválida. Por favor vuelva a ingresarla'))
			self.search_path.SetFocus()
			return False
		string_search = self.string_search.GetValue()
		if string_search == "":
			message(_('Por favor ingresa alguna búsqueda'))
			self.string_search.SetFocus()
			return False
		try:
			self.pattern = re.compile(string_search)
			return True
		except re.error:
			message(_('Expresión regular inválida. Por favor vuelve a intentarlo'))
			self.string_search.SetFocus()
			return False

	def get_files(self, event):
		if not self.verify(): return
		if self.scope.GetSelection() == 1:
			files = [file.path for file in scandir(self.search_path.GetValue()) if file.is_file()]
		elif self.scope.GetSelection() == 0:
			files = []
			for (absolute_path, folder_name, file_list) in walk(self.search_path.GetValue()):
				for file in file_list:
					files.append(path.join(absolute_path, file))
		self.startSearch(files)

	def startSearch(self, files):
		results = []
		for file in files:
			result = self.search_string(file)
			if result:
				result_dict = {"name": path.split(file)[1], "path": file, "line": result}
				results.append(result_dict)
				self.Close()
				newResults = Results(self.parent, results)
				self.parent.prePopup()
				newResults.Show()

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

class Results(wx.Dialog):

	def __init__(self, parent, results):
		super(Results, self).__init__(parent, -1, title= _(f'{len(results)} resultados'))
		self.results = results
		self.name_files = [f"{result['name']}, línea {result['line']}" for result in results]
		self.panel = wx.Panel(self, wx.ID_ANY)

		sizer_1 = wx.BoxSizer(wx.VERTICAL)

		label_1 = wx.StaticText(self.panel, wx.ID_ANY, _("Archivos encontrados"))
		sizer_1.Add(label_1, 0, 0, 0)

		self.list_files = wx.ListBox(self.panel, wx.ID_ANY, choices=self.name_files)
		self.list_files.SetSelection(0)
		sizer_1.Add(self.list_files, 0, 0, 0)

		self.nvda_button = wx.Button(self.panel, wx.ID_ANY, _("Abrir en una ventana de NVDA"))
		sizer_1.Add(self.nvda_button, 0, 0, 0)

		self.notepad_button = wx.Button(self.panel, wx.ID_ANY, _("Abrir con el bloc de notas"))
		sizer_1.Add(self.notepad_button, 0, 0, 0)

		self.cancel_button = wx.Button(self.panel, wx.ID_CANCEL, _('&Cerrar'))
		sizer_1.Add(self.cancel_button, 0, 0, 0)

		self.panel.SetSizer(sizer_1)

		self.nvda_button.Bind(wx.EVT_BUTTON, self.onNVDA)
		self.notepad_button.Bind(wx.EVT_BUTTON, self.onNotepad)
		self.cancel_button.Bind(wx.EVT_BUTTON, self.onSalir)
		self.Bind(wx.EVT_ACTIVATE, self.onSalir)
		# self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)

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

	def onNVDA(self, event):
		browseableMessage(self.results[self.list_files.GetSelection()]["path"])

	def onNotepad(self, event):
		Thread(target=self.notepad, daemon= True).start()

	def notepad(self):
		file_path = self.results[self.list_files.GetSelection()]["path"]
		run(["notepad", file_path])
