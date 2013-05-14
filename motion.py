import cv
import math
import sys
import time
from threading import Thread

########################################################################################
#Por si se ingresa el flag -h o --help, imprimir informacion de ayuda
########################################################################################
try:
  if "-h" in sys.argv[1] or "--help" in sys.argv[1]:
    print "Ejecucion:"
    print "\t \t python %s input_video output_video"%sys.argv[0]
    print
    print "Parametros:"
    print "-input_video(opcional): Video de entrada a procesar (camara web si no se especifica)"
    print "-output_video(opcional): Video de salida para almacenar los resultados"
    sys.exit()
except IndexError:
  print 'Algo ocurrio.'

def normalize(x):
  a, b, c, d = (-180, 180, 0, 360)
  return (x*(d-c)/(b-a) + (c*b - a*d)/(b-a) )

def is_inside_bb(p, bb):
  (x1, y1), (x2, y2) = bb
  x, y = p
  if x > min(x1, x2) and x < max(x1, x2) and y > min(y1, y2) and y < max(y1, y2):
    return True
  else:
    return False

########################################################################################
#Funcion que a partir de una lista de bounding box busca aquellos que se sobreponen
#y los combina creando uno solo. Retorna la nueva lista conteniendo bounding box
#no sobrepuestos.
########################################################################################
def get_collided_bboxes(bbox_list):
  for this_bbox in bbox_list:
    for other_bbox in bbox_list:
      if this_bbox is other_bbox: continue
      (x1, y1), (w1, h1) = this_bbox
      (x2, y2), (w2, h2) = other_bbox
      if (x1 < w2 and w1 > x2 and y1 < h2 and h1 > y2):
        x = min(x1, x2)
        y = min(y1, y2)
        w = max(w1, w2)
        h = max(h1, h2)
        new_bbox = ((x, y), (w, h))
        bbox_list.remove(this_bbox)
        bbox_list.remove(other_bbox)
        bbox_list.append(new_bbox)
        return get_collided_bboxes(bbox_list)
  return bbox_list

########################################################################################
#Simple funcion usada para calcular la distancia entre dos puntos.
########################################################################################
def distance(p1, p2):
  x1, y1 = p1
  x2, y2 = p2
  return math.sqrt( (y2 - y1)**2 + (x2 - x1)**2)

########################################################################################
#Funcion usada para calcular el cambo de tamano de una imagen.
########################################################################################
def calculate_resize(actual_size, input_size):
  max_actual = max(actual_size)
  max_input = max(input_size)
  rate_change = float(max_input) / max_actual
  return tuple([int(i*rate_change) for i in actual_size])

########################################################################################
#Propiedades de la captura de imagenes desde la camara.
########################################################################################
WIDTH = 440 #Ancho de video a usar
HEIGHT = 200 #Alto de video a usar
#FPS = 30
#BRIGHTNESS = 200
#CONTRAST = 200
AREA = WIDTH*HEIGHT #Numero de pixeles/Area total de los frames
MIN_PERCENT = 0.05 #Porcentaje minimo de pixeles que debe tener un objeto en movimiento
GAUSSIAN_BLUR_FACTOR_1 = 3 #Tamano de la matriz usada para eliminar ruido la primera vez
GAUSSIAN_BLUR_FACTOR_2 = 19 #Tamano de la matriz usada para eliminar ruido la segunda vez
BINARY_THRESHOLD_1 = 10 #Umbral de binarizacion inicial
BINARY_THRESHOLD_2 = 240 #Umbral de binarizacion final
DILATION_FACTOR = 3 #Tamano de la matriz usada para dilatar las manchas de movimiento
SHOW_MOVEMENT_CONTOUR = True #Ver o no contornos de las manchas de movimiento
SHOW_MOVEMENT_AREA = False #Ver o no las manchas de movimiento
DIAGONAL = distance((0, 0), (WIDTH, HEIGHT)) #Distancia Maxima del video
GAUSSIAN_BLUR_FACTOR = 3 #Tamano de la matriz usada para eliminar ruido la primera vez
NFEATURES = 100 #Numero maximo de caracterististicas a buscar
NOPTICAL_FLOW = 5
NFRAMES = None #Numero de frames a usar, si se utiliza un archivo
VIDEOFILE = False #Para saber si se esta leyendo desde un archivo
PLAY = False #Para saber si se estan tomando los frames por si solos
#Font usado para los textos
TEXT_FONT = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX, .5, .5, 0.0, 1, cv.CV_AA )
VIDEO_WRITER = None #Para almacenar el objeto de OpenCV de escritura de videos
########################################################################################
#Inicializacion de lectura de frames. Si se especifico un archivo de video como argumento
#desde la linea de comandos, se utiliza dicho video, si no se utiliza la webcam.
########################################################################################
c = cv.CreateCameraCapture(0) #Usar camara 0 (camara web)
try:
  if ".avi" in sys.argv[1]:
    VIDEOFILE = True #si utilizaremos video de entrada
    c = cv.CaptureFromFile( sys.argv[1] ) #Usar camara 0 (camara web)
    #numero total de frames en el video
    NFRAMES = cv.GetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_COUNT  )
    print cv.GetCaptureProperty( c, cv.CV_CAP_PROP_FPS)
    #FRAMES_VIDEO = [None for i in range(int(NFRAMES))]
    #Ancho de resolucion usado en el video
    WIDTH = int(cv.GetCaptureProperty(c, cv.CV_CAP_PROP_FRAME_WIDTH))
    #Alto de resolucion usado en el video
    HEIGHT = int(cv.GetCaptureProperty(c, cv.CV_CAP_PROP_FRAME_HEIGHT))
    print WIDTH, HEIGHT
