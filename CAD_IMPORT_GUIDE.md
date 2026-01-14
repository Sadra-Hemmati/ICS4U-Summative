# CAD Import Guide - Simple & Reliable

SubsystemSim uses **OBJ and STL mesh files** for physics simulation.

---

## Supported Formats

✅ **OBJ** (.obj) - Wavefront Object (Recommended)
✅ **STL** (.stl) - Stereolithography

These are standard 3D mesh formats that work perfectly with PyBullet physics.

---

## Quick Start

### If you have OBJ/STL files already:

1. Launch SubsystemSim: `python subsystemsim_app.py`
2. CAD Import tab → **"Import CAD Files"**
3. Select your OBJ/STL files
4. Click **"Auto-Generate Config"**
5. Done!

### If you have STEP files:

**30-Second Conversion Process:**

1. CAD Import tab → **"Convert STEP Online"** button
2. Website opens: https://convert3d.org/step-to-obj
3. Upload your STEP file
4. Click "Convert"
5. Download OBJ file(s)
6. Import the OBJ files in SubsystemSim

**No software installation needed!**

---

## Getting FRC CAD Files

### 1. GrabCAD (Largest Library)
**URL:** https://grabcad.com/library?query=frc

**What you'll find:**
- Thousands of FRC robot designs
- Arms, elevators, intakes, shooters, climbers
- Filter by year (2020-2024)
- Download as STEP or OBJ

**Example searches:**
- "FRC arm 2024"
- "FRC elevator mechanism"
- "FRC intake 2023"

**To download:**
- Click on a model
- Click "Download"
- Choose STEP format
- Convert to OBJ if needed

### 2. Chief Delphi CAD Forum
**URL:** https://www.chiefdelphi.com/c/technical/cad/15

**What you'll find:**
- Community-shared designs
- Well-documented mechanisms
- Team-tested designs
- STEP and SLDPRT formats

### 3. Everybot (Perfect for Testing)
**URL:** https://www.robowranglers148.com/uploads/1/0/5/4/10542658/2024_everybot_cad.zip

**Why it's great:**
- Simple, single-joint arm
- Well-documented
- Tested by hundreds of teams
- Easy to understand

**How to use:**
1. Download ZIP
2. Open in SolidWorks/Fusion 360
3. Export individual parts as OBJ or STEP
4. Import to SubsystemSim

### 4. WCP (West Coast Products)
**URL:** https://www.wcproducts.com/

**Commercial components with CAD:**
- Greyt Elevator
- Greyt Arm
- Gearboxes
- STEP files available

---

## Exporting from CAD Software

### SolidWorks
```
1. Open assembly/part
2. File → Save As
3. Save as type: OBJ (*.obj) or STEP (*.step)
4. Save
```

### Fusion 360
```
1. Open design
2. File → Export
3. Type: OBJ (.obj) or STEP (.step)
4. Export
```

### Onshape
```
1. Open document
2. Right-click part/assembly
3. Export → OBJ or STEP
4. Download
```

### FreeCAD
```
1. Open file
2. File → Export
3. File type: Alias Mesh (*.obj)
4. Export
```

---

## Best Practices

### 1. Simplify Before Export
- Remove screws, bolts, small details
- Export only the moving mechanism
- Combine small parts if possible
- Reduces file size and simulation complexity

### 2. Export Individual Parts
- Export base, arm, intake separately
- Each part becomes a "link" in config
- Easier to define joints between them

**Example: Simple Arm**
```
base.obj       (stationary base)
arm.obj        (rotating arm)
intake.obj     (rotating intake on arm)
```

Then define joints:
- base → arm (revolute joint at shoulder)
- arm → intake (revolute joint at wrist)

### 3. Check Orientation
- Most CAD exports in correct Z-up orientation
- If mesh looks wrong, adjust in config:
  ```json
  "origin": [0, 0, 0.1],  // Position offset
  "axis": [0, 0, 1]        // Rotation axis (Z-up)
  ```

### 4. Scale Check
- PyBullet uses meters
- Most CAD uses inches or mm
- Check if mechanism looks right size
- Adjust mass/inertia if needed

---

## Complete Workflow Example

### Scenario: Import 2024 Everybot Arm

**Step 1: Get CAD**
- Download: https://www.robowranglers148.com/uploads/1/0/5/4/10542658/2024_everybot_cad.zip
- Extract ZIP file

**Step 2: Export from CAD**
- Open in SolidWorks/Fusion 360
- Export parts individually:
  - `base.obj` (frame/base)
  - `arm.obj` (rotating arm)

