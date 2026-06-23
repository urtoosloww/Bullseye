#!/usr/bin/env python3
"""
Vision debug v3 - NEURAL hand detection (run on the desktop)
============================================================
Shows what the neural detector sees:
  GREEN box + score = confident hand detection (what the robot tracks)
  GRAY  box + score = seen but below the confidence slider

Slider: min score % - confidence required. Raise if any false positives.
'q' to quit.   No calibration exists anymore - none is needed.
"""
import cv2, numpy as np, os
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
sess = ort.InferenceSession(os.path.join(HERE, "palm_detection.onnx"),
                            providers=["CPUExecutionProvider"])
IN_NAME = sess.get_inputs()[0].name
print("neural palm detector loaded")

def open_cam():
    for idx in [0, 1, 2, 3]:
        c = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if c.isOpened():
            c.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            ok, _ = c.read()
            if ok:
                print(f"camera at /dev/video{idx}"); return c
        c.release()
    return None

cap = open_cam()
if cap is None:
    print("no camera found"); raise SystemExit(1)

cv2.namedWindow("Debug")
def _n(x): pass
cv2.createTrackbar("min score %", "Debug", 55, 95, _n)

while True:
    ok, frame = cap.read()
    if not ok:
        print("camera fail"); break
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    min_score = max(5, cv2.getTrackbarPos("min score %", "Debug")) / 100.0

    img = cv2.resize(frame, (192, 192))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    inp = (img.astype(np.float32) / 255.0)[None].transpose(0, 3, 1, 2)
    rows = sess.run(None, {IN_NAME: inp})[0]

    found = False
    for r in rows:
        score, bx, by, bs = float(r[0]), float(r[1]), float(r[2]), float(r[3])
        if score < 0.30:
            continue
        cx_, cy_ = int(bx * w), int(by * h)
        half = int(bs * max(w, h) / 2)
        good = score >= min_score
        color = (0, 255, 0) if good else (160, 160, 160)
        cv2.rectangle(frame, (cx_-half, cy_-half), (cx_+half, cy_+half), color, 2)
        cv2.putText(frame, f"{score:.2f}", (cx_-half, cy_-half-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if good: found = True

    lbl, lc = ("HAND DETECTED", (0,255,0)) if found else ("nothing", (0,0,255))
    cv2.putText(frame, lbl, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, lc, 2)
    cv2.imshow("Debug", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