except:
  print "No se especifico video de entrada, usando camara web."
  print "Usa %s -h   o %s --help para conocer los parametros."%(sys.argv[0], sys.argv[0])
  
########################################################################################
#Lectura de archivo de salida, si se especifico alguno.
########################################################################################
try:
  if ".avi" in sys.argv[2]:
    VIDEO_WRITER = cv.CreateVideoWriter(sys.argv[2], cv.CV_FOURCC('P','I','M','1') , 30, (WIDTH, HEIGHT), True)
    print "Grabando video en: %s"%sys.argv[2]
except:
  print "No se especifico video de salida."
  print "Usa %s -h   o %s --help para conocer los parametros."%(sys.argv[0], sys.argv[0])
########################################################################################
#Propiedades de la captura de imagenes desde la webcam.
########################################################################################
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH ) #Ajustar ancho de video
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT ) #Ajustar altura de video
#cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FPS, FPS )
#cv.SetCaptureProperty( c, cv.CV_CAP_PROP_BRIGHTNESS, BRIGHTNESS ) 
#cv.SetCaptureProperty( c, cv.CV_CAP_PROP_CONTRAST, CONTRAST ) 

########################################################################################
#Inicializacion de variables para diferentes imagenes usadas en los calculos
#de caracteristicas y flujo optico.
########################################################################################
frame = cv.QueryFrame( c ) #Primer frame de la imagen usada para generar copias
ORIGINAL_SIZE = cv.GetSize(frame) #Tamano original del video antes del cambio de tamano
SIZE = (WIDTH, HEIGHT) #Nuevo tamano deseado
#contenedor de la imagen con el nuevo tamano
thumbnail = cv.CreateImage( calculate_resize(ORIGINAL_SIZE, SIZE), frame.depth, frame.nChannels)
#contenedores de parametros para el calculo de las caracteristicas
eig_image = cv.CreateImage(cv.GetSize(thumbnail), cv.IPL_DEPTH_32F, 1)
temp_image = cv.CreateImage(cv.GetSize(thumbnail), cv.IPL_DEPTH_32F, 1)
#contenedor para almacenar las posiciones de las caracteristicas al inicio
frame1_1C = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_8U, 1 ) 
#contenedor para almacenar las posiciones de las caracteristicas al despues del movimiento
frame2_1C = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_8U, 1 ) 
#contenedor de parametros usados en el algoritmo Lucas Kanade
pyramid1 = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_8U, 1 ) 
pyramid2 = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_8U, 1 )
#copia usada para binarizacion y grescale
grey_image = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_8U, 1 )
#copia usada para promediado de frames
running_average_image = cv.CreateImage( cv.GetSize(thumbnail), cv.IPL_DEPTH_32F, 3 )
#copia usada para conversion de escala
running_average_in_display_color_depth = cv.CloneImage( thumbnail )
mem_storage = cv.CreateMemStorage(0) #buffer de memoria usado por algunas funciones
difference = cv.CloneImage( thumbnail ) #copia usada para almacenar la diferencia entre frames
bbox_list = []

