#!/usr/bin/env python3
"""
AI Tracking Robot - HEADLESS (Raspberry Pi 5)   [neural detection]
==================================================================
- Neural hand detection (ONNX palm detector) - no calibration
- Servo (GPIO18 hardware PWM) actively centers the target; structured
  scan-sweep when the target is lost
- LCD eyes track smoothly (NO blinking); red targeting state holds
- Lock-on plays one seamless sound (voice + laser merged)

Files needed here: palm_detection.onnx, detect.mp3, lockon_seq.mp3
Install once: pip install onnxruntime --break-system-packages
"""
import cv2, numpy as np, os, threading, time, math, signal, subprocess, shutil
import onnxruntime as ort
from rpi_hardware_pwm import HardwarePWM
from gpiozero import LED
import board, digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

HERE        = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE  = os.path.join(HERE, "palm_detection.onnx")
DETECT_FILE = os.path.join(HERE, "detect.mp3")        # "I see you" on first sight
SEQ_FILE    = os.path.join(HERE, "lockon_seq.mp3")    # voice + laser, merged

MIN_SCORE = 0.55      # detection confidence (raise = stricter)

# ---------------- neural detector ----------------
sess = ort.InferenceSession(MODEL_FILE, providers=["CPUExecutionProvider"])
IN_NAME = sess.get_inputs()[0].name
print("Neural palm detector loaded", flush=True)

def detect_hand(frame):
    h, w = frame.shape[:2]
    img = cv2.resize(frame, (192, 192))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    inp = (img.astype(np.float32) / 255.0)[None].transpose(0, 3, 1, 2)
    rows = sess.run(None, {IN_NAME: inp})[0]
    if rows.shape[0] == 0:
        return None
    best = rows[np.argmax(rows[:, 0])]
    score, bx, by, bs = float(best[0]), float(best[1]), float(best[2]), float(best[3])
    if score < MIN_SCORE:
        return None
    return (int(bx * w), int(by * h), int(bs * max(w, h)))

# ---------------- shared state ----------------
state_lock = threading.Lock()
shared = {"locked": False, "hx": 0.0, "hy": 0.0, "running": True}
def clamp(v, lo, hi): return max(lo, min(hi, v))

# ---------------- servo + laser ----------------
servo_pwm = HardwarePWM(pwm_channel=2, hz=50)
servo_pwm.start(0)
def set_angle(a):
    a = clamp(a, 0, 180)
    servo_pwm.change_duty_cycle(2.5 + a / 18.0)
laser = LED(17)

# ---------------- sound (only ONE clip can play at a time) ----------------
_PLAYER = (["mpv", "--no-video", "--really-quiet"] if shutil.which("mpv")
           else ["mpg123", "-q"])
audio_lock  = threading.Lock()
current_proc = None
current_is_lockon = False        # True only while the lockon sequence is playing

def play_audio(path, interrupt=False):
    """Plays a sound file. Enforces single-track audio:
       - if something is already playing and interrupt=False -> SKIP (no overlap)
       - if something is already playing and interrupt=True  -> stop it, play this one
    """
    global current_proc, current_is_lockon
    with audio_lock:
        if current_proc is not None and current_proc.poll() is None:
            if not interrupt:
                return
            current_proc.terminate()
            try: current_proc.wait(timeout=0.3)
            except Exception: pass
        if os.path.exists(path):
            current_proc = subprocess.Popen(
                _PLAYER + [path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current_is_lockon = (path == SEQ_FILE)

def lockon_is_playing():
    """True iff the lockon sequence audio is still playing right now."""
    global current_is_lockon
    with audio_lock:
        if not current_is_lockon:
            return False
        if current_proc is None or current_proc.poll() is not None:
            current_is_lockon = False
            return False
        return True

# ---------------- clean shutdown ----------------
def stop(*_):
    with state_lock:
        shared["running"] = False
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

# ======================================================================
#  FACE THREAD - smooth tracking eyes, no blinking
# ======================================================================
def face_loop():
    cs_pin    = digitalio.DigitalInOut(board.CE0)
    dc_pin    = digitalio.DigitalInOut(board.D24)
    reset_pin = digitalio.DigitalInOut(board.D25)
    spi = board.SPI()
    disp = ili9341.ILI9341(spi, cs=cs_pin, dc=dc_pin, rst=reset_pin,
                           baudrate=24000000, rotation=90)
    W, H = (disp.height, disp.width) if disp.rotation % 180 == 90 else (disp.width, disp.height)
    eye_r, pupil_r = 55, 22
    travel = eye_r - pupil_r - 6
    cy = H // 2
    eye_cx = [W // 2 - 80, W // 2 + 80]
    mid_x = (eye_cx[0] + eye_cx[1]) // 2
    disp_hx = disp_hy = 0.0
    img = Image.new("RGB", (W, H)); draw = ImageDraw.Draw(img)

    while True:
        with state_lock:
            if not shared["running"]: break
            locked = shared["locked"]
            hx, hy = shared["hx"], shared["hy"]
        now = time.time()

        # smooth, intentional pupil motion (no blinking, no jitter)
        disp_hx += 0.22 * (hx - disp_hx)
        disp_hy += 0.22 * (hy - disp_hy)

        draw.rectangle((0, 0, W, H), fill=(0, 0, 0))

        if locked:
            pulse = 0.5 + 0.5 * math.sin(now * 8.0)
            inten = int(150 + 105 * pulse)
            red   = (inten, 0, 0)
            glow  = (int(inten * 0.30), 0, 0)
            for ex in eye_cx:
                draw.ellipse((ex-eye_r-12, cy-eye_r-12, ex+eye_r+12, cy+eye_r+12), fill=glow)
                draw.ellipse((ex-eye_r, cy-eye_r, ex+eye_r, cy+eye_r), fill=red)
                px = ex + disp_hx * (eye_r * 0.45)
                py = cy + disp_hy * (eye_r * 0.45)
                ring = int(13 + 4 * pulse)
                draw.ellipse((px-ring, py-ring, px+ring, py+ring), outline=(255,255,255), width=2)
                draw.line((px-ring-7, py, px+ring+7, py), fill=(255,255,255), width=2)
                draw.line((px, py-ring-7, px, py+ring+7), fill=(255,255,255), width=2)
                draw.ellipse((px-3, py-3, px+3, py+3), fill=(255,255,255))
                if ex < mid_x:
                    draw.line((ex-eye_r, cy-eye_r-16, ex+eye_r, cy-eye_r-1), fill=red, width=9)
                else:
                    draw.line((ex-eye_r, cy-eye_r-1, ex+eye_r, cy-eye_r-16), fill=red, width=9)
        else:
            for ex in eye_cx:
                draw.ellipse((ex-eye_r, cy-eye_r, ex+eye_r, cy+eye_r), fill=(255,255,255))
                px = ex + disp_hx * travel
                py = cy + disp_hy * travel
                draw.ellipse((px-pupil_r, py-pupil_r, px+pupil_r, py+pupil_r), fill=(20,20,20))

        disp.image(img); time.sleep(0.04)

    draw.rectangle((0, 0, W, H), fill=(0, 0, 0)); disp.image(img)

# ======================================================================
#  MAIN LOOP
# ======================================================================
def main():
    current_angle = 90.0
    set_angle(current_angle); time.sleep(0.5)
    laser.off()

    # ---- tuning ----
    DIRECTION   = -1      # turns TOWARD the hand (flip to 1 if it turns away)
    DEADZONE    = 55      # px from center: inside this the servo HOLDS STILL (wider = less work)
    GAIN        = 0.05    # steering strength (lower = gentler moves, less load spike)
    MAX_STEP    = 4.0     # max degrees per frame (smaller = smoother, less peak current)
    SEARCH_STEP = 1.8     # scan sweep speed when target is lost
    SMOOTH      = 0.4     # target-position smoothing
    GRACE       = 8       # keep "found" this many frames through brief misses
    PERSIST     = 2       # frames to confirm a new detection
    LOCK_IN     = 70      # within this px of center -> can engage LOCK (wider = locks sooner)
    LOCK_FRAMES = 4       # centered this many frames -> servo LOCKS (frozen)
    UNLOCK_DIST = 160     # hand must move THIS far from center to break lock (stickier)
    UNLOCK_FRAMES = 14    # ...AND stay that far for this many frames
    RED_HOLD    = 3.5     # red eyes stay at least this many seconds
    SERVO_MIN, SERVO_MAX = 25, 155   # narrower range = less leverage on a heavy head
    MOVE_HOLD   = 0.06    # seconds to hold a move before relaxing (rests the servo)
    MIN_MOVE_DELTA = 0.8  # don't bother commanding moves smaller than this many degrees

    def open_camera():
        for idx in [0, 1, 2, 3]:
            c = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if c.isOpened():
                c.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ok, _ = c.read()
                if ok:
                    print(f"Camera opened at /dev/video{idx}", flush=True)
                    return c
            c.release()
        return None

    cap = None
    fail_count = 0
    smooth_cx = smooth_cy = None
    seen_streak = miss = 0
    found = locked = False
    prev_found = prev_locked = False
    center_frames = offcenter_frames = 0
    search_dir = 1
    lock_hold_until = 0.0
    last_print = 0.0
    last_move_at = 0.0       # when we last commanded the servo (for auto-relax)
    last_commanded = current_angle

    try:
        while True:
            with state_lock:
                if not shared["running"]: break
            if cap is None:
                cap = open_camera()
                if cap is None:
                    print("No camera found - waiting...", flush=True); time.sleep(1.0); continue

            ok, frame = cap.read()
            if not ok:
                fail_count += 1
                if fail_count >= 10:
                    print("Camera dropped - reopening...", flush=True)
                    cap.release(); cap = None; time.sleep(1.0); fail_count = 0
                else:
                    time.sleep(0.1)
                continue
            fail_count = 0

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2

            now = time.time()
            seq_playing = lockon_is_playing()

            det = detect_hand(frame)
            if det is not None:
                rcx, rcy, _ = det
                smooth_cx = rcx if smooth_cx is None else SMOOTH*rcx + (1-SMOOTH)*smooth_cx
                smooth_cy = rcy if smooth_cy is None else SMOOTH*rcy + (1-SMOOTH)*smooth_cy
                seen_streak += 1; miss = 0
                if seen_streak >= PERSIST: found = True
            else:
                miss += 1; seen_streak = 0
                if miss > GRACE:
                    found = False; smooth_cx = smooth_cy = None

            hx_norm = hy_norm = 0.0
            err = 0

            if seq_playing:
                # ===== TOTAL FREEZE while the lock-on sequence is playing =====
                # servo off, eyes stay red, lock can't change. Pupils may still
                # track the hand if visible (for a more "alive" red-stare).
                locked = True
                lock_hold_until = now + RED_HOLD
                center_frames = offcenter_frames = 0
                servo_pwm.change_duty_cycle(0)
                if found and smooth_cx is not None:
                    err = smooth_cx - cx
                    hx_norm = clamp(err / cx, -1, 1)
                    hy_norm = clamp((smooth_cy - cy) / cy, -1, 1)

            elif found and smooth_cx is not None:
                err = smooth_cx - cx
                hx_norm = clamp(err / cx, -1, 1)
                hy_norm = clamp((smooth_cy - cy) / cy, -1, 1)

                # ----- lock state machine (hysteresis) -----
                if abs(err) < LOCK_IN:
                    center_frames += 1; offcenter_frames = 0
                else:
                    center_frames = 0
                    if abs(err) > UNLOCK_DIST:
                        offcenter_frames += 1
                    else:
                        offcenter_frames = 0

                if not locked and center_frames >= LOCK_FRAMES:
                    locked = True; lock_hold_until = now + RED_HOLD
                if locked and now >= lock_hold_until and offcenter_frames >= UNLOCK_FRAMES:
                    locked = False

                # ----- servo: FROZEN while locked, gentle proportional otherwise -----
                if locked:
                    servo_pwm.change_duty_cycle(0)
                elif abs(err) > DEADZONE:
                    step = clamp(err * GAIN, -MAX_STEP, MAX_STEP)
                    target_angle = clamp(current_angle - DIRECTION * step, SERVO_MIN, SERVO_MAX)
                    if abs(target_angle - last_commanded) >= MIN_MOVE_DELTA:
                        current_angle = target_angle
                        set_angle(current_angle)
                        last_commanded = current_angle
                        last_move_at = now
                    elif now - last_move_at > MOVE_HOLD:
                        servo_pwm.change_duty_cycle(0)
                else:
                    # in deadzone -> relax (mechanical hold by friction; no hum, no load)
                    servo_pwm.change_duty_cycle(0)
            else:
                # target fully lost -> hold red briefly, then structured scan sweep
                if not (locked and now < lock_hold_until):
                    locked = False
                center_frames = offcenter_frames = 0
                target_angle = current_angle + SEARCH_STEP * search_dir
                if target_angle <= SERVO_MIN:
                    target_angle = SERVO_MIN; search_dir = 1
                elif target_angle >= SERVO_MAX:
                    target_angle = SERVO_MAX; search_dir = -1
                if abs(target_angle - last_commanded) >= MIN_MOVE_DELTA:
                    current_angle = target_angle
                    set_angle(current_angle)
                    last_commanded = current_angle
                    last_move_at = now
                elif now - last_move_at > MOVE_HOLD:
                    servo_pwm.change_duty_cycle(0)
                hx_norm = 0.6 * search_dir
                hy_norm = 0.0

            # events: only ONE audio clip plays at a time.
            # - detect plays only if no clip is currently playing
            # - lockon interrupts detect (lock-on is more important)
            if found and not prev_found:
                play_audio(DETECT_FILE, interrupt=False)
            if locked and not prev_locked:
                play_audio(SEQ_FILE, interrupt=True)
            laser.on() if locked else laser.off()
            prev_found, prev_locked = found, locked

            with state_lock:
                shared["locked"] = locked
                shared["hx"], shared["hy"] = hx_norm, hy_norm

            if now - last_print > 1.0:
                print(f"found={found} locked={locked} err={int(err)} "
                      f"angle={int(current_angle)} det={'Y' if det is not None else 'n'}",
                      flush=True)
                last_print = now
    finally:
        with state_lock:
            shared["running"] = False
        if cap: cap.release()
        servo_pwm.stop(); laser.off()

if __name__ == "__main__":
    face_thread = threading.Thread(target=face_loop, daemon=True)
    face_thread.start()
    main()
    face_thread.join(timeout=2)
