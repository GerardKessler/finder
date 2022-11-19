from pathlib import Path
import re
from subprocess import run

class NewSearch():

	def __init__(self):
		self.scopes = {"a": "*", "t": "**/*"}
		self.folderPath = None
		self.pattern = None
		self.scope = None
		self.newSearch()

	def newSearch(self):
		while True:
			user = input("ingresa el texto de búsqueda o expresión regular")
			try:
				pattern = re.compile(user)
			except re.error:
				print("Expresión regular inválida. Por favor vuelve a intentarlo")
				continue
			scope = input("Ingresa a para buscar en el directorio actual, o t para buscar de forma recursiva")
			if scope == "a" or scope == "t":
				self.pattern = pattern
				self.scope = scope
				self.get_files()
				break

	def get_files(self, folderPath="."):
		files = Path(folderPath).glob(self.scopes[self.scope])
		self.startSearch(files)

	def startSearch(self, files):
		for file in files:
			filePath = str(file.absolute()).replace("\\", "/")
			result = self.search_string(filePath)
			if result:
				print(f"Encontrado en el archivo {file.name}, en la línea {result}")
				open_file = input("ingresa a para abrir con el blok de notas")
				if open_file == "a":
					run(["notepad", filePath])

	def search_string(self, filePath):
		index = 0
		try:
			with Path(filePath).open(mode="r") as f:
				for line in f:
					index+=1
					if self.pattern.search(line):
						return index
		except (PermissionError, TypeError, UnicodeDecodeError):
			pass
		return False

NewSearch()