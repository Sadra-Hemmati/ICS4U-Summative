# STEP to OBJ Converter - User Guide

SubsystemSim now includes built-in STEP file conversion using FreeCAD!

---

## What This Does

Converts STEP CAD files (from SolidWorks, Fusion 360, Onshape, etc.) directly to OBJ mesh files for use in PyBullet physics simulation.

**Before**: Download STEP → Upload to online converter → Download OBJ → Import to SubsystemSim
**Now**: Download STEP → Click button in SubsystemSim → Done!

---

## Installation

### Step 1: Install FreeCAD

**Windows:**
1. Download: https://www.freecad.org/downloads.php
2. Click "Windows 64-bit installer"
3. Run installer (default options are fine)
4. Install location: `C:\Program Files\FreeCAD 0.21`

**macOS:**
1. Download: https://www.freecad.org/downloads.php
2. Click "macOS 64-bit dmg"
3. Drag FreeCAD to Applications folder

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install freecad freecad-python3

# Fedora
sudo dnf install freecad

# Arch
sudo pacman -S freecad
```

### Step 2: Verify Installation

```bash
python test_step_converter.py
```

Expected output:
```
============================================================
STEP to OBJ Converter Test
============================================================

Checking for FreeCAD installation...
  FreeCAD 0.21 found

✓ FreeCAD is installed and ready!
```

If FreeCAD is not found, the script will show installation instructions.

---

## Using the Converter in GUI

### Method 1: Through GUI Button

1. Launch SubsystemSim: `python subsystemsim_app.py`
2. Go to **CAD Import** tab
3. Click **"Convert STEP to OBJ"** button
4. Select your STEP file(s)
5. Choose output directory
6. Wait for conversion (progress shown in popup)
7. Click "Yes" to automatically import converted OBJ files

### Method 2: Command Line

```bash
python -m subsystemsim.cad.step_converter your_file.step
```

Or specify output directory:
```bash
python -m subsystemsim.cad.step_converter your_file.step -o output_folder
```

---

## What Happens During Conversion

1. **FreeCAD loads STEP file**
   - Reads all parts/assemblies
   - Preserves geometry

2. **Creates mesh for each part**
   - Tessellates surfaces into triangles
   - Quality: 0.1 deviation (good balance of detail/size)

3. **Exports OBJ files**
   - One OBJ per part/component
   - Named: `filename_partname.obj`
   - Or just `filename.obj` if single part

4. **Ready for simulation**
   - OBJ files can be imported directly
   - Use auto-generate config to create joints

---

## Example Workflow

### Converting Everybot 2024 Arm

1. **Download CAD:**
   - Go to: https://www.robowranglers148.com/uploads/1/0/5/4/10542658/2024_everybot_cad.zip
   - Extract ZIP file

2. **Export from SolidWorks/Fusion:**
   - Open assembly
   - File → Export → STEP (.step)
   - Save as `everybot_arm.step`

3. **Convert in SubsystemSim:**
   - CAD Import tab → Convert STEP to OBJ
   - Select `everybot_arm.step`
   - Output to: `examples/everybot_arm/meshes/`
   - Wait for conversion

4. **Result:**
   ```
   everybot_arm_base.obj
   everybot_arm_arm.obj
   everybot_arm_intake.obj
   ```

5. **Auto-generate config:**
   - Import OBJ files
   - Click "Auto-Generate Config"
   - Edit joint types and motor specs
   - Save configuration

6. **Run simulation!**

---

## Troubleshooting

### "FreeCAD Not Found"

**Problem:** Converter can't find FreeCAD installation

**Solutions:**
1. **Reinstall FreeCAD** to default location
2. **Add to PATH** (Windows):
   - System → Advanced → Environment Variables
   - Add: `C:\Program Files\FreeCAD 0.21\bin`
3. **Use online converter** as fallback:
   - https://convert3d.org/step-to-obj

### Conversion Creates Too Many Files

**Problem:** STEP file has many small parts

**Solution:** Simplify in CAD before export:
- Combine small parts
- Export only mechanism (not screws/bolts)
- Create simplified assembly

### Meshes Look Wrong in Simulation

**Problem:** Geometry is off, holes missing, etc.

**Solutions:**
1. **Check STEP export settings** in CAD software
2. **Increase mesh quality** (edit step_converter.py line 102):
   ```python
   mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.05))  # Lower = more detail
   ```
3. **Manually edit OBJ** in Blender if needed

### Conversion is Slow

**Problem:** Takes minutes for complex assemblies

**This is normal!** Complex CAD with many parts takes time.

**Tips:**
- Simplify assembly first
- Convert smaller sub-assemblies separately
- Use online converter for very complex files

---

## Advanced Usage

### Batch Convert Multiple Files

```python
from pathlib import Path
from subsystemsim.cad import batch_convert_step_files

step_files = [
    Path("arm_part1.step"),
    Path("arm_part2.step"),
    Path("intake.step")
]

obj_files = batch_convert_step_files(step_files, Path("output"))
print(f"Created {len(obj_files)} OBJ files")
```

### Convert in Python Script

```python
from pathlib import Path
from subsystemsim.cad import convert_step_to_obj

# Convert single file
obj_files = convert_step_to_obj(
    Path("my_mechanism.step"),
    output_dir=Path("meshes")
)

# obj_files is a list of created OBJ file paths
for obj in obj_files:
    print(f"Created: {obj}")
```

### Adjust Mesh Quality

Edit `subsystemsim/cad/step_converter.py` line ~102:

```python
# Higher quality (more triangles, larger files, slower)
mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.01))

# Standard quality (default)
mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))

# Lower quality (fewer triangles, faster)
mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.5))
```

---

## Supported CAD Formats

**Input:** STEP (.step, .stp)
- Universal CAD exchange format
- Supported by all major CAD tools:
  - SolidWorks
  - Fusion 360
  - Onshape
  - Inventor
  - CATIA
  - Creo
  - FreeCAD

**Output:** OBJ (.obj)
- Standard 3D mesh format
- Widely supported
- Works with PyBullet

**Export from CAD:**
- SolidWorks: File → Save As → STEP (*.step)
- Fusion 360: File → Export → STEP
- Onshape: Right-click part → Export → STEP

---

## Alternative: Online Converters

If FreeCAD installation doesn't work, use online converters:

1. **Convert3D** (Recommended)
   - https://convert3d.org/step-to-obj
   - Free, no account required
   - Fast, reliable conversion
   - Upload STEP → Download OBJ

2. **Aspose**
   - https://products.aspose.app/3d/conversion/step-to-obj
   - Free, no account
   - Supports batch conversion

3. **Greentoken**
   - https://www.greentoken.de/onlineconv/
   - Free converter
   - Multiple formats

---

## Benefits of Built-in Converter

✓ **No internet needed** - Works offline
✓ **Faster** - No upload/download time
✓ **Automated** - One click, auto-import
✓ **Batch processing** - Convert multiple files
✓ **Privacy** - CAD stays on your machine
✓ **Integration** - Seamless workflow in GUI

---

## Future Improvements

Planned features:
- [ ] STL input support
- [ ] Automatic mesh simplification
- [ ] Preview before conversion
- [ ] Adjust quality in GUI
- [ ] Convert on import (automatic)

---

## Summary

The STEP converter makes SubsystemSim truly ready for FRC teams:
1. Download CAD from GrabCAD/Chief Delphi
2. Export as STEP from any CAD tool
3. Convert to OBJ in SubsystemSim (one click!)
4. Auto-generate configuration
5. Run simulation with real robot code

No more manual online conversion steps!
