from detectors import yolo
from sources import webcam
import cv2


cam = webcam.WebCamSource()
detector = yolo.yoloDetector()

while True:
    frame = cam.read()
    if frame is not None:
        results = detector.track(frame)

    detect_frame = results[0].plot()
    cv2.imshow('feed',detect_frame)
    print(results[0].boxes.id)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.close()