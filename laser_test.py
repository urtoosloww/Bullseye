#!/usr/bin/env python3
"""
Laser blink test - proves the laser independent of the vision/AI.
Stop the robot first:   systemctl --user stop airobot.service
Run:                    python3 laser_test.py     (Ctrl+C to stop)

If the laser BLINKS 1s on / 1s off  -> laser wiring is fine.
If it never lights                  -> check: laser '+' on 3.3V/5V,
                                       'S' on GPIO17, '-' on GND.
"""
import time
from gpiozero import LED

laser = LED(17)                              # GPIO17
print("Blinking 1s ON / 1s OFF. If it never lights, check wiring/power.")
try:
    while True:
        laser.on();  print("LASER ON");  time.sleep(1)
        laser.off(); print("LASER OFF"); time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    laser.off()
    print("\nstopped")