#muestra = 0
#prom = 0
def motion_bbox(output, motion):
  #global muestra, prom
  global bbox_list
  #INICIO = time.time()
  contour = cv.FindContours( motion, mem_storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE )  
  bbox_list = [] #lista para almacenar los bounding box de las manchas
  average_box_area = 0 #variable para obtener el area en promedio de las bounding box
  while contour: #recorrido de los contornos/manchas
    bbox = cv.BoundingRect(list(contour)) #obtencion del bounding box del contorno actual
    pt1 = (bbox[0], bbox[1]) #punto 1 del bounding box
    pt2 = (bbox[0] + bbox[2], bbox[1] + bbox[3]) #punto 2 del bounding box
    w, h = abs(pt1[0] - pt2[0]), abs(pt1[1] - pt2[1]) #ancho y largo del bounding box
    #obtencion de puntos del contorno para crear un wire-frame
    polygon_points = cv.ApproxPoly( list(contour), mem_storage, cv.CV_POLY_APPROX_DP )
    #mostrar o las manchas de movimiento
    if SHOW_MOVEMENT_AREA: cv.FillPoly( output, [ list(polygon_points), ], cv.CV_RGB(255,255,255), 0, 0 )
    #mostrar o no los contornos de las manchas de movimiento
    if SHOW_MOVEMENT_CONTOUR and w*h > AREA*MIN_PERCENT: cv.PolyLine( output, [ polygon_points, ], 0, cv.CV_RGB(255,255,255), 1, 0, 0 )
    average_box_area += w*h #acumulacion de totales de areas
    bbox_list.append((pt1, pt2)) #lista con todos los bounding box
    contour = contour.h_next() #lectura del siguiente contorno, si hay
  if len(bbox_list) > 0: #si hubo movimiento 
    average_box_area = average_box_area/float(len(bbox_list)) #area promedio de bounding box
    new_bbox_list = [] #nueva lista de bounding box, eliminando los menores al area promedio
    for i in range(len(bbox_list)): #recorrido de los bounding box
      pt1, pt2 = bbox_list[i] #separacion en dos puntos del bounding box
      w, h = abs(pt1[0] - pt2[0]), abs(pt1[1] - pt2[1]) #obtencion del ancho y largo
      if w*h >= average_box_area and w*h > AREA*MIN_PERCENT: #comparacion del area del bounding box con el promedio
        new_bbox_list.append((pt1, pt2)) #si es mayor o igual, se queda en la nueva lista
  bbox_list = get_collided_bboxes(new_bbox_list) #combinacion de varios bounding box en uno si estan en contacto
  #FIN = time.time()
  #print "%s, %s"%(muestra, FIN - INICIO)
  #prom += FIN - INICIO
 
########################################################################################
#Funcion que realiza todos los procesamientos a los frames de la camara para obtener
#al final una imagen binarizada, donde los pixeles blancos son en los que hubo 
#movimiento y los negros en los que no.
########################################################################################
def get_motion_mask(first_frame, second_frame):
  cv.Smooth( first_frame, first_frame, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR_1, 0 ) #smooth/blur inicial para eliminar ruido
  cv.Smooth( second_frame, first_frame, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR_1, 0 ) #smooth/blur inicial para eliminar ruido
  #cv.RunningAvg( color_image, running_average_image, 0.320, None )#obtencion de un promedio de frames
  #cv.ConvertScale( running_average_image, running_average_in_display_color_depth, 1.0, 0.0 ) #conversion de escala
  cv.AbsDiff( first_frame, second_frame, difference ) #diferencia entre la imagen promedio y la original
  cv.CvtColor( difference, grey_image, cv.CV_RGB2GRAY )#conversion de la imagen a escala de grises
  cv.Threshold( grey_image, grey_image, BINARY_THRESHOLD_1, 255, cv.CV_THRESH_BINARY )#binarizacion de la imagen
  #dilatacion y afinamiento de las manchas para crear blobs mas definidos
  cv.Dilate(grey_image, grey_image, None, 4)
  cv.Erode(grey_image, grey_image, None, 4)
  cv.Smooth( grey_image, grey_image, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR_2, 0 ) #otro smooth aplicado para eliminar pequenas manchas
  cv.Threshold( grey_image, grey_image, BINARY_THRESHOLD_2, 255, cv.CV_THRESH_BINARY ) #rebinarizacion para eliminar pequenas manchas
  return grey_image

cv.SetCaptureProperty(c, cv.CV_CAP_PROP_POS_FRAMES, 0.0 ) #reiniciar la lectura de video al primer frame
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FPS, 7.5)
print cv.GetCaptureProperty( c, cv.CV_CAP_PROP_FPS)
#cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT)
#cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH)
current_frame = 0
cv.NamedWindow("Deteccion de Movimiento", cv.CV_WINDOW_AUTOSIZE) 
cv.MoveWindow("Deteccion de Movimiento", (1366/2) - WIDTH/2, (768/2) - HEIGHT/2)
########################################################################################
#Loop infinito para ejecutar las rutinas de deteccion de movimiento hasta
#que se presione la tecla esc
########################################################################################
while True:
  #INICIO = time.time()
  if VIDEOFILE: cv.SetCaptureProperty(c, cv.CV_CAP_PROP_POS_FRAMES, current_frame )
  frame = cv.QueryFrame( c ) #primer frame obtenido para el calculo del flujo optico
  if frame == None: break #si no se obtuvo ningun frame, se termino el archivo de video
  cv.Resize(frame, thumbnail) #si se obtuvo un frame, se cambia el tamano al deseado
  first_frame = cv.CloneImage(thumbnail)
  output = cv.CloneImage( thumbnail ) #se crea una copia del frame para dibujar sobre el
  #se pasa un filtro gaussiano para reducir ruido
  cv.Smooth( thumbnail, thumbnail, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR, GAUSSIAN_BLUR_FACTOR )
  #se voltean las imagenes para corregir un error de opencv
  cv.ConvertImage(thumbnail, frame1_1C, cv.CV_CVTIMG_FLIP)
  #cv.ConvertImage(thumbnail, output, cv.CV_CVTIMG_FLIP)
  frame = cv.QueryFrame( c ) #segundo frame obtenido para el calculo del flujo optico
  if frame == None: break 
  cv.Resize(frame, thumbnail) 
  second_frame = cv.CloneImage(thumbnail)
  motion = get_motion_mask(first_frame, second_frame)
  cv.Smooth( thumbnail, thumbnail, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR, GAUSSIAN_BLUR_FACTOR )
  cv.ConvertImage(thumbnail, frame2_1C, cv.CV_CVTIMG_FLIP)
  t = Thread(target = motion_bbox, args=(output, motion, ))
  t.run()

  #obtencion de caracteristicas del primer frame
  frame1_features = cv.GoodFeaturesToTrack(frame1_1C, eig_image, temp_image, NFEATURES, 0.1, 5, None, 3, False)

  #busqueda de caracteristicas del primer frame, en el segundo usando el algoritmo de Lucas Kanade

  frame2_features, status, track_error = cv.CalcOpticalFlowPyrLK(frame1_1C, frame2_1C, pyramid1, pyramid2, frame1_features, 
                            (3, 3), 5,  (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS, 20, 0.03), 0)

  #recorrido de las caracteristicas y dibujo de las flechas
  #utilizando el algoritmo de http://ai.stanford.edu/~dstavens/cs223b/optical_flow_demo.cpp
  totals = []
  for pt1, pt2 in bbox_list: #recorrido de los bounding box finales
    cv.Rectangle(output, pt1, pt2, cv.CV_RGB(255,0,0), 1) #se dibuja un rectangulo en ese bounding box
    center = ( min(pt1[0], pt2[0]) + abs(pt1[0] - pt2[0])/2, min(pt1[1], pt2[1]) + abs(pt1[1] - pt2[1])/2 )
    angles = []
    for i in range(len(frame2_features)):
      p = frame1_features[i]
      q = frame2_features[i]
      p = int(p[0]), int(p[1])
      q = int(q[0]), int(q[1])
      angle = math.atan2(p[1] - q[1], p[0] - q[0]) #calculamos el angulo entre ellos
      hypotenuse = math.sqrt(math.pow(p[1] - q[1], 2) + math.pow(p[0] - q[0], 2))
      q = (int(p[0] - 3*hypotenuse * math.cos(angle)), int(p[1] - 3*hypotenuse * math.sin(angle)))
      p = (p[0], HEIGHT - p[1])
      q = (q[0], HEIGHT - q[1])
      if is_inside_bb(p, (pt1, pt2)) or is_inside_bb(p, (pt1, pt2)):
        #eliminacion de ruido (movimientos bruscos de un lado de la imagen al otro)
        if distance(p, q) > DIAGONAL * 0.2:
          continue
        #mas eliminacion de ruido (pequenos movimientos casi nulos)
        elif distance(p, q) < 10:
          continue
        #por un error, openCV toma los .avi al reves verticalmente, por lo que se voltean las coordenadas y
        angles.append(angle)
        #dibujo de las flechas de flujo optico
    if len(angles) > 0:
      p, q = center, center
      angle = sum(angles)/float(len(angles))
      if int(math.degrees(angle)) in range(90, 270):
        print "Derecha, ",math.degrees(angle)
        angle = math.radians(180)
      else:
        print "Izquierda, ", math.degrees(angle)
        angle = math.radians(0)
      cv.Line( output, p, q, cv.CV_RGB(0, 0, 255), 3, cv.CV_AA, 0 )
      p = (int(q[0] + 15 * math.cos(angle + math.pi / 4)), int(q[1] + 15 * math.sin(angle + math.pi/4)))
      cv.Line( output, p, q, cv.CV_RGB(0, 0, 255), 3, cv.CV_AA, 0 )
      p = (int(q[0] + 15 * math.cos(angle - math.pi / 4)), int(q[1] + 15 * math.sin(angle - math.pi/4)))
      cv.Line( output, p, q, cv.CV_RGB(0, 0, 255), 3, cv.CV_AA, 0 )

  #print "%s, %s"%(muestra, FIN - INICIO)
  text = ""
  key = cv.WaitKey(7) % 0x100
  if key == 27 or key == 10:
    break
  #Operaciones cuando se utiliza un video de entrada y no se esta escribiendo en la salida
  if VIDEOFILE and VIDEO_WRITER is None:
    if chr(key) == 'n' or chr(key) == 'N': #si se presiona n/N avanzamos un frame
      current_frame += 1.0
    elif chr(key) == 'b' or chr(key) == 'B': #si se presiona b/B retrocedemos un frame
      current_frame -= 1.0
    elif chr(key) == 'p' or chr(key) == 'P': #si se presiona p/P se pausa o inicia el video
      PLAY = not PLAY
    
    if (chr(key) == 's' or chr(key) == 'S') and not PLAY: #si se presiona s/S se almacena el frame
      cv.SaveImage("output_frame_%s.jpg"%current_frame, output) #se guarda la imagen
      #ponemos un texto confirmando que se guardo la imagen
      cv.PutText( output, "Frame guardado", (5, 30), TEXT_FONT, cv.CV_RGB(255, 255, 255))

    if PLAY: #si se reproduce automaticamente, aumentar los frames y cambiar el estado
      current_frame += 1
      text = "Estado Actual: (Play)"
    else:
      text = "Estado Actual: (Pausa)"

    #condiciones para evitar un error al llegar al frame -1 o NFRAMES + 1
    if current_frame < 0.0: 
      print "Se llego al principio del video, no se puede ir mas atras"
      current_frame = 0.0
    elif current_frame >= NFRAMES - 1: 
      print "Final del video, no se puede ir mas adelante"
      current_frame = NFRAMES - 2
      break
  else:
    #si se designo un archivo de salida, escribimos ahi el frame actual y avanzamos
    if VIDEO_WRITER: cv.WriteFrame(VIDEO_WRITER, output)
    current_frame += 1
  cv.PutText( output, text, (5, 15), TEXT_FONT, cv.CV_RGB(255, 255, 255) )
  cv.ShowImage("Deteccion de Movimiento", output) #mostrar los resultados en el feed de video   
  #FIN = time.time()
  #print "%s, %s"%(muestra, FIN - INICIO)
  #muestra += 1
  #prom += FIN - INICIO

print "Fin"
#print "Promedio: %s"%(prom/float(muestra))
