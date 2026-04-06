# SR3 AUX Exporter — Blender Add-on

Exports Blender meshes to the proprietary **Auxiliary 3D** binary format (`.aux`)
used by **StreetRod3Classic**, together with a companion text material file (`.mat`).

---

## Installation

1. Select all four Python files and zip them **as a folder**:
   ```
   blender_exporter/
       __init__.py
       exporter.py
       aux_writer.py
       mat_writer.py
   ```
2. Blender → **Edit > Preferences > Add-ons > Install…** → select the zip.
3. Enable **Import-Export: StreetRod3 AUX Exporter**.

---

## Usage

**File > Export > StreetRod3 Model (.aux)**

The exporter writes two files side by side:

| File | Content |
|---|---|
| `car.aux` | Binary 3D geometry (vertices, UVs, normals, meshes, lights, anchors) |
| `car.mat` | Text material definitions (textures, colours, blending) |

Copy both into `game/data/cars/<your_car_folder>/`.

---

## Object Conventions

| Blender type | Condition | Result in .aux |
|---|---|---|
| `MESH` | any | 3D mesh |
| `LIGHT` | any | Point light |
| `EMPTY` | name starts with `$` | Game-object anchor |

### Required Anchor Names (`$`-Empties)

Place an Empty at each attachment point and name it exactly:

```
Wheels      $flwheel  $frwheel  $brwheel  $blwheel
Shocks      $flshock  $frshock  $brshock  $blshock
Exhaust     $lmuffler  $rmuffler
Engine      $block
Drivetrain  $diff  $trans
Camera      $incar_cam
Headlights  $hlite01  $hlite02  …  (sequential, stop at first missing)
Taillights  $tlite01  $tlite02  …
```

---

## Export Options

| Option | Default | Description |
|---|---|---|
| **Selected Only** | ✓ | Export only selected objects |
| **Axis Conversion (Z-up → Y-up)** | ✓ | Converts Blender Z-up to SR3 Y-up: `game(X,Y,Z) = blender(X, Z, -Y)` |

---

## Material Mapping

The exporter reads each Blender material's node tree:

- **Image Texture node** → `Texture FILENAME.PNG` in the `.mat`
- **Principled BSDF Base Color** → `RGB r,g,b` (used when no image texture)
- **Alpha blend mode** → `Blend b_alpha` + `backcull false`

### Special material names

| Name | Behaviour |
|---|---|
| `CarMaterial` | Gets `TcGen tc_sphere` (chrome/env-map reflection) + two-pass paint overlay |
| `window` | Automatically gets `Blend b_alpha` + `backcull false` |

---

## Coordinate System

```
Blender  →  SR3 Game
   X     →     X     (right)
   Z     →     Y     (up)
  -Y     →     Z     (forward)
```

If your model is already oriented for the game, disable **Axis Conversion**.

---

## .aux Binary Format Reference

See [`aux_writer.py`](aux_writer.py) for the full byte-level layout documentation.

---

## Project Structure

```
blender_exporter/
    __init__.py       Blender add-on registration + export operator
    exporter.py       Blender scene data  →  AUXModel
    aux_writer.py     AUXModel            →  binary .aux file
    mat_writer.py     AUXModel            →  text .mat file
    README.md         This file
```
