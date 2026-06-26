# Security Camera Project — Claude Context

## What This Is

A learning project building surveillance tooling on top of YOLOv8 (COCO pretrained).
The model is just the detector — the real work is the infrastructure around it:
persistent identity across frames, spatial alerts, event recording, and eventually re-ID.

**Input:** webcam or RTSP stream
**Detector:** YOLOv8 (no training needed — person/car/etc. already in COCO)
**Tracker:** ByteTrack (cross-frame identity)
**Planned layers:** zone/tripwire alerts → clip recording on detection → re-ID

---

## This Is a Learning Project

Every decision must be explained. No magic. When we choose a library, algorithm,
architecture, or data structure, we document WHY — not just what it does, but why
it beats the alternatives for this specific use case.

**Format for decisions (use in code comments and commit messages):**
```
DECISION: [what we chose]
WHY: [reason — tradeoffs considered, alternatives rejected]
ALTERNATIVES: [what we didn't pick and why not]
```

This applies to: tracker choice, buffer strategy, zone representation,
threading model, file format for clips, alert logic, etc.

---

## Key Design Decisions (Running Log)

### Detector: YOLOv8 (COCO pretrained)
- **Why:** COCO has 80 classes including person, car, bicycle — covers security use cases
- **Why not train:** no labeled data, no GPU budget, pretrained generalizes well enough
- **Why YOLOv8 over v5/v9:** Ultralytics API is clean, active maintenance, easy ByteTrack integration

### Tracker: ByteTrack
- **Why:** handles occlusion better than SORT by using low-confidence detections in
  the second association pass — critical for real-world footage where people
  partially disappear behind objects
- **Why not DeepSORT:** adds re-ID embedding model (more compute, more complexity)
  — save that for later phase
- **Why not SORT:** drops tracks on occlusion, IDs re-assign — defeats the purpose
  of persistent identity

---

## Claude's Role

Claude is a **teacher and guide**, not a code author. The user writes the code.
Claude explains concepts, answers questions, points out bugs, and suggests what to
try next — but does NOT write implementation code unprompted. Snippets for
explanation are fine; full implementations are not.

---

## Architecture Principles

1. **Explain before implement.** Before writing a module, write a comment block
   explaining what it does, why it exists, and what the interface is.
2. **No black boxes.** If a library does something non-obvious, comment it.
3. **Incremental.** Each session adds one working layer. Don't scaffold ahead.
4. **Correctness over performance** (at this stage). Get it right, then optimize.

---

## Stretch Goals

### C++ Port (hot path / Pi optimization)
- **Why it's on the list:** User is too dependent on a pure Python ecosystem — C++ exposure
  is valuable SWE growth regardless of domain
- **What to port:** not everything — just the hot path once profiling identifies it.
  Likely candidates: frame capture loop, zone/tripwire math, pre/post-processing around YOLO
- **What to learn along the way:**
  - Memory layout of images (what numpy arrays actually are in memory)
  - Cost of copying frames (why it matters at 30fps)
  - ONNX Runtime — standard way to run YOLO in C++ without Ultralytics
  - Why real-time systems avoid heap allocation in the hot loop
- **Why not now:** Python first — learn the concepts, find the bottleneck, then port with purpose.
  Premature optimization obscures what's actually slow.
- **Pi relevance:** AI hat offloads model inference; C++ gains matter most in the surrounding
  logic and frame handling, not the model itself

---

## Current File Structure

```
main.py                  # entry point: read frame → detect → plot → display
sources/
  base.py                # abstract base class `stream` (ABC) — enforces read()/close() on all sources
  webcam.py              # WebCamSource: wraps cv2.VideoCapture(0), returns np.ndarray frames
detectors/
  yolo.py                # yoloDetector: loads yolov8n.pt, wraps model(frame) → Results
requirements.txt         # opencv-python, ultralytics, lapx
```

**Main loop pattern:**
```
cam.read() → detector.detect(frame) → results[0].plot() → cv2.imshow()
```
`results[0].plot()` is a Ultralytics helper that draws bounding boxes + labels directly on a copy of the frame.

---

## Session Log

### Session 1 (2026-06-21)
- **Goal:** webcam → YOLO detection → live display with bounding boxes
- **Achieved:** working pipeline end-to-end — `main.py` reads frames from webcam, runs YOLOv8n inference, renders annotated frame in an OpenCV window, `q` to quit
- **Built:**
  - `sources/base.py` — ABC enforcing `read()`/`close()` interface on all future sources (webcam, RTSP, file)
  - `sources/webcam.py` — `WebCamSource` wrapping `cv2.VideoCapture(0)`
  - `detectors/yolo.py` — `yoloDetector` loading `yolov8n.pt` via Ultralytics
  - `main.py` — the loop tying it together
- **Model:** `yolov8n` (nano) — smallest/fastest YOLOv8 variant, good for iteration; upgrade to `yolov8s` or larger if accuracy matters
- **Next session:** add ByteTrack (`model.track()` instead of `model()`) to get persistent track IDs across frames

