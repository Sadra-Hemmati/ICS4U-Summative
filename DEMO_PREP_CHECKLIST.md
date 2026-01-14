# Demo Day Checklist - January 15, 2026

## Before Demo (Morning Prep)

### ✓ Environment Check
```bash
# Activate venv
venv\Scripts\activate.bat

# Verify all dependencies
python -c "import pybullet, numpy, websockets, tkinter; print('✓ All dependencies OK')"

# Test GUI launches
python subsystemsim_app.py
# Close after confirming it opens
```

### ✓ Quick Functionality Test
```bash
# Test core physics (should take 5 seconds)
python tests/test_joint_movement.py
# Look for: arm rotating, position changing

# Test GUI with example
python subsystemsim_app.py
# Menu → Examples → Load Simple Arm Example
# Verify all tabs populate
# Close
```

### ✓ Prepare Demo Materials

**On Desktop**:
- [ ] SubsystemSim GUI running
- [ ] Terminal ready for commands
- [ ] Web browser with tabs open:
  - GrabCAD FRC page
  - WPILib Java examples
  - Online STEP→OBJ converter

**Have Ready**:
- [ ] This checklist printed/visible
- [ ] Sample CAD file (examples/simple_arm/meshes/)
- [ ] Sample config (examples/simple_arm/arm_config.json)

---

## Demo Flow (5-7 minutes)

### Part 1: Introduction (1 min)
"SubsystemSim is a physics simulator for FRC robot subsystems that works with real CAD files and real robot code in Java, C++, or Python."

**Show**:
- PyBullet physics window (from test)
- Mention problem: Teams can't test subsystems without building hardware

### Part 2: Import CAD (1 min)
**Launch GUI**: `python subsystemsim_app.py`

**Option A - Use Example**:
- Menu → Examples → Load Simple Arm Example
- "Built-in example loads instantly"

