import cv2
import numpy as np
import Image
import cv

blur_cross = (19, 1) 
c = cv2.VideoCapture(0)
c.set(cv.CV_CAP_PROP_FRAME_WIDTH, 320) 
c.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
avg = np.float32(c.read()[1])

right = 1
left = 0
top = 0
bottom = 1

while(1):
  frame = c.read()[1]
  display_image = frame
  cv2.accumulateWeighted(frame, avg, 0.32)
  avg = cv2.GaussianBlur(avg, blur_cross, 0)
  res = cv2.convertScaleAbs(avg)
  diff = cv2.absdiff(frame, res)
  gray_image = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
  (thresh, grey_image) = cv2.threshold(gray_image, 2, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
  grey_image = cv2.GaussianBlur(grey_image, blur_cross, 0)
  (thresh, grey_image) = cv2.threshold(gray_image, 240, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
  contours, hierarchy = cv2.findContours(grey_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  bounding_box_list = []
  for contour in contours:
    bounding_rect = cv2.boundingRect(contour)
    point1 = ( bounding_rect[0], bounding_rect[1] )
    point2 = ( bounding_rect[0] + bounding_rect[2], bounding_rect[1] + bounding_rect[3] )
    bounding_box_list.append( ( point1, point2 ) )
    arc = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.1*arc, True)
    cv2.fillPoly(grey_image, approx, (255, 255, 255))
    cv2.polylines(display_image, approx, 0, (255, 255, 255))
#    cv2.rectangle(display_image, point1, point2, (255, 255, 255))

  cv2.imshow('e2', grey_image)

#  box_areas = []
#  for box in bounding_box_list:
#    box_width = box[right][0] - box[left][0]
#    box_height = box[bottom][0] - box[top][0]
#    box_areas.append( box_width * box_height )

#  average_box_area = 0.0
#  if len(box_areas): average_box_area = float( sum(box_areas) ) / len(box_areas)

#  trimmed_box_list = []
#  for box in bounding_box_list:
#    box_width = box[right][0] - box[left][0]
#    box_height = box[bottom][0] - box[top][0]
#    if (box_width * box_height) > average_box_area*0.1: trimmed_box_list.append( box )

#  bounding_box_list = merge_collided_bboxes( trimmed_box_list )
#  for box in bounding_box_list:
#    cv2.rectangle(display_image, box[0], box[1], (255, 0, 0))
  if cv2.waitKey(5) == 27:
    break
cv2.destroyAllWindows()
