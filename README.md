# Bullseye

A Raspberry Pi 5 desktop turret that detects a human hand with a real neural network,
rotates a servo to center it in frame, locks on with red targeting eyes, fires a
visible laser, and plays a custom voice/laser sound sequence.

---

## Why I built this

I built Bullseye because I wanted to test my 3D modeling skills and grow as a hardware
creator. I thought turrets were cool, and I wanted a project that combined CAD, embedded
electronics, computer vision, and audio into one build I could actually demo.

---

## What it does (the sequence)

1. Sits idle, scanning slowly side to side, white eyes searching.
2. Sees your hand → eyes pop alert, "I see you" plays.
3. Servo rotates to center your hand in frame.
4. When centered → LOCK: eyes turn red and pulsing, laser turns on, voice line
   "I've got you in my sights" plays followed by a laser firing sound.
5. While the audio plays, the whole robot freezes - servo silent, eyes locked red.
6. When the audio finishes, normal tracking resumes. Move far away to break the lock.

---

## Hardware

- Raspberry Pi 5 (with the official 27 W USB-C supply recommended)
- USB webcam (any UVC class - I used a GEMBIRD "W1")
- USB-powered speaker (plug-and-play)
- **SG90 hobby servo** - mounted as the yaw base under the head. It's small,
  cheap, and has just enough torque for a light 3D-printed head. If you make
  the head heavy, counterweight the back, or swap to an MG996R.
- ILI9341 3.2" SPI LCD (320x240)
- Laser diode module (3-pin: VCC / GND / signal)
- **Momentary push button** - wired to GPIO26 and GND. Used for BOTH safe
  shutdown AND boot, no terminal needed. See assembly steps below.
- ~1000 µF capacitor across servo power+ground recommended for stability
- Jumper wires
- 3D-printed chassis (see cad/ for files)

---

## Wiring

See [wiring.md](wiring.md) for the full ASCII block diagram and a note on common
ground. A `wiring.png` schematic will be added in a future update.

### LCD (ILI9341, SPI) - 8 wires, no touch panel used

| LCD pin | Pi pin           |
|---------|------------------|
| VCC     | 3.3 V (pin 1)    |
| GND     | GND (pin 6)      |
| CS      | GPIO8 (pin 24)   |
| RESET   | GPIO25 (pin 22)  |
| DC      | GPIO24 (pin 18)  |
| MOSI    | GPIO10 (pin 19)  |
| SCK     | GPIO11 (pin 23)  |
| LED     | 3.3 V (pin 17)   |

### Servo (SG90)

| Wire (colour)   | Goes to                                  |
|-----------------|------------------------------------------|
| Signal (orange) | GPIO18 (pin 12) - hardware PWM channel 2 |
| Power (red)     | 5 V (Pi pin 2/4, with cap if available)  |
| Ground (brown)  | GND (any Pi GND pin)                     |

### Laser module (3-pin)

| Laser pin | Goes to            |
|-----------|--------------------|
| + (VCC)   | 3.3 V or 5 V on Pi |
| - (GND)   | GND on Pi          |
| S (signal)| GPIO17 (pin 11)    |

### Shutdown / boot button

- One leg to GPIO26 (pin 37)
- Other leg to GND (pin 39)

### USB ports

USB camera and USB speaker plugged directly into the Pi.

---

## Assembly Guide

This is what I did to physically put Bullseye together. Read the wiring tables first.

### Step 1 - Print the chassis

Print all parts from cad/. The chassis is two main pieces:
- A fixed **BASE** that holds the Pi, the wiring, and bolts the servo down.
- A rotating **HEAD** that mounts on the SG90's horn and carries the LCD, camera,
  and laser, all pointing forward.

### Step 2 - Mount the SG90 servo into the base

The SG90 is what makes the robot pan left and right (it has NO up/down axis -
that's intentional; the pupils on the LCD handle vertical movement).

- Drop the servo into the slot in the base so the shaft points straight up.
- Screw it down firmly through the SG90's mounting flanges. The body must NOT
  move; only the horn on top should rotate.
- Pick a horn from the SG90's accessory bag. Press it onto the spline lightly
  (don't push it on hard yet - we'll align it).

### Step 3 - Mount the head onto the servo horn

- Screw or hot-glue the chosen horn into the pocket on the underside of the head.
- Now place the head onto the SG90 spline so it's roughly facing forward when
  the servo is at its center.
- Once aligned, secure the horn with the small screw that came with the SG90
  (in the accessory bag) - this is what stops the head popping off when it spins.
  Almost everyone forgets this screw. Don't.

### Step 4 - Mount the camera, LCD, and laser on the head

All three go on the FRONT of the head, facing forward:
- LCD in its frame slot (eyes facing out).
- Camera mounted above or beside the LCD, pointing forward.
- Laser screwed in next to the camera so its dot lands near the center of
  what the camera sees. Eyeball this - you can sight it later by running
  `laser_test.py` and adjusting until the dot is centered in the camera feed.

### Step 5 - Run the wires through the head into the base

Bundle the LCD ribbon + camera USB + laser wires together and route them down
past the servo shaft into the base. **Leave a loose loop of slack** so the
head can pan a full ~140 degrees without pulling on the cables. Tight cables
will fight the servo and burn it out.

### Step 6 - Wire to the Pi (per the wiring tables above)

Connect the LCD, servo, laser, and shutdown button to the Pi's GPIO pins.
USB camera and USB speaker go into Pi USB ports.

### Step 7 - Install and wire the power button

This is the cleanest part of the build - you never have to type a shutdown
command or yank power again.

- Pick a momentary push button (the four-leg tactile kind is fine).
- Drill or print a hole in the side of the base where you want the button.
- Wire one leg of the button to **GPIO26 (physical pin 37)** on the Pi.
- Wire any leg on the OTHER side of the button to a **GND pin** (pin 39 is
  right next to GPIO26 and convenient).
- IMPORTANT: on a 4-leg tactile button, the two legs on the same side are
  permanently connected. You must wire across the gap (diagonal), not two
  legs on the same side.

How the button works once configured:
- **Pi is OFF → press button → Pi boots up** (and Bullseye starts on its own
  via the systemd user service). This is a built-in GPIO26 hardware feature.
- **Pi is RUNNING → press button → clean kernel shutdown**, triggered by the
  `dtoverlay=gpio-shutdown,gpio_pin=26` line in config.txt. Wait for the
  green LED to stop blinking, then it's safe to cut power.

Result: power flow becomes "press to turn on, press to turn off." No SSH,
no keyboard, no risk of SD card corruption from yanked power.

### Step 8 - Balance the head

The LCD + camera + laser all sit on the front of the head, so the head is
front-heavy by default. If the SG90 strains, hums, or droops:
- Tape a counterweight (coins, a small bolt, etc.) to the BACK of the head
  behind the servo shaft until it sits roughly level.
- The code already auto-relaxes the servo between moves to ease the load,
  but mechanical balance is still the best fix.

---

## /boot/firmware/config.txt additions

Add these lines (the project depends on each):

```
dtparam=spi=off
dtoverlay=spi0-0cs
dtoverlay=pwm
dtoverlay=gpio-shutdown,gpio_pin=26
usb_max_current_enable=1
```

---

## /boot/firmware/cmdline.txt additions

Append this to the existing single line (with a space before it). It tells usb-storage
to ignore the webcam, which on some cheap cams claims interface 0 and blocks uvcvideo
from binding. Replace `1908:1331` with your camera's `lsusb` ID if different.

```
usb-storage.quirks=1908:1331:i
```

---

## System dependencies

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-opencv python3-lgpio python3-gpiozero python3-pil \
                    python3-numpy mpv mpg123 v4l-utils ffmpeg
```

---

## Python dependencies

```bash
pip install onnxruntime adafruit-circuitpython-rgb-display adafruit-blinka \
            rpi-hardware-pwm --break-system-packages
```

---

## Project layout

Place all the files in `/home/<user>/` (the scripts read paths relative to themselves):

```
/home/<user>/ai_robot_boot.py
/home/<user>/vision_debug.py
/home/<user>/servo_test.py
/home/<user>/laser_test.py
/home/<user>/palm_detection.onnx
/home/<user>/audio/detect.mp3
/home/<user>/audio/lockon_seq.mp3
```

---

## First-run tests (do these BEFORE running the robot)

1. Test the servo on its own:
   ```bash
   python3 servo_test.py
   ```

2. Test the laser on its own:
   ```bash
   python3 laser_test.py
   ```

3. Test the LCD and detector together (live view, needs monitor):
   ```bash
   python3 vision_debug.py
   ```

4. Run the full robot:
   ```bash
   python3 ai_robot_boot.py
   ```

---

## Run on boot (headless, no keyboard/monitor/mouse)

Copy the service file, enable lingering, and enable + start the service:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/airobot.service ~/.config/systemd/user/airobot.service
loginctl enable-linger $USER
systemctl --user daemon-reload
systemctl --user enable airobot.service
systemctl --user start airobot.service
journalctl --user -u airobot.service -f    # live logs
```

To stop / disable:

```bash
systemctl --user stop airobot.service
systemctl --user disable airobot.service
```

---

## Power button behavior

Wired button shorts GPIO26 to GND momentarily.
- Pi off, press button → boots up, robot auto-starts.
- Pi on, press button → kernel does a clean shutdown.

---

## Troubleshooting (from real debugging during the build)

- **Camera detected by lsusb but no /dev/videoN**: usb-storage is claiming it.
  The cmdline.txt quirk above fixes this. After editing, `sudo reboot`.

- **Camera drops after running a while**: USB power. Use the official 27 W Pi 5 supply,
  add `usb_max_current_enable=1`, or put the camera on a powered USB hub.

- **Servo buzzing/ringing after a few seconds**: it's straining against a top-heavy load.
  Counterweight the back of the body, or the code already auto-relaxes the servo
  between moves to reduce this.

- **"GPIO busy"**: the service or an old run is still holding the pin.
  ```bash
  systemctl --user stop airobot.service && pkill -f ai_robot_boot.py
  ```

---

## CAD

Files in `cad/` are FDM-printable. Mount the head (LCD + camera + laser) on the SG90's
horn; bolt the SG90 body into the base; keep the camera and laser aligned forward so
the laser dot lands inside the camera frame.

---

## Credits

Neural detector: MediaPipe Palm Detection (ONNX export by PINTO0309).
