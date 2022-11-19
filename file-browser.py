from os import scandir, walk, getcwd, path
import re
from subprocess import run

class NewSearch():

	def __init__(self):
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

	def get_files(self, folder_path= getcwd()):
		if self.scope == "a":
			files = [file.path for file in scandir(folder_path) if file.is_file()]
		elif self.scope == "t":
			files = []
			for (absolute_path, folder_name, file_list) in walk(folder_path):
				for file in file_list:
					files.append(path.join(absolute_path, file))
		self.startSearch(files)

	def startSearch(self, files):
		for file in files:
			result = self.search_string(file)
			if result:
				print(f"Encontrado en el archivo {path.split(file)[1]}, en la línea {result}")
				open_file = input("ingresa a para abrir con el blok de notas")
				if open_file == "a":
					run(["notepad", file])

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

NewSearch()