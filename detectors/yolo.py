from ultralytics import YOLO
from ultralytics.engine.results import Results
import numpy as np


class yoloDetector:

    def __init__(self): #yolo26n.pt or yolo11n.pt if below fails
        self.model = YOLO('yolov8n.pt')


    
    def detect(self, frame: np.ndarray) -> Results:
        return self.model(frame)