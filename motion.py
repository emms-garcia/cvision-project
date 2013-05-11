import cv2
import cv

########################################################################################
#Variables importantes utilizadas
########################################################################################
WIDTH = 320 #Ancho de video a usar
HEIGHT = 240 #Alto de video a usar
AREA = WIDTH*HEIGHT #Numero de pixeles/Area total de los frames
MIN_PERCENT = 0.1 #Porcentaje minimo de pixeles que debe tener un objeto en movimiento
GAUSSIAN_BLUR_FACTOR_1 = 3 #Tamano de la matriz usada para eliminar ruido la primera vez
GAUSSIAN_BLUR_FACTOR_2 = 19 #Tamano de la matriz usada para eliminar ruido la segunda vez
BINARY_THRESHOLD_1 = 2 #Umbral de binarizacion inicial
BINARY_THRESHOLD_2 = 240 #Umbral de binarizacion final
DILATION_FACTOR = 1 #Tamano de la matriz usada para dilatar las manchas de movimiento
SHOW_MOVEMENT_CONTOUR = True #Ver o no contornos de las manchas de movimiento
SHOW_MOVEMENT_AREA = False #Ver o no las manchas de movimiento

########################################################################################
#Propiedades de la captura de imagenes desde la camara.
########################################################################################
c = cv.CreateCameraCapture(0) #Usar camara 0 (camara web)
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH ) #Ajustar ancho de video
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT ) #Ajustar altura de video

########################################################################################
#Inicializacion de variables. En esta version de OpenCV para Python en muchas funciones
#es necesario pasar como argumento la variable en la cual queremos que retorne un cierto
#dato esa funcion, y debe ser del mismo tipo de dato que la funcion utiliza.
########################################################################################
frame = cv.QueryFrame( c ) #Se toma un frame desde la camara para crear copias
grey_image = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) #copia usada para binarizacion y grescale
running_average_image = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_32F, 3 ) #copia usada para promediado de frames
running_average_in_display_color_depth = cv.CloneImage( frame ) #copia usada para conversion de escala
mem_storage = cv.CreateMemStorage(0) #buffer de memoria usado por algunas funciones
difference = cv.CloneImage( frame ) #copia usada para almacenar la diferencia entre frames

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
      has_collision = False
      if (x1 < w2 and w1 > x2 and y1 < h2 and h1 > y2):
        has_collision = True
      if has_collision:
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
#Funcion que realiza todos los procesamientos a los frames de la camara para obtener
#al final una imagen binarizada, donde los pixeles blancos son en los que hubo 
#movimiento y los negros en los que no.
########################################################################################
def get_motion_mask(camera_image):
  color_image = cv.CloneImage( camera_image ) #copia usada para no modificar la original
  cv.Smooth( color_image, color_image, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR_1, 0 ) #smooth/blur inicial para eliminar ruido
  cv.RunningAvg( color_image, running_average_image, 0.320, None )#obtencion de un promedio de frames
  cv.ConvertScale( running_average_image, running_average_in_display_color_depth, 1.0, 0.0 ) #conversion de escala
  cv.AbsDiff( color_image, running_average_in_display_color_depth, difference ) #diferencia entre la imagen promedio y la original
  cv.CvtColor( difference, grey_image, cv.CV_RGB2GRAY )#conversion de la imagen a escala de grises
  cv.Threshold( grey_image, grey_image, BINARY_THRESHOLD_1, 255, cv.CV_THRESH_BINARY )#binarizacion de la imagen
  cv.Dilate(grey_image, grey_image, None, DILATION_FACTOR) #dilatacion de los pixeles blancos para juntar manchas de movimiento cercanas
  cv.Smooth( grey_image, grey_image, cv.CV_GAUSSIAN, GAUSSIAN_BLUR_FACTOR_2, 0 ) #otro smooth aplicado para eliminar pequenas manchas
  cv.Threshold( grey_image, grey_image, BINARY_THRESHOLD_2, 255, cv.CV_THRESH_BINARY ) #rebinarizacion para eliminar pequenas manchas
  return grey_image

########################################################################################
#Loop infinito para ejecutar las rutinas de deteccion de movimiento hasta
#que se presione la tecla esc
########################################################################################
while True:
  camera_image = cv.QueryFrame( c ) #imagen obtenida de la camara
  prev = get_motion_mask(camera_image) #imagen tratada con los filtros para obtener zonas en movimiento
  #obtencion de contornos de las manchas
  contour = cv.FindContours( prev, mem_storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE )
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
    if SHOW_MOVEMENT_AREA: cv.FillPoly( camera_image, [ list(polygon_points), ], cv.CV_RGB(255,255,255), 0, 0 )
    #mostrar o no los contornos de las manchas de movimiento
    if SHOW_MOVEMENT_CONTOUR and w*h > AREA*MIN_PERCENT: cv.PolyLine( camera_image, [ polygon_points, ], 0, cv.CV_RGB(255,255,255), 1, 0, 0 )
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
  for pt1, pt2 in bbox_list: #recorrido de los bounding box finales
    cv.Rectangle(camera_image, pt1, pt2, cv.CV_RGB(255,0,0), 1) #se dibuja un rectangulo en ese bounding box
#  if len(points):
#    center_point = reduce(lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), points)
#    cv.Circle(camera_image, center_point, 40, cv.CV_RGB(255, 255, 255), 1)
#    cv.Circle(camera_image, center_point, 30, cv.CV_RGB(255, 100, 0), 1)
#    cv.Circle(camera_image, center_point, 20, cv.CV_RGB(255, 255, 255), 1)
#    cv.Circle(camera_image, center_point, 10, cv.CV_RGB(255, 100, 0), 1)
  cv.ShowImage('e2', camera_image) #mostrar los resultados en el feed de video

  if cv.WaitKey(5) == 27: #si se presiona la tecla esc
    break #salir del while infinito para terminar
