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

right = 1
left = 0
bottom = 1
top = 0

def merge_collided_bboxes( bbox_list ):
  for this_bbox in bbox_list:
    for other_bbox in bbox_list:
      if this_bbox is other_bbox: continue
      has_collision = True
      if (this_bbox[bottom][0]*1.1 < other_bbox[top][0]*0.9): has_collision = False
      if (this_bbox[top][0]*.9 > other_bbox[bottom][0]*1.1): has_collision = False

      if (this_bbox[right][1]*1.1 < other_bbox[left][1]*0.9): has_collision = False
      if (this_bbox[left][1]*0.9 > other_bbox[right][1]*1.1): has_collision = False

      if has_collision:
        top_left_x = min( this_bbox[left][0], other_bbox[left][0] )
        top_left_y = min( this_bbox[left][1], other_bbox[left][1] )
        bottom_right_x = max( this_bbox[right][0], other_bbox[right][0] )
        bottom_right_y = max( this_bbox[right][1], other_bbox[right][1] )

        new_bbox = ( (top_left_x, top_left_y), (bottom_right_x, bottom_right_y) )

        bbox_list.remove( this_bbox )
        bbox_list.remove( other_bbox )
        bbox_list.append( new_bbox )
        return merge_collided_bboxes( bbox_list )
  return bbox_list

def get_motion_mask(camera_image):
  color_image = cv.CloneImage( camera_image )
  cv.Smooth( color_image, color_image, cv.CV_GAUSSIAN, 19, 0 )
  cv.RunningAvg( color_image, running_average_image, 0.320, None )
  cv.ConvertScale( running_average_image, running_average_in_display_color_depth, 1.0, 0.0 )
  cv.AbsDiff( color_image, running_average_in_display_color_depth, difference )
  cv.CvtColor( difference, grey_image, cv.CV_RGB2GRAY )
  cv.Threshold( grey_image, grey_image, 2, 255, cv.CV_THRESH_BINARY )
  # Smooth and threshold again to eliminate "sparkles"
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
  bounding_box_list = []
  contour = cv.FindContours( prev, mem_storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE )
  #print len(contour)
  if len(list(contour)) > 0:
    prev_pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
    pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
    features, status, track_error = cv.CalcOpticalFlowPyrLK(prev, next, pyramid, prev_pyramid, contour,
                                  (10, 10), 5,  (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS, 20, 0.03), 0)
    print features
#    sys.exit()
    bounding_rect = cv.BoundingRect( list(contour) )
    while contour:
      point1 = ( bounding_rect[0], bounding_rect[1] )
      point2 = ( bounding_rect[0] + bounding_rect[2], bounding_rect[1] + bounding_rect[3] )

      bounding_box_list.append( ( point1, point2 ) )
      polygon_points = cv.ApproxPoly( list(contour), mem_storage, cv.CV_POLY_APPROX_DP )

      cv.FillPoly( prev, [ list(polygon_points), ], cv.CV_RGB(255,255,255), 0, 0 )
      cv.PolyLine( camera_image, [ polygon_points, ], 0, cv.CV_RGB(255,255,255), 1, 0, 0 )

      contour = contour.h_next()


#  box_areas = []
#  for box in bounding_box_list:
#    cv.Rectangle( camera_image, box[0], box[1], (0, 255, 0), 1 )
#  cv.CalcOpticalFlowLK(prev, curr, winSize, velx, vely)
#  for box in bounding_box_list:
#    box_width = box[right][0] - box[left][0]
#    box_height = box[bottom][0] - box[top][0]
#    box_areas.append( box_width * box_height )
#  
#  average_box_area = 0.0
#  if len(box_areas): average_box_area = float( sum(box_areas) ) / len(box_areas)
#  
#  trimmed_box_list = []
#  for box in bounding_box_list:
#    box_width = box[right][0] - box[left][0]
#    box_height = box[bottom][0] - box[top][0]
#    if (box_width * box_height) > average_box_area*0.1: trimmed_box_list.append( box )
#    
#  bounding_box_list = merge_collided_bboxes( trimmed_box_list )
#  for box in bounding_box_list:
#    cv.Rectangle( display_image, box[0], box[1], cv.CV_RGB(0,255,0), 1 )
#  crit = ( cv.CV_TERMCRIT_EPS | cv.CV_TERMCRIT_ITER, 10, 1)

#  (iters, (area, value, rect), track_box) = cv.CamShift(grey_image, (box[0][0], box[0][1], box[1][0], box[1][1]), crit)
#  cv.EllipseBox( camera_image, track_box, cv.CV_RGB(255,0,0), 3, cv.CV_AA, 0 )
  cv.ShowImage('e2', camera_image)

  if cv2.waitKey(5) == 27:
    break
cv2.destroyAllWindows()
