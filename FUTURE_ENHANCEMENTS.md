# Future Enhancements for SubsystemSim

This document tracks potential improvements and features for future development.

---

## High Priority

### 1. Built-in STEP Converter using pythonocc

**Goal:** Convert STEP files to OBJ directly within SubsystemSim without external dependencies or online converters.

**Technology:** pythonocc-core (Python wrapper for OpenCASCADE CAD kernel)

**Benefits:**
- ✅ Fully offline conversion
- ✅ Batch processing support
- ✅ No external website dependency
- ✅ More professional UX
- ✅ Customizable mesh quality

**Implementation Plan:**

#### Phase 1: Research & Setup
1. **Test pythonocc installation**
   ```bash
   conda install -c conda-forge pythonocc-core
   ```
   Note: pythonocc requires conda, not available via pip

2. **Create proof-of-concept converter**
   ```python
   from OCC.Extend.DataExchange import read_step_file
   from OCC.Core.StlAPI import StlAPI_Writer
   from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

   # Read STEP
   shape = read_step_file("input.step")

   # Mesh the shape
   mesh = BRepMesh_IncrementalMesh(shape, 0.1)
   mesh.Perform()

   # Export to OBJ/STL
   writer = StlAPI_Writer()
   writer.Write(shape, "output.stl")
   ```

3. **Test with FRC CAD files**
   - Everybot arm
   - Complex assemblies
   - Multi-part STEP files

#### Phase 2: Integration
1. **Create converter module**
   - `subsystemsim/cad/pythonocc_converter.py`
   - Similar API to `step_converter.py` (FreeCAD version)
   - Handle multi-part assemblies
   - Adjustable mesh quality

2. **Update GUI**
   - Check if pythonocc available
   - If yes: Use built-in converter
   - If no: Fall back to online converter
   - Add progress bar for conversion

3. **Add settings panel**
   - Mesh quality slider (0.01 - 1.0)
   - Combine small parts option
   - Preview before import

#### Phase 3: Testing & Polish
1. **Test with various CAD files**
   - Simple parts
   - Assemblies
   - Complex mechanisms

2. **Error handling**
   - Invalid STEP files
   - Out of memory
   - Unsupported geometry

3. **Performance optimization**
   - Multi-threading for large files
   - Caching converted meshes
   - Incremental mesh generation

**Challenges:**
- pythonocc is ~500MB+ with conda dependencies
- Installation more complex than pip
- May still be too heavy for some users
- OpenCASCADE learning curve

**Solution Strategy:**
- Make it optional: "Install pythonocc for built-in STEP conversion"
- Keep online converter as default/fallback
- Provide conda installation instructions
- Or: Create standalone converter app that SubsystemSim can call

**Estimated Effort:** 2-3 days
**Priority:** Medium (nice-to-have, not essential)

---

## Medium Priority

### 2. STL File Support Enhancement

**Goal:** Better STL handling with automatic mesh simplification

**Current:** STL files work but may have too many triangles
**Future:**
- Automatic decimation (reduce triangle count)
- Mesh repair (fix holes, non-manifold edges)
- Preview before import

**Technology:** trimesh (already a dependency!)

**Implementation:**
```python
import trimesh

# Load STL
mesh = trimesh.load("input.stl")

# Simplify (reduce triangles by 50%)
simplified = mesh.simplify_quadric_decimation(len(mesh.faces) // 2)

# Repair
simplified.fill_holes()
simplified.fix_normals()

# Export
simplified.export("output.obj")
```

**Estimated Effort:** 1 day

---

### 3. Multi-Robot Simulation

**Goal:** Simulate multiple robots/mechanisms interacting

**Use Cases:**
- Robot-to-robot handoffs
- Defense scenarios
- Multi-mechanism coordination

**Challenges:**
- Multiple WebSocket connections
- Collision detection between robots
- Coordinate frame management

**Estimated Effort:** 3-4 days

---

### 4. Physics Tuning GUI

**Goal:** Visual editor for physics parameters

**Features:**
- Sliders for mass, friction, damping
- Real-time preview of changes
- Reset to defaults
- Save physics profiles

**Estimated Effort:** 2 days

---

## Low Priority (Polish & UX)

### 5. Built-in CAD Viewer

**Goal:** Preview meshes before importing

**Technology:** VTK or matplotlib 3D

**Features:**
- 3D rotation, zoom, pan
- Show multiple parts
- Measure distances
- Check alignment

**Estimated Effort:** 2-3 days

---

### 6. Project File Format

**Goal:** Save entire project (CAD + config + code path) in one file

**Format:** ZIP archive containing:
- `project.json` - Metadata
- `meshes/` - CAD files
- `config.json` - Subsystem config
- `code/` - Robot code (optional copy)

**Benefits:**
- Easy sharing between team members
- Version control
- Backup/restore

**Estimated Effort:** 1 day

---

### 7. Real-time Physics Graphs

**Goal:** Live plotting of joint angles, velocities, motor voltages