**Step 3: Import to SubsystemSim**
```
1. Launch: python subsystemsim_app.py
2. CAD Import tab
3. Import CAD Files → select base.obj and arm.obj
4. Both appear in list
```

**Step 4: Auto-Generate Config**
```
5. Click "Auto-Generate Config from CAD Files"
6. Configuration tab opens with generated JSON
```

**Step 5: Edit Configuration**
```json
{
  "name": "everybot_arm",
  "links": [
    {
      "name": "base",
      "mesh": "C:\\...\\base.obj",
      "mass": 5.0,                    // Adjust to actual mass
      "center_of_mass": [0, 0, 0.05]
    },
    {
      "name": "arm",
      "mesh": "C:\\...\\arm.obj",
      "mass": 2.0,
      "center_of_mass": [0, 0, 0.25]  // Adjust to arm length
    }
  ],
  "joints": [
    {
      "name": "shoulder",
      "type": "revolute",
      "parent": "base",
      "child": "arm",
      "axis": [0, 0, 1],              // Z-axis rotation
      "origin": [0, 0, 0.1],          // Joint height
      "limits": null,                 // Continuous rotation
      "velocity_limit": 1000.0,
      "effort_limit": 100.0
    }
  ],
  "motors": [
    {
      "name": "arm_motor",
      "type": "neo",                  // NEO motor
      "joint": "shoulder",
      "gear_ratio": 60.0,             // 60:1 reduction
      "hal_port": 0,                  // PWM port 0
      "inverted": false
    }
  ],
  "sensors": [
    {
      "name": "arm_encoder",
      "type": "encoder",
      "joint": "shoulder",
      "hal_ports": [0, 1],            // DIO ports 0, 1
      "ticks_per_rev": 2048,
      "offset": 0.0
    }
  ]
}
```

**Step 6: Save Config**
```
7. Save Config As → everybot_arm_config.json
```

**Step 7: Test Simulation**
```
8. Run Simulation tab
9. Start Simulation
10. PyBullet window shows arm
```

**Step 8: Run Robot Code**
```
Terminal: gradlew simulateJava -Phalsim
(or Python: python robot.py sim)
```

**Step 9: Watch It Work!**
- Arm moves based on robot code
- Real-time physics simulation
- Encoder feedback to code

---

## Troubleshooting

### Mesh Not Visible in PyBullet
**Problem:** Imported but can't see mechanism

**Solutions:**
- Check file paths are absolute
- Verify OBJ file isn't corrupted (open in Blender)
- Check scale (might be too small/large)
- Look at console for errors

### Mesh in Wrong Position/Orientation
**Problem:** Parts not aligned correctly

**Solutions:**
- Adjust `origin` in joint definition
- Change `axis` if rotating wrong direction
- Re-export from CAD with correct orientation

### Too Many Files
**Problem:** CAD export created 100+ OBJ files

**Solutions:**
- Simplify in CAD first (remove screws, combine parts)
- Export only mechanism, not whole robot
- Manually select important parts

### File Size Too Large
**Problem:** OBJ files are huge (100MB+)

**Solutions:**
- Simplify mesh in CAD before export
- Use Blender to decimate mesh (reduce triangles)
- Export at lower quality setting

---

## Tips for Demo/Testing

### Use Simple Mechanisms First
- Single-joint arm
- Simple elevator
- One degree of freedom
- Easy to debug, fast to test

### Test Incrementally
1. Import one mesh → verify it loads
2. Add second mesh → verify both load
3. Add joint → verify connection
4. Add motor → verify control
5. Add encoder → verify feedback

### Keep Original CAD
- Save STEP files separately
- May need to re-export with different settings
- Keep source files for future iterations

---

## Summary

**Supported Formats:**
- ✅ OBJ (Recommended)
- ✅ STL
- ❌ STEP (convert online first - 30 seconds)

**Workflow:**
1. Get FRC CAD (GrabCAD, Chief Delphi)
2. Export as OBJ/STEP
3. Convert STEP→OBJ if needed (online, free)
4. Import to SubsystemSim
5. Auto-generate config
6. Edit and test

**No complex software installation needed!**

---

## Resources

**CAD Sources:**
- GrabCAD: https://grabcad.com/library?query=frc
- Chief Delphi: https://www.chiefdelphi.com/c/technical/cad/15
- Everybot: https://www.robowranglers148.com/

**Converters:**
- STEP→OBJ: https://convert3d.org/step-to-obj

**Tools:**
- Blender (mesh editing): https://www.blender.org/
- MeshLab (mesh viewing): https://www.meshlab.net/

Your SubsystemSim is ready to work with real FRC CAD!
