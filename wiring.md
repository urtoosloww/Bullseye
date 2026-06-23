# Bullseye Wiring Reference

## Block Diagram

```
                     ┌──────────────────────────────────────────┐
                     │           Raspberry Pi 5                 │
                     │                                          │
  USB-C 27 W ───────►│ 5 V / GND rails                         │
                     │                                          │
                     │  GPIO8  ──────────── LCD CS              │
                     │  GPIO10 ──────────── LCD MOSI            │
                     │  GPIO11 ──────────── LCD SCK             │
                     │  GPIO24 ──────────── LCD DC              │
                     │  GPIO25 ──────────── LCD RESET           │
                     │  3.3 V  ──────────── LCD VCC + LED       │
                     │  GND    ──────────── LCD GND             │
                     │                                          │
                     │  GPIO18 ──────────── Servo signal        │
                     │  5 V    ──[cap]───── Servo VCC           │
                     │  GND    ──────────── Servo GND           │
                     │                                          │
                     │  GPIO17 ──────────── Laser signal (S)    │
                     │  3.3 V  ──────────── Laser VCC (+)       │
                     │  GND    ──────────── Laser GND (-)       │
                     │                                          │
                     │  GPIO26 ──────────── Button leg A        │
                     │  GND    ──────────── Button leg B        │
                     │                                          │
                     │  USB ──────────────► Camera (UVC)        │
                     │  USB ──────────────► Speaker             │
                     └──────────────────────────────────────────┘
```

`[cap]` = ~1000 µF electrolytic capacitor across the servo power/ground lines,
placed as close to the servo connector as possible. Reduces voltage spikes when
the servo stalls or reverses.

---

## LCD (ILI9341, 3.2" SPI, no touch)

| LCD pin | Pi physical pin | Pi GPIO |
|---------|-----------------|---------|
| VCC     | Pin 1           | 3.3 V   |
| GND     | Pin 6           | GND     |
| CS      | Pin 24          | GPIO8   |
| RESET   | Pin 22          | GPIO25  |
| DC      | Pin 18          | GPIO24  |
| MOSI    | Pin 19          | GPIO10  |
| SCK     | Pin 23          | GPIO11  |
| LED     | Pin 17          | 3.3 V   |

---

## Servo (SG90)

| Wire colour | Pi physical pin | Pi GPIO / rail |
|-------------|-----------------|----------------|
| Signal (orange) | Pin 12      | GPIO18 (HW PWM) |
| Power  (red)    | Pin 2 or 4  | 5 V             |
| Ground (brown)  | Any GND     | GND             |

---

## Laser module (3-pin)

| Laser pin | Pi physical pin | Pi GPIO / rail |
|-----------|-----------------|----------------|
| + (VCC)   | Pin 1 or 17     | 3.3 V          |
| - (GND)   | Any GND         | GND            |
| S (signal)| Pin 11          | GPIO17         |

---

## Shutdown / boot button

| Button leg | Pi physical pin | Pi GPIO |
|------------|-----------------|---------|
| Leg A      | Pin 37          | GPIO26  |
| Leg B      | Pin 39          | GND     |

For a 4-leg tactile button, wire **across the gap** (diagonal legs). The two legs on
the same side are internally connected and will not switch.

---

## Common ground note

All components in this build are powered from the Pi itself (3.3 V or 5 V headers)
and share the Pi's GND, so there is no separate power domain and no common-ground
bridging is needed. If you ever power the servo from an external 5 V supply
(for a heavier servo or multiple servos), **always connect that supply's GND to a
Pi GND pin** or signals will float and the servo will behave erratically.
