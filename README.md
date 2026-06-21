# security-camera
CV powered security camera. Ultimate goal is to get it running on a raspberry pi

overall goal
⏺ Security camera project using YOLOv8 pretrained on COCO (no training needed —
  person, car, etc. already built in). Build infrastructure on top: ByteTrack
  for persistent cross-frame identity, zone/tripwire alerts, clip recording on
  detection, and potentially re-ID down the line. Webcam or RTSP stream as
  input. The model is just the detector underneath — the real project is the
  tooling around it. Start tonight with tracking on a live feed.
