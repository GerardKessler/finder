# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gera Késsler <gera.kessler@gmail.com>
# This file is covered by the GNU General Public License.

import wx
from threading import Thread
import queue
import re
from subprocess import run
from math import inf
from winsound import PlaySound, SND_FILENAME, SND_ASYNC, SND_LOOP, SND_PURGE
from os import path, getcwd, walk, scandir, environ
from shellapi import ShellExecute

import gui
from comtypes.client import CreateObject as COMCreate
import globalPluginHandler
import controlTypes
import api
import globalVars
from scriptHandler import script
from ui import message, browseableMessage

# # código desarrollado originalmente por Alberto Buffolino para el complemento Column review
def getDocName():
	docPath= ""
	fg= api.getForegroundObject()
	if fg.role != api.controlTypes.Role.PANE and fg.appModule.appName != "explorer":
		return "None"
	shell= COMCreate("shell.application")
	for window in shell.Windows():
		try:
			if window.hwnd and window.hwnd == fg.windowHandle:
				focusedItem=window.Document.FocusedItem
				break
		except:
			pass
	else:
		desktop_path= path.join(path.join(environ['USERPROFILE']), 'Desktop')
		docPath= '\"' + desktop_path + '\\' + api.getDesktopObject().objectWithFocus().name + '\"'
		return "None"
	targetFile= focusedItem.path
	docPath= path.split(str(targetFile))[0]
	return docPath

ADDON_PATH= path.dirname(__file__)

def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return decoratedCls

@disableInSecureMode
class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		self.IS_WINON= False
		self.fileVerify()

	def fileVerify(self):
		if not path.exists(path.join(ADDON_PATH, 'editor')):
			with open(path.join(ADDON_PATH, 'editor'), 'w') as editor:
				editor.write('BlocDeNotas')

	@script(
		category= 'finder',
		description= _('Activa la ventana de nueva búsqueda'),
		gesture=None
	)
	def script_newFinder(self, gesture):
		if not self.IS_WINON:
			AddonThread(self, 1).start()
		else:
			# Translators: Mensaje que avisa de la existencia de una instancia abierta
			message(_('Existe una instancia activa del complemento'))