### Session 3 (2026-06-23)
- **Goal:** zone detection — draw a polygon on the frame, trigger when a person enters it
- **Achieved:** working zone pipeline — `zones/zone.py` with `Zone` class, polygon drawn on frame, red when triggered green when not, `pointPolygonTest` for inside/outside check
- **Built:**
  - `zones/zone.py` — `Zone` class with `draw(frame, triggered)` (mutates in place) and `check(box) → bool`
  - `main.py` updated — instantiates `Zone`, loops over `results[0].boxes.xyxy`, calls `check` on each, passes `any(trig)` to `draw`
- **Key decisions:**
  - Bottom-center `(x1+x2)//2, y2` as foot point — tests where person stands on ground plane, not body center
  - Zone drawn on `detect_frame` (post-plot copy), not raw frame — so boxes and zone are on same image
  - `draw` mutates in place — no copy per zone, scales to multiple zones cleanly
  - Points must be in perimeter order (clockwise/counterclockwise) — sequential connection by `polylines` causes hourglass if out of order
- **Next session candidates:** event logic (enter/exit detection), clip recording on trigger, multi-zone support, dwell time tracking
- **Next session goal:** event transitions (IDLE → TRIGGERED → RECORDING → COOLDOWN → IDLE) + ring buffer recorder. `deque(maxlen=fps*N)` holds rolling pre-trigger frames; on zone entry dump buffer + keep writing; on exit + cooldown write clip to disk. Two pieces: event state machine in `main.py`, ring buffer + `cv2.VideoWriter` in new `recorder.py`.

### Session 4 (2026-06-25)
- **Goal:** wire Raspberry Pi camera as a remote source over LAN
- **Achieved:** Pi streams MJPEG over HTTP; laptop pulls frames via `cv2.VideoCapture(url)` and runs YOLO + zone detection unchanged
- **Built:**
  - `sources/ip_camera.py` — `RaspberrySource(stream)` takes a URL, wraps `cv2.VideoCapture(url)`, identical `read()`/`close()` interface to `WebCamSource`
  - Pi runs `pi_camera_node.py` (Flask + Picamera2, port 8000) — captures RGB888 frames, JPEG-encodes, serves as `multipart/x-mixed-replace` MJPEG stream
- **Key decisions:**
  - `cv2.VideoCapture` handles MJPEG boundary parsing and JPEG decode natively — no custom HTTP or frame parsing needed
  - URL passed as constructor arg (`RaspberrySource(url)`) not hardcoded — keeps class reusable for any MJPEG source
  - Heavy ML (YOLO, ByteTrack) stays on laptop; Pi is capture-only — no inference on Pi
- **Hardware:** Raspberry Pi 5, Pi Camera V2 (IMX219), CSI ribbon cable — cable is fragile, reseat if stream drops
- **Pi access:** `ssh sev@192.168.1.220`, start server: `python3 ~/security_camera/pi_camera_node.py`; stream URL: `http://192.168.1.220:8000/stream`
- **Known gotcha:** camera hardware times out if CSI cable loses contact — restart Picamera2/Flask after reseating
- **Next session goal:** event transitions (IDLE → TRIGGERED → RECORDING → COOLDOWN → IDLE) + ring buffer recorder (same as Session 3 goal — still pending)

### Session 5 (2026-06-26)
- **Goal:** event logging, loitering detection, and clip recording pipeline
- **Achieved:** full pipeline from detection → zone state → loitering trigger → pre-buffer dump → clip to disk, with structured event log
- **Built:**
  - `events.log` — append-mode structured log: timestamp, event type (ENTRY/EXIT/LOITER), track ID, zone name
  - Ring buffer — `deque(maxlen=FPS * PRE_BUFFER_SECONDS)` rolling window of annotated frames, always running
  - Loitering detection — per-track dwell time via `zone_state` dict storing `(inside: bool, entry_time: datetime)`, fires when dwell exceeds `loiter_thresh`
  - Clip recording — on loiter trigger: dump ring buffer to `cv2.VideoWriter`, keep writing until EXIT, save to `clips/` as timestamped `.mp4`
  - Class filter — `WATCHED_CLASSES = {0, 15, 16}` (person, cat, dog) — all other COCO classes ignored for zone logic
- **Key decisions:**
  - `zone_state` keyed on `int(track_id)` — tensor keys don't work as dict keys, must cast
  - `trig` list kept separate from `zone_state` — `any(trig)` drives zone color, state dict drives logging; two concerns, both needed
  - Pre-buffer holds annotated frames (post-plot) — clips show bounding boxes and zone overlay, not raw frames
  - Dump blocks main loop briefly (~100-200ms) — acceptable for front door use case, producer-consumer queue deferred
  - Log file opened with `"w"` on startup — fresh log each run; change to `"a"` when persistence across runs is needed
- **Known limitation:** brief display freeze at loiter trigger while buffer dumps to disk; recording itself is correct
- **Next candidates:** producer-consumer writer queue (fix freeze), multi-zone support, cooldown period to prevent re-triggering, dwell time in log entries
