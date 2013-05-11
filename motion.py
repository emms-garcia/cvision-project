import cv2
import numpy as np
import Image
import cv
import sys

c = cv.CreateCameraCapture(0)
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_WIDTH, 320 )
cv.SetCaptureProperty( c, cv.CV_CAP_PROP_FRAME_HEIGHT, 240 )

frame = cv.QueryFrame( c )
grey_image = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_8U, 1 )
running_average_image = cv.CreateImage( cv.GetSize(frame), cv.IPL_DEPTH_32F, 3 )
running_average_in_display_color_depth = cv.CloneImage( frame )
mem_storage = cv.CreateMemStorage(0)
difference = cv.CloneImage( frame )

def get_motion_mask(camera_image):
  color_image = cv.CloneImage( camera_image )
  cv.Smooth( color_image, color_image, cv.CV_GAUSSIAN, 3, 0 )
  cv.RunningAvg( color_image, running_average_image, 0.320, None )
  cv.ConvertScale( running_average_image, running_average_in_display_color_depth, 1.0, 0.0 )
  cv.AbsDiff( color_image, running_average_in_display_color_depth, difference )
  cv.CvtColor( difference, grey_image, cv.CV_RGB2GRAY )
  cv.Threshold( grey_image, grey_image, 2, 255, cv.CV_THRESH_BINARY )
#  cv.Dilate(grey_image, grey_image, None, 18)
#  cv.Erode(grey_image, grey_image, None, 10)
  cv.Smooth( grey_image, grey_image, cv.CV_GAUSSIAN, 19, 0 )
  cv.Threshold( grey_image, grey_image, 240, 255, cv.CV_THRESH_BINARY )

  return grey_image


while(1):
  camera_image = cv.QueryFrame( c )
  #display_image = cv.CloneImage( camera_image )
  prev = get_motion_mask(camera_image)

  camera_image = cv.QueryFrame( c )
  next = get_motion_mask(camera_image)  
 
  #cv.ShowImage('e2', grey_image)
  points = []
  contour = cv.FindContours( prev, mem_storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE )
  #print len(contour)
  while contour:
    #prev_pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
    #pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
    #features, status, track_error = cv.CalcOpticalFlowPyrLK(prev, next, pyramid, prev_pyramid, contour,
    #                              (10, 10), 5,  (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS, 20, 0.03), 0)
    #print features
    #sys.exit()
    bound_rect = cv.BoundingRect(list(contour))
    polygon_points = cv.ApproxPoly( list(contour), mem_storage, cv.CV_POLY_APPROX_DP )
    contour = contour.h_next()

    cv.FillPoly( prev, [ list(polygon_points), ], cv.CV_RGB(255,255,255), 0, 0 )
    cv.PolyLine( camera_image, [ polygon_points, ], 0, cv.CV_RGB(255,255,255), 1, 0, 0 )

    pt1 = (bound_rect[0], bound_rect[1])
    pt2 = (bound_rect[0] + bound_rect[2], bound_rect[1] + bound_rect[3])
    points.append(pt1)
    points.append(pt2)
    cv.Rectangle(camera_image, pt1, pt2, cv.CV_RGB(255,0,0), 1)

#  if len(points):
#    center_point = reduce(lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), points)
#    cv.Circle(camera_image, center_point, 40, cv.CV_RGB(255, 255, 255), 1)
#    cv.Circle(camera_image, center_point, 30, cv.CV_RGB(255, 100, 0), 1)
#    cv.Circle(camera_image, center_point, 20, cv.CV_RGB(255, 255, 255), 1)
#    cv.Circle(camera_image, center_point, 10, cv.CV_RGB(255, 100, 0), 1)
  cv.ShowImage('e2', camera_image)

  if cv2.waitKey(5) == 27:
    break
cv2.destroyAllWindows()