**Option B - Show Import**:
- Show CAD Import tab
- Examples → Download FRC CAD Resources
- "Teams download CAD from GrabCAD or Chief Delphi"
- "Convert STEP to OBJ online"
- Click Import CAD Files → select examples/simple_arm/meshes/*.obj

**Key Points**:
- Works with any FRC subsystem
- Thousands of designs available online
- Simple conversion process

### Part 3: Configuration (1 min)
**Switch to Configuration tab**

Point out:
- "JSON defines joints, motors, sensors"
- "Auto-generated from CAD files"
- Show structure:
  ```json
  "joints": [...]  // How parts connect
  "motors": [...]  // NEO, CIM, Falcon, etc.
  "sensors": [...]  // Encoders
  ```
- "Can edit manually or use GUI forms"

**Key Points**:
- Supports all FRC motors
- HAL ports match robot code
- Physics-based DC motor models

### Part 4: Robot Code (1 min)
**Switch to Robot Code tab**

- Browse → examples/simple_arm
- Show detected: Python project
- "Also works with Java and C++"

**Key Points**:
- Real, unmodified robot code
- Same code runs on real robot
- Universal - any WPILib language

### Part 5: Run Simulation (2 min)
**Switch to Run Simulation tab**

**Click Start Simulation**

Expected:
- Log shows initialization
- PyBullet window opens
- "WebSocket bridge running..."

**In Second Terminal**:
```bash
cd examples\simple_arm
python -m robotpy sim
```

**Show**:
- Robot code connects
- Arm moves in PyBullet
- Real-time physics simulation
- "This is real robot code controlling the simulation!"

**Key Points**:
- WebSocket bridge connects any language
- Real-time physics
- Realistic motor dynamics
- Teams can test code before robot is built

### Part 6: Java Support Demo (1 min - if time)
**Show in GUI**:
- Examples → Download Java Robot Examples
- Point to WPILib official examples
- "Same process: Start simulation, run gradlew simulateJava"

**Key Points**:
- 70% of FRC teams use Java
- Works identically to Python
- C++ support too

---

## Demo Talking Points

**Problem**:
- FRC teams build complex mechanisms (arms, elevators, intakes)
- Can't test code until hardware is built
- Late-season problems are expensive
- Limited testing time with real robot

**Solution - SubsystemSim**:
- Import CAD of your subsystem
- Configure joints and motors
- Run your real robot code
- Physics simulation shows how it will behave
- Test BEFORE building hardware

**Key Features**:
1. **Universal Language Support**: Java, C++, Python
2. **Real CAD**: Import actual team designs
3. **Unmodified Code**: Same code runs in sim and on robot
4. **Realistic Physics**: PyBullet engine, accurate motor models
5. **Easy to Use**: GUI application, auto-config generation

**Impact**:
- Test code early in build season
- Find problems in simulation, not on field
- Iterate faster
- More confident code at competition

---

## If Things Go Wrong

### GUI Won't Launch
**Fix**: Check Python/tkinter
```bash
python -c "import tkinter"
```

### PyBullet Window Doesn't Open
**Show**: Run test instead
```bash
python tests/test_joint_movement.py
```

### WebSocket Connection Fails
**Backup**: Explain architecture
- Draw diagram: Robot Code ↔ WebSocket ↔ PyBullet
- Show websocket_bridge.py code
- Explain it's implemented, working in testing

### Robot Code Won't Connect
**Backup**: Show pyfrc approach
```bash
cd examples\simple_arm
python robot.py sim
```
Or just show physics tests working

---

## Questions to Prepare For

**Q: Can it simulate full robots?**
A: Currently subsystems (one mechanism). Full robot support is future work. But most teams focus on subsystems anyway.

**Q: How accurate is the physics?**
A: Uses PyBullet (professional physics engine) + real motor specs. Angle wrapping, DC motor equations, realistic dynamics. Showed bug fix report proving accuracy.

**Q: Does it support sensors besides encoders?**
A: Currently encoders. Extensible to gyros, limit switches, vision. Foundation is there.

**Q: Can teams use their existing CAD?**
A: Yes! Just export to STEP, convert to OBJ online (free, 30 seconds). Works with SolidWorks, Fusion 360, Onshape, anything.

**Q: Do they need to modify their robot code?**
A: No modifications needed! That's the key feature. HAL WebSocket bridge makes it transparent.

**Q: What about C++ specifically?**
A: Same as Java - use gradlew simulateNative -Phalsim. WebSocket protocol is language-agnostic.

---

## Success Criteria

✓ **Must Have**:
- GUI launches and works
- Example loads successfully
- Physics simulation runs
- Clear explanation of workflow

✓ **Nice to Have**:
- Robot code connects live
- Show Java example download
- Smooth, confident presentation

✓ **Bonus**:
- Live Java robot code connection
- Custom CAD import demo
- Show bug fix report

---

## Final Checks (5 minutes before demo)

- [ ] Venv activated
- [ ] GUI tested and working
- [ ] Example loads successfully
- [ ] Terminal window ready
- [ ] Browser tabs prepared
- [ ] Know your talking points
- [ ] Backup plan if WebSocket fails
- [ ] Confident and ready!

---

## After Demo

**Potential Questions to Deflect to Future Work**:
- "Can it do multi-robot simulation?" → Future work
- "Can it simulate pneumatics?" → Future work, focus is motors now
- "CAD import isn't fully automatic?" → True, STEP conversion is one extra step but takes 30 seconds online

**Strengths to Emphasize**:
- Universal language support (unique!)
- Real, unmodified code (huge value)
- Based on real FRC ecosystem (WPILib HAL)
- Realistic physics (PyBullet + motor models)
- Practical for teams (solves real problem)

**You've built**:
- Complete physics engine wrapper
- Motor models with DC equations
- WebSocket bridge (language-agnostic!)
- Full GUI application
- Config generation system
- Integration with WPILib HAL

This is a substantial, working project that solves a real problem for FRC teams!

Good luck! 🚀
