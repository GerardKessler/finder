# finder

Módulo global que permite buscar  texto en el contenido de los archivos de una carpeta de forma recursiva. Busca a partir  de alguna palabra, frase, o expresión regular. 

## Atajos del complemento

* Sin asignar: Activa la ventana de búsqueda

### Instrucciones de uso

Al abrir el explorador de archivos en una carpeta, podemos buscar entre sus archivos  dependiendo de alguna palabra frase o expresión regular.
Para ello hay que pulsar el comando previamente asignado en los gestos de entrada para abrir la interfaz.
En la misma podremos seleccionar la ruta de búsqueda, el alcance, la cantidad de resultados, el tipo de bhúsqueda y el contenido a buscar.
Hay que tener en cuenta que la misma se realiza abriendo uno a uno los archivos y leyendo línea a línea, por lo que si seleccionamos todos los resultados la búsqueda puede tardar mucho tiempo.

Si no se encuentran resultados se avisa a través de un mensaje modal, de lo contrario se activa una nueva ventana con lo siguiente:

* Una lista de resultados que tiene el nombre del archivo, y el número de línea donde se encontró la coincidencia.
* Un botón que permite abrir el archivo con el editor seleccionado. Por defecto está configurado el bloc de notas.
* Un botón que permite copiar la ruta absoluta del archivo seleccionado en la lista al portapapeles.
* Un botón que permite cambiar el editor para abrir los archivos; Bloc de notas, notepad++, y VisualStudioCode.

Lógicamente estos programas deben estar instalados para utilizarse. En el caso de que la apertura con VisualStudioCode o notepad++ falle, se abrirá automáticamente con el bloc de notas.
En el caso de abrirse con los 2 primeros editores, el cursor de edición debería situarse automáticamente en la línea donde se encontró la coincidencia.