class NewSearch(wx.Dialog):
	def __init__(self, parent, frame_addon, new_title):
		super(NewSearch, self).__init__(parent, -1, title= new_title)
		self.frame= frame_addon
		self.frame.IS_WINON= True
		self.dlgload= None
		self.path_folder= getDocName()
		self.pattern= None
		self.parent= parent
		self.panel= wx.Panel(self, wx.ID_ANY)
		sizer= wx.BoxSizer(wx.VERTICAL)

		label= wx.StaticText(self.panel, wx.ID_ANY, _("Ruta acttual"))
		sizer.Add(label, 0, 0, 0)

		self.search_path= wx.TextCtrl(self.panel, wx.ID_ANY, self.path_folder)
		sizer.Add(self.search_path, 0, 0, 0)

		self.browse_button= wx.Button(self.panel, wx.ID_ANY, _(u"Examinar"))
		sizer.Add(self.browse_button, 0, 0, 0)

		self.scope= wx.RadioBox(self.panel, wx.ID_ANY, _(u"Selecciona el alcance de la búsqueda"), choices=[_("Recursiva: incluye todos los subdirectorios"), _(u"Raíz: solo el directorio actual")], majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.scope.SetSelection(0)
		sizer.Add(self.scope, 0, 0, 0)

		self.amounts= [[_('Un resultado'), 1], [_('5 resultados'), 5], [_('10 resultados'), 10], [_('25 resultados'), 25], [_('Todos los resultados'), inf]]
		self.amount= wx.RadioBox(self.panel, wx.ID_ANY, _(u"Selecciona la cantidad de resultados a mostrar"), choices=[amount[0] for amount in self.amounts], majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.amount.SetSelection(1)
		sizer.Add(self.amount, 0, 0, 0)

		self.type_search= wx.RadioBox(self.panel, wx.ID_ANY, _(u"Selecciona el tipo de búsqueda"), choices=[_("Texto"), _(u"Expresión regular")], majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.type_search.SetSelection(0)
		sizer.Add(self.type_search, 0, 0, 0)

		label_2= wx.StaticText(self.panel, wx.ID_ANY, _(u"Cadena o expresión regular a buscar"))
		sizer.Add(label_2, 0, 0, 0)

		self.string_search= wx.TextCtrl(self.panel, wx.ID_ANY, "")
		sizer.Add(self.string_search, 0, 0, 0)

		self.start_button= wx.Button(self.panel, wx.ID_ANY, _(u"Iniciar la búsqueda"))
		sizer.Add(self.start_button, 0, 0, 0)

		self.cancel_button= wx.Button(self.panel, wx.ID_CANCEL, _('&Cerrar'))
		sizer.Add(self.cancel_button, 0, 0, 0)

		self.panel.SetSizer(sizer)

		self.browse_button.Bind(wx.EVT_BUTTON, self.fileDialog)
		self.start_button.Bind(wx.EVT_BUTTON, self.get_files)
		self.cancel_button.Bind(wx.EVT_BUTTON, self.onSalir)
		self.search_path.Bind(wx.EVT_CONTEXT_MENU, self.onPass)
		self.string_search.Bind(wx.EVT_CONTEXT_MENU, self.onPass)
		self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)

	def onPass(self, event):
		pass

	def onSalir(self, event):
		if event.GetEventType() == 10012:
			self.frame.IS_WINON= False
			self.Destroy()
			gui.mainFrame.postPopup()
		elif not event.GetSkipped():
			self.frame.IS_WINON= False
			self.Destroy()
			gui.mainFrame.postPopup()
		event.Skip()

	def fileDialog(self, event):
		# Translators: Título del diálogo de búsqueda de carpeta
		dlg= wx.DirDialog(self, message=_('Seleccionar carpeta de búsqueda'), style=wx.DD_DEFAULT_STYLE)
		if dlg.ShowModal() == wx.ID_OK:
			self.search_path.SetValue(dlg.GetPath())
			self.search_path.SetFocus()
		else:
			return
			dlg.Destroy()

	def verify(self):
		path_folder= self.search_path.GetValue()
		type_search= self.type_search.GetSelection()
		if path.exists(path_folder):
			self.path_folder= path_folder
		else:
			message(_('Ruta inválida. Por favor vuelva a ingresarla'))
			self.search_path.SetFocus()
			return False
		string_search= self.string_search.GetValue()
		if string_search == "":
			message(_('Por favor ingresa alguna búsqueda'))
			self.string_search.SetFocus()
			return False
		if type_search == 0: return True
		try:
			self.pattern= re.compile(string_search)
			return True
		except re.error:
			message(_('Expresión regular inválida. Por favor vuelve a intentarlo'))
			self.string_search.SetFocus()
			return False

	def get_files(self, event):
		if not self.verify(): return
		self.out_queue= queue.Queue()
		thread= Thread(target=self.get_file_list, args= (self.out_queue,), daemon= True).start()
		# Translators: Mensaje de espera
		self.dlgload= PopupDialog(None, _('Espere por favor...'), _("Obteniendo datos."))
		self.dlgload.ShowModal()
		resultados= self.out_queue.get()
		self.dlgload.Destroy()
		self.Close()
		if len(resultados) > 0:
			newResults= Results(self.parent, self.frame, resultados)
			self.parent.prePopup()
			newResults.Show()
		else:
			PlaySound(None, SND_PURGE)
			browseableMessage(_('No se han encontrado resultados con la búsqueda ingresada'), '😖')

	def get_file_list(self, out_queue):
		PlaySound(path.join(ADDON_PATH, "sounds", "tic-tac.wav"), SND_LOOP + SND_ASYNC)
		if self.scope.GetSelection() == 1:
			files= [file.path for file in scandir(self.search_path.GetValue()) if file.is_file()]
		elif self.scope.GetSelection() == 0:
			files= []
			for (absolute_path, folder_name, file_list) in walk(self.search_path.GetValue()):
				for file in file_list:
					files.append(path.join(absolute_path, file))
		results= []
		for file in files:
			result= self.search_string(file)
			if result:
				result_dict= {"name": path.split(file)[1], "path": file, "line": result}
				results.append(result_dict)
				if len(results) == self.amounts[self.amount.GetSelection()][1]:
					break
		PlaySound(path.join(ADDON_PATH, "sounds", "finish.wav"), SND_FILENAME)
		out_queue.put(results)
		self.dlgload.getMessage("")

	def search_string(self, file_path):
		index= 0
		type_search= self.type_search.GetSelection()
		string_search= self.string_search.GetValue() 
		try:
			with open(file_path, encoding="latin-1") as f:
				for line in f:
					index+=1
					if type_search == 0:
						if string_search in line: 
							return index
					else:
						if self.pattern.search(line):
							return index
		except (PermissionError, TypeError, UnicodeDecodeError):
			pass
		return False

class Results(wx.Dialog):
	def __init__(self, parent, frame_addon, results):
		super(Results, self).__init__(parent, -1, title= _(f'{len(results)} resultados'))
		self.frame= frame_addon
		self.frame.IS_WINON= True
		self.results= results
		self.name_files= [f"{result['name']}, línea {result['line']}" for result in results]
		self.panel= wx.Panel(self, wx.ID_ANY)

		sizer_1= wx.BoxSizer(wx.VERTICAL)

		label_1= wx.StaticText(self.panel, wx.ID_ANY, _("Archivos encontrados"))
		sizer_1.Add(label_1, 0, 0, 0)

		self.list_files= wx.ListBox(self.panel, wx.ID_ANY, choices=self.name_files)
		self.list_files.SetSelection(0)
		sizer_1.Add(self.list_files, 0, 0, 0)

		with open(path.join(ADDON_PATH, 'editor'), 'r') as editor:
			self.program= editor.read()
		self.notepad_button= wx.Button(self.panel, wx.ID_ANY, _("Abrir el archivo con el {}".format(self.program)))
		sizer_1.Add(self.notepad_button, 0, 0, 0)

		self.clipboard_button= wx.Button(self.panel, wx.ID_ANY, _("Copiar la ruta del archivo al portapapeles"))
		sizer_1.Add(self.clipboard_button, 0, 0, 0)

		self.change_editor_button= wx.Button(self.panel, wx.ID_ANY, _('Editor por defecto: {}. Pulsar para cambiar').format(self.program))
		sizer_1.Add(self.change_editor_button, 0, 0, 0)

		self.cancel_button= wx.Button(self.panel, wx.ID_CANCEL, _('&Cerrar'))
		sizer_1.Add(self.cancel_button, 0, 0, 0)

		self.panel.SetSizer(sizer_1)

		self.clipboard_button.Bind(wx.EVT_BUTTON, self.onClipboard)
		self.notepad_button.Bind(wx.EVT_BUTTON, self.fileOpen)
		self.change_editor_button.Bind(wx.EVT_BUTTON, self.changeEditor)
		self.cancel_button.Bind(wx.EVT_BUTTON, self.onSalir)
		self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)


	def onPass(self, event):
		pass

	def onSalir(self, event):
		if event.GetEventType() == 10012:
			self.frame.IS_WINON= False
			self.Destroy()
			gui.mainFrame.postPopup()
		elif not event.GetSkipped:
			self.frame.IS_WINON= False
			self.Destroy()
			gui.mainFrame.postPopup()
		event.Skip()

	def changeEditor(self, event):
		if self.program == 'BlocDeNotas':
			new_editor= 'notepad++'
		elif self.program == 'notepad++':
			new_editor= 'VisualStudioCode'
		elif self.program == 'VisualStudioCode':
			new_editor= 'BlocDeNotas'
		with open(path.join(ADDON_PATH, 'editor'), 'w') as editor:
			editor.write(new_editor)
		self.program= new_editor
		self.notepad_button.SetLabel(_('Abrir el archivo con el {}').format(new_editor))
		self.change_editor_button.SetLabel(_('Editor por defecto: {}. Pulsar para cambiar').format(new_editor))

	def onClipboard(self, event):
		selection= self.list_files.GetSelection()
		api.copyToClip(self.results[selection]["path"])
		# Translators: Aviso de que la ruta ha sido copiada al portapapeles
		message(_('Ruta del archivo copiada al portapapeles'))

	def fileOpen(self, event):
		Thread(target=self.startOpen, daemon= True).start()

	def startOpen(self):
		file_path= self.results[self.list_files.GetSelection()]["path"]
		message(_('Abriendo el archivo. Por favor espere...'))
		if self.program == 'notepad++':
			if path.exists('C:/Program Files/Notepad++/notepad++.exe'):
				run(['C:/Program Files/Notepad++/notepad++.exe', "-n{}".format(self.results[self.list_files.GetSelection()]["line"]), file_path])
				return
			elif path.exists('C:/Program Files (x86)/Notepad++/notepad++.exe'):
				run(['C:/Program Files (x86)/Notepad++/notepad++.exe', "-n{}".format(self.results[self.list_files.GetSelection()]["line"]), file_path])
				return
			else:
				gui.messageBox(_('No se pudo abrir el archivo con este editor. Se utilizará el bloc de notas en su lugar'), '😟')
		elif self.program == 'VisualStudioCode':
			try:
				ShellExecute(None, None, 'code', '-g {}:{}'.format(file_path, self.results[self.list_files.GetSelection()]["line"]), None, 10)
				return
			except:
				gui.messageBox(_('No se pudo abrir el archivo con este editor. Se utilizará el bloc de notas en su lugar'), '😟')
		run(["notepad", file_path])

class PopupDialog(wx.Dialog):
	def __init__(self, parent, title, msg):
		wx.Dialog.__init__(self, parent, -1, title, size=(350, 150), style=wx.CAPTION)
		box= wx.BoxSizer(wx.VERTICAL)
		box2= wx.BoxSizer(wx.HORIZONTAL)

		if hasattr(wx, ''):
			ai= wx.ActivityIndicator(self)
			ai.Start()
			box2.Add(ai, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
		self.message= wx.StaticText(self, -1, msg, style=wx.ALIGN_CENTRE_VERTICAL)
		box2.Add(self.message, 0, wx.EXPAND | wx.ALL, 10)
		box.Add(box2, 0, wx.EXPAND)
		bitmap= wx.Bitmap(48, 48)
		bitmap= wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX, (48, 48))
		graphic= wx.StaticBitmap(self, -1, bitmap)
		box2.Add(graphic, 0, wx.TOP | wx.ALL, 10)

		self.SetAutoLayout(True)
		self.SetSizer(box)
		self.Fit()
		self.Layout()
		self.CenterOnScreen()
		self.Bind(wx.EVT_CLOSE, self.onCerrar)

	def SetMessage(self, status):
		self.message.SetLabel(status)

	def getMessage(self, status):
		try:
			self.EndModal(1)
		except:
			self.Close()

	def onCerrar(self, event):
		return

class AddonThread(Thread):
	def __init__(self, frame, option):
		super(AddonThread, self).__init__()
		self.frame= frame
		self.option= option
		self.daemon= True

	def run(self):
		def windowsApp():
			newSearch= NewSearch(gui.mainFrame, self.frame, _('Nueva búsqueda'))
			gui.mainFrame.prePopup()
			newSearch.Show()
		if self.option == 1:
			wx.CallAfter(windowsApp)
