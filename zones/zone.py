
import cv2
import numpy as np

class Zone:

    def __init__(self, pts):
        self.pts = pts

    
    def draw(self, frame, triggered):
       
        pts = self.pts.reshape((-1, 1, 2))

        isClosed = True

        # Blue color in BGR
        red = (0, 0, 255)
        green = (0,255,0)

        # Line thickness of 2 px
        thickness = 2

        if triggered:
            cv2.polylines(frame, [pts], isClosed, red, thickness)

        else:
            cv2.polylines(frame, [pts], isClosed, green, thickness)

    def check(self, box):
        x1,y1,x2,y2 = box
        pt = (float((x1+x2)//2), float(y2)) #center bottom pt for box of obj being tracked

        contour = self.pts.reshape((-1,1,2)) #(figure out grids, per grid: 1 row, 2 cols)

        #measureDist — False - just care about in/out of box
        #returns +1 in, -1 out, 0 on edge

        result = cv2.pointPolygonTest(contour, pt, measureDist=False)
        return result >= 0
    

        