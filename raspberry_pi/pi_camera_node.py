#this is code run ON the pi to produce the video stream

from flask import Flask, Response
from picamera2 import Picamera2
import cv2

app = Flask(__name__)
cam = Picamera2()
cam.configure(cam.create_video_configuration(main={"size": (640, 480), "format": "RGB888"}))
cam.start()

def frames():
    while True:
        frame = cam.capture_array()
        ok, jpg = cv2.imencode(".jpg", frame)
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                   + jpg.tobytes() + b"\r\n")

@app.route("/stream")
def stream():
    return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

app.run(host="0.0.0.0", port=8000)