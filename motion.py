import cv
import math
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
pi = 3.14159265358979323846
while True:
  frame = cv.QueryFrame( c ) #imagen obtenida de la camara
  frame1 = cv.CloneImage( frame )
  #frame = get_motion_mask(frame) #imagen tratada con los filtros para obtener zonas en movimiento
  eig_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 1)
  temp_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 1)
  frame1_1C = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) 
  frame2_1C = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) 
  frame2_1C = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) 
  pyramid1 = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) 
  pyramid2 = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 ) 
  #cv.ConvertImage(frame, frame1_1C, cv.CVTIMPG_FLIP)
  cv.ConvertImage(frame, frame1_1C, cv.CV_CVTIMG_FLIP)
  #cv.ConvertImage(frame, frame1, cv.CV_CVTIMG_FLIP)

  frame = cv.QueryFrame( c ) #imagen obtenida de la camara
  cv.ConvertImage(frame, frame2_1C, cv.CV_CVTIMG_FLIP)

  qualityLevel = 0.1
  minDistance = 5
  number_of_features = 400
  frame1_features = cv.GoodFeaturesToTrack(frame1_1C, eig_image, temp_image, number_of_features, qualityLevel, minDistance, None, 3, False)

  frame2_features, status, track_error = cv.CalcOpticalFlowPyrLK(frame1_1C, frame2_1C, pyramid1, pyramid2, frame1_features, 
                            (3, 3), 5,  (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS, 20, 0.03), 0)
  for i in range(number_of_features):
    try:
      p = frame1_features[i]
      q = frame2_features[i]
      p = int(p[0]), int(p[1])
      angle = math.atan2(p[1] - q [1], p[0] - q[0])
      hypotenuse = math.sqrt(math.pow(p[1] - q[1], 2) + math.pow(p[0] - q[0], 2))
      q = (int(p[0] - 3*hypotenuse * math.cos(angle)), int(p[1] - 3*hypotenuse * math.sin(angle)))

      cv.Line( frame1, p, q, cv.CV_RGB(255, 0, 0), 1, cv.CV_AA, 0 )

      p = (int(q[0] + 9 * math.cos(angle + pi / 4)), int(q[1] + 9 * math.sin(angle + pi/4)))
      cv.Line( frame1, p, q, cv.CV_RGB(255, 0, 0), 1, cv.CV_AA, 0 )
      p = (int(q[0] + 9 * math.cos(angle - pi / 4)), int(q[1] + 9 * math.sin(angle - pi/4)))
      cv.Line( frame1, p, q, cv.CV_RGB(255, 0, 0), 1, cv.CV_AA, 0 )
    except IndexError:
      break
  
  cv.ShowImage('e2',frame1) #mostrar los resultados en el feed de video

  if cv.WaitKey(5) == 27: #si se presiona la tecla esc
    break #salir del while infinito para terminar