**Technology:** matplotlib or plotly

**Features:**
- Time series plots
- Multiple variables
- Export to CSV
- Pause/resume

**Estimated Effort:** 2 days

---

### 8. Sensor Expansion

**Goal:** Support more FRC sensors

**Sensors to Add:**
- Limit switches
- Gyroscopes (IMU)
- Vision (AprilTag detection)
- Pressure sensors (pneumatics)
- Current sensors

**Estimated Effort:** 1-2 days per sensor type

---

### 9. Better Mesh Generation from URDF

**Goal:** Generate visual and collision meshes separately

**Current:** Uses same mesh for visual and collision
**Future:**
- Simplified collision mesh (faster physics)
- High-detail visual mesh (better appearance)
- Convex hull generation for collision

**Estimated Effort:** 2 days

---

### 10. Cloud Conversion Service

**Goal:** Own hosted STEP→OBJ converter

**Alternative to external websites:**
- Host our own conversion API
- Uses pythonocc or FreeCAD backend
- Teams upload STEP, download OBJ
- No size limits, privacy guaranteed

**Technology:**
- Flask/FastAPI backend
- pythonocc for conversion
- Cloud hosting (Heroku, AWS)

**Benefits:**
- More reliable than third-party sites
- Can optimize for FRC CAD specifically
- Privacy (CAD doesn't go to external sites)

**Challenges:**
- Hosting costs
- Maintenance
- Security (file uploads)

**Estimated Effort:** 1-2 weeks

---

## Research & Experimental

### 11. Machine Learning for Auto-Configuration

**Goal:** Automatically detect joint types, axes, and parameters from CAD

**Approach:**
- Train on FRC CAD dataset
- Detect common patterns (arms, elevators, intakes)
- Suggest joint placements
- Estimate masses and inertias

**Technology:**
- Computer vision (point clouds)
- Graph neural networks
- Transfer learning from CAD datasets

**Estimated Effort:** Research project (months)

---

### 12. Integration with CAD Tools

**Goal:** Direct plugin for SolidWorks, Fusion 360, Onshape

**Features:**
- Export button in CAD interface
- Automatic config generation
- One-click export to SubsystemSim

**Challenges:**
- Each CAD tool has different API
- Commercial licensing may be required
- Onshape uses JavaScript API (different approach)

**Estimated Effort:** 2-3 weeks per CAD tool

---

### 13. Hardware-in-the-Loop (HIL) Testing

**Goal:** Connect real motor controllers to simulation

**Use Cases:**
- Test real CAN bus code
- Validate motor controller firmware
- Detect timing issues

**Technology:**
- CANivore/Phoenix API
- Real-time Linux kernel
- Hardware abstraction layer

**Estimated Effort:** Major research project

---

## Implementation Priorities

**For Next Version (V1.1):**
1. ✅ pythonocc STEP converter (if feasible)
2. ✅ STL mesh simplification
3. ✅ Physics tuning GUI

**For Version 2.0:**
1. Multi-robot simulation
2. Project file format
3. Real-time graphs
4. More sensor types

**Research/Long-term:**
1. ML auto-configuration
2. CAD tool plugins
3. Hardware-in-the-loop

---

## Contributing

If implementing any of these features:
1. Create feature branch
2. Add tests
3. Update documentation
4. Submit PR with demo

---

## pythonocc Installation Guide (For Future Reference)

### Option 1: Conda (Recommended)

```bash
# Create conda environment
conda create -n subsystemsim-dev python=3.11
conda activate subsystemsim-dev

# Install pythonocc
conda install -c conda-forge pythonocc-core

# Install other dependencies
pip install -r requirements.txt
```

### Option 2: Docker

```dockerfile
FROM continuumio/miniconda3

RUN conda install -c conda-forge pythonocc-core
RUN pip install pybullet numpy websockets

WORKDIR /app
COPY . .

CMD ["python", "subsystemsim_app.py"]
```

### Option 3: Standalone Converter App

Create separate converter application:
```
step-converter-app/
  ├── converter.py          # pythonocc conversion logic
  ├── app.exe              # Compiled executable
  └── README.md

SubsystemSim calls: converter.exe input.step output.obj
```

Benefits:
- No conda dependency in main app
- Users download converter separately (optional)
- Easier to maintain

---

## Notes for Future Developers

**When implementing pythonocc converter:**

1. **Test installation first**
   - pythonocc is notoriously tricky to install
   - Conda-only (not pip)
   - Large dependency tree
   - May conflict with other packages

2. **Make it optional**
   - Don't break existing functionality
   - Fall back to online converter if unavailable
   - Clear error messages

3. **Handle complex STEP files**
   - Assemblies vs single parts
   - Multiple bodies
   - Different units (mm, inches, meters)

4. **Performance considerations**
   - Large files can take minutes
   - Consider multi-threading
   - Show progress to user

5. **Documentation**
   - Clear installation instructions
   - Example code
   - Troubleshooting guide

**Good luck!** 🚀
