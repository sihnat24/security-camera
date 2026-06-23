from detectors import yolo
from zones import zone
from sources import webcam
import cv2
import numpy as np


cam = webcam.WebCamSource()
detector = yolo.yoloDetector()

pts = np.array([ #POINTS ARE CONNECTED SEQUENTIALLY
      [500,  300],   # top-left
      [1500, 300],   # top-right
      [1500, 1000],  # bottom-right
      [500,  1000],  # bottom-left
  ], dtype=np.int32)


area = zone.Zone(pts)

while True:
    frame = cam.read()
    if frame is None:
        print("cannot capture frame")
        continue

    results = detector.track(frame)
    
    trig = []
    for box in results[0].boxes.xyxy: #check if any boxes are in the area
        trig.append(area.check(box))

    detect_frame = results[0].plot()
    area.draw(detect_frame, any(trig)) #mutate the box
    cv2.imshow('feed',detect_frame)
    
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.close()