import cv2
from .base import stream
import numpy as np


class WebCamSource(stream):

    def __init__(self):
        self.cap = cv2.VideoCapture(0)

    
    def read(self) -> np.ndarray:

            ret, frame = self.cap.read()
            if not ret:
                print("unable to capture frame")
                return None
            
            return frame

    
    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()