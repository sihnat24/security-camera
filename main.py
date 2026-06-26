from detectors import yolo
from zones import zone
from sources.webcam import WebCamSource
from sources.raspberry import RaspberrySource
import cv2
import numpy as np
from datetime import datetime
from collections import deque
import os

PRE_BUFFER_SECONDS = 20
WATCHED_CLASSES = {0,15,16} #person, dog, cat classes
os.makedirs("clips", exist_ok=True)

#source setup
#cam = RaspberrySource("http://192.168.1.220:8000/stream")
cam = WebCamSource()
FPS = cam.fps
buff = deque(maxlen=FPS * PRE_BUFFER_SECONDS)




#detector setup 
detector = yolo.yoloDetector()

p_pts = np.array([[213, 160], [427, 160], [427, 320], [213, 320]])
w_pts = np.array([ #POINTS ARE CONNECTED SEQUENTIALLY
      [500,  300],   # top-left
      [1500, 300],   # top-right
      [1500, 1200],  # bottom-right
      [500,  1200],  # bottom-left
  ], dtype=np.int32)

area = zone.Zone(w_pts, "dev zone")


#logging and recording varaibles
log = open("events.log","w")
loiter_thresh = 10 #10 seconds
recording = False



zone_state = {}

while True:
    frame = cam.read()
    if frame is None:
        print("cannot capture frame")
        continue

    results = detector.track(frame)

    trig = []
    
    if results[0].boxes.id is not None:
        for track_box, track_id, track_class in zip(results[0].boxes.xyxy, results[0].boxes.id, results[0].boxes.cls): #check if any boxes are in the area
            
            track_id = int(track_id) #turn tensor into int to prevent repeat fires

            if int(track_class) not in WATCHED_CLASSES:
                continue

            currently_inside = area.check(track_box)
            was_inside, entry_time = zone_state.get(track_id, (False, None))
            
            #STATE UPDATES - EXIT / ENTRY
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if currently_inside and not was_inside:
                log.write(f"{ts}, ENTRY, track {track_id}, zone {area.name}\n")
                zone_state[track_id] = (currently_inside, datetime.now())

            elif was_inside and not currently_inside:
                log.write(f"{ts}, EXIT, track {track_id}, zone {area.name}\n")
                zone_state[track_id] = (False, None)

                if recording:
                    writer.release() #stop recording
                    recording = False
            else:
                zone_state[track_id] = (currently_inside, entry_time) #did not cross, keep the same


            #LOITERING CHECKS
            if currently_inside and was_inside and (datetime.now() - entry_time).seconds > loiter_thresh and not recording:
    
                #if loitering, dump queue and record until object leaves
                recording = True
                f_name = f"clips/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
                writer = cv2.VideoWriter(f_name, cv2.VideoWriter_fourcc(*'mp4v'),FPS, cam.frame_size)
                
                for buffered_frame in buff: #dump buffer
                    writer.write(buffered_frame)

            log.flush()
            trig.append(currently_inside)
     
    detect_frame = results[0].plot()
    area.draw(detect_frame, any(trig)) #mutate frame 
    
    #log in buffer, and potentially writer
    buff.append(detect_frame)
    if recording: #add to 
        writer.write(detect_frame)

    cv2.imshow('feed',detect_frame)
    
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

#close the camera and log file
log.close()
cam.close()