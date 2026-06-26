import cv2
from .base import stream
import numpy as np


class RaspberrySource(stream):

    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
            
    def read(self) -> np.ndarray:

            ret, frame = self.cap.read()
            if not ret:
                print("unable to capture frame")
                return None
            
            return frame

    
    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()


    @property
    def fps(self):
        return 30 
    
    @property
    def frame_size(self):
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (w, h)