cvision-project
===============
Proyecto: Detección de Movimiento
Creado por: Emmanuel García
Correo: aleksgs10@gmail.com
Blog: http://synnick.blogspot.com
Fecha Última de Modificación: 12 de Mayo de 2013

Instalación
===========

No es necesario instalar el programa, basta con descargarlo
para poder ejecutarlo. Para ver los requerimientos necesarios
para ejecutarlo correctamente, ver el archivo "INSTALL".

Ejecución
=========

Para correr el ejemplo en Linux, basta con abrir una terminal,
localizarse en el directorio donde se encuentra el programa
y escribir el comando:

		python motion.py

Para obtener más información sobre los parámetros de ejecución
correr:

		python motion.py --help // python motion.py -h

Uso
===

En ejecución utilizando algún video predefinido, y sin
especificar archivo de salidael programa inicialmente se
encontrará pausado, esperando entrada del usuario.

Para correr la deteccion de movimiento en todo el video sin 
interrupciones, oprimir p/P. 

Para ver el video frame por frame, estando pausado el video
presionar n/N para ver el siguiente frame o b/B para ver
el frame anterior.

Para grabar un frame, estando pausado el video y localizado
en dicho frame, se presiona s/S.

En ejecución utilizando algún video predefinido y con 
algún nombre de archivo de salida definido, el video se
reproducira automaticamente, y se escribira la salida
en el archivo designado.

En ejecución, sin ningun video de entrada definido, se
utilizara la webcam.

Para salir presionar ESC o Enter.

Acerca de
=========

Este programa es un proyecto para la materia de Visión Computacional
de la carrera de Ingeniería en Tecnología de Software en la Facultad 
de Ingeniería Mecánica y Eléctrica, impartida por la Doctora Elisa
Schaeffer. 

Página Web del curso:
http://elisa.dyndns-web.com/~elisa/teaching/comp/vision/2013.html

Para más información sobre el funcionamiento del proyecto, visitar
el post en la siguiente liga:
http://synnick.blogspot.com/2013/05/reporte-de-proyecto-deteccion-de.html
