#!/usr/bin/env python3
"""
Servo sweep test - proves the servo independent of the vision/AI.
Stop the robot first:   systemctl --user stop airobot.service
Run:                    python3 servo_test.py     (Ctrl+C to stop)

If the servo SWEEPS back and forth  -> servo hardware is fine.
If it does NOTHING                  -> servo has no POWER (most likely),
                                       or signal wire isn't on GPIO18.
"""
import time
from rpi_hardware_pwm import HardwarePWM

pwm = HardwarePWM(pwm_channel=2, hz=50)      # GPIO18 on the Pi 5
pwm.start(0)
def set_angle(a):
    pwm.change_duty_cycle(2.5 + a / 18.0)

print("Sweeping 0 -> 180 -> 0. If it doesn't move, the servo has no power.")
try:
    while True:
        for a in range(0, 181, 5):
            set_angle(a); print("angle", a); time.sleep(0.04)
        for a in range(180, -1, -5):
            set_angle(a); print("angle", a); time.sleep(0.04)
except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
    print("\nstopped")
