# CAD Files

This folder contains the 3D model files for the Bullseye chassis.

## Files

| File | Format | Description |
|------|--------|-------------|
| CAD model.f3d | Fusion 360 | Full assembly - base + rotating head |

## Printing

All structural parts are designed for **FDM printing** (PLA or PETG recommended).

- **Base** - holds the Raspberry Pi, wiring, and servo body. Print with 20%+ infill.
- **Head** - mounts on the SG90 horn and carries the LCD, camera, and laser on the front face. Keep it as light as possible to reduce servo strain.

## Tips

- Export individual bodies from the F3D as STLs before slicing.
- The servo slot in the base is sized for a standard SG90 footprint - do not scale the model or it will not fit.
- Leave a loop of wire slack when routing cables through the head so the full ~140 degree pan range is free.
