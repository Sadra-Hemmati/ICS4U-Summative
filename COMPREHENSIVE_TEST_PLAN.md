# SubsystemSim - Comprehensive Test Plan
**Updated**: January 14, 2026
**Deadline**: January 15, 2026
**Status**: Ready for Testing

---

## Overview

This test plan verifies all SubsystemSim features work correctly after adding:
- WebSocket bridge for Java/C++/Python support
- GUI application for ease of use
- CAD import and config generation

---

## Prerequisites

Ensure all dependencies are installed:

```bash
pip install websockets
```

Verify installation:
```bash
python -c "import pybullet, numpy, websockets; print('All dependencies OK')"
```

---

## Phase 1: Core Component Tests (Previously Passed)

These tests verify the foundation still works after new features were added.

### Test 1: PyBullet Basic Rendering
**Purpose**: Verify PyBullet installation and basic physics
**Command**: `python tests/test_pybullet.py`
**Expected**: Cube falls under gravity in PyBullet GUI
**Duration**: 5 seconds
**Pass Criteria**: PyBullet window opens, cube falls smoothly

### Test 2: Data Model Validation
**Purpose**: Verify subsystem model classes work
**Command**: Run directly in Python:
```python
from subsystemsim.core.model import SubsystemModel, Link, Joint, Motor, Sensor
from subsystemsim.physics.actuators import MotorType

# Create simple model
link = Link(name="test", mesh_path="test.obj", mass=1.0)
joint = Joint(name="j1", joint_type="revolute", parent_link="base", child_link="test")
motor = Motor(name="m1", motor_type=MotorType.NEO, joint_name="j1", gear_ratio=60, hal_port=0)
sensor = Sensor(name="e1", sensor_type="encoder", joint_name="j1", hal_ports=[0,1], ticks_per_revolution=2048)

model = SubsystemModel(name="test", links=[link], joints=[joint], motors=[motor], sensors=[sensor])
print(f"✓ Model created: {model}")
print(f"✓ Validation: {model.validate()}")
```
**Pass Criteria**: Model creates without errors, validation returns True

### Test 3: JSON Config Loading
**Purpose**: Verify config files load correctly
**Command**:
```python
from subsystemsim.core.config import load_config
model = load_config("examples/simple_arm/arm_config.json")
print(f"✓ Loaded: {model}")
```
**Pass Criteria**: Config loads, prints model details

### Test 4: URDF Generation
**Purpose**: Verify URDF generation from model
**Command**: `python regenerate_urdf.py`
**Expected**: Creates `generated_urdfs/simple_arm.urdf`
**Pass Criteria**: File exists, no errors, valid XML

### Test 5: Motor Physics Models
**Purpose**: Verify DC motor calculations
**Command**:
```python
from subsystemsim.physics.actuators import DCMotor

motor = DCMotor("neo")
torque = motor.calculate_torque(voltage=6.0, angular_velocity=50.0, gear_ratio=60.0)
print(f"✓ NEO motor @ 6V, 50 rad/s: {torque:.3f} Nm")
assert torque > 0, "Torque should be positive"
```
**Pass Criteria**: Calculates torque, value is reasonable (> 0)

### Test 6: Joint Movement (Physics Engine)
**Purpose**: Verify PyBullet joint control with angle wrapping
**Command**: `python tests/test_joint_movement.py`
**Expected**: Arm rotates continuously, position wraps to ±180°
**Duration**: 30 seconds
**Pass Criteria**:
- Arm visible and rotating
- Velocity increases linearly
- Position wraps correctly at ±π

### Test 7: HAL Bridge Initialization
**Purpose**: Verify HAL bridge components load
**Command**: `python tests/test_hal_bridge.py`
**Expected**: Loads model, creates motors/sensors, runs update loop
**Pass Criteria**: All checks pass, no errors

---

## Phase 2: GUI Application Tests

These tests verify the new GUI works correctly.

### Test 8: GUI Launch
**Purpose**: Verify GUI application starts
**Command**: `python subsystemsim_app.py`
**Expected**: Window opens with 4 tabs
**Pass Criteria**:
- Window title: "SubsystemSim - FRC Subsystem Simulator"
- 4 tabs visible: CAD Import, Configuration, Robot Code, Run Simulation
- Menu bar with File, Examples, Help
- No errors in console

### Test 9: Load Built-in Example
**Purpose**: Verify example loader works
**Steps**:
1. Launch GUI: `python subsystemsim_app.py`
2. Menu → Examples → Load Simple Arm Example
3. Check all tabs populate correctly

**Expected Results**:
- **CAD Import tab**: Shows 2 files (base.obj, arm.obj)
- **Configuration tab**: JSON editor shows arm_config.json contents
- **Robot Code tab**: Shows examples/simple_arm path and Python project info
- **Status bar**: "Loaded simple arm example"

**Pass Criteria**: All data loads, no errors, popup confirms success

### Test 10: CAD Import (Manual)
**Purpose**: Verify manual CAD file import
**Steps**:
1. Launch GUI
2. CAD Import tab → Import CAD Files
3. Select: examples/simple_arm/meshes/base.obj
4. Select: examples/simple_arm/meshes/arm.obj

**Expected**: Both files appear in list
**Pass Criteria**: Files listed, status shows "Imported 2 CAD file(s)"

### Test 11: Auto-Generate Config
**Purpose**: Verify config auto-generation from CAD
**Steps**:
1. Load example (Test 9) or import CAD (Test 10)
2. Click "Auto-Generate Config from CAD Files"

**Expected**:
- Switches to Configuration tab
- JSON shows generated config with links, joints, motors, sensors
- Popup shows summary

**Pass Criteria**: Valid JSON generated, matches CAD file count

### Test 12: Config Validation
**Purpose**: Verify config editor validates JSON
**Steps**:
1. Load example
2. Configuration tab → Validate button

**Expected**: Popup shows "Configuration is valid!" with counts
**Pass Criteria**: Validation passes, shows correct counts

### Test 13: Save/Load Config
**Purpose**: Verify config persistence
**Steps**:
1. Load example
2. Configuration tab → Save Config As
3. Save to new location (e.g., Desktop/test_config.json)
4. File → New Project
5. Configuration tab → Load from File
6. Select saved config

**Expected**: Config loads back correctly
**Pass Criteria**: All data preserved, no errors

---

## Phase 3: WebSocket Bridge Tests

These tests verify the WebSocket bridge connects robot code to physics.

### Test 14: WebSocket Bridge Standalone
**Purpose**: Verify bridge starts independently
**Command**: `python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json`

**Expected Output**:
```
SubsystemSim HAL WebSocket Bridge
==================================================
Config: examples/simple_arm/arm_config.json

Loaded model: SubsystemModel(...)
Generated URDF: generated_urdfs/simple_arm.urdf
PhysicsEngine initialized
PWM[0] → shoulder (neo, ratio=60.0)
Encoder[0] → shoulder (2048 ticks/rev)

Waiting for WebSocket connection...
```

**Pass Criteria**:
- PyBullet window opens showing arm
- Bridge waits for connection
- No errors

### Test 15: GUI-Launched Simulation
**Purpose**: Verify GUI can start WebSocket bridge
**Steps**:
1. Launch GUI
2. Load simple arm example
3. Run Simulation tab → Start Simulation

**Expected**:
- Simulation log shows initialization messages
- PyBullet window opens
- Status: "Simulation running"
- Stop button becomes enabled

**Pass Criteria**: Bridge starts, PyBullet visible, no errors

### Test 16: Python Robot Code Connection
**Purpose**: Verify Python robot code connects to bridge

**Setup - Terminal 1**:
```bash
python -m subsystemsim.hal_bridge.websocket_bridge
```

**Setup - Terminal 2**:
```bash
cd examples/simple_arm
python -m robotpy sim
```

**Expected**:
- Terminal 1 shows: "✓ Connected to HAL simulation WebSocket"
- Terminal 1 shows: "Subscribed to PWM[0]"
- Terminal 2 shows: Robot code initialization messages
- PyBullet shows arm moving

**Pass Criteria**: Connection established, arm responds to robot code

**Note**: This test may fail if RobotPy HAL WS extension isn't working. If so, proceed to Java test (Test 17).

---

## Phase 4: Java Integration Tests

These tests verify Java robot code works with SubsystemSim.

### Test 17: Download Java Example Code
**Purpose**: Get Java robot code for testing

**Quick Option** - WPILib ArmBot Example:
1. Go to: https://github.com/wpilibsuite/allwpilib
2. Click "Code" → Download ZIP
3. Extract allwpilib-main.zip
4. Navigate to: `wpilibjExamples/src/main/java/edu/wpi/first/wpilibj/examples/armbot/`
5. This is your Java robot code folder

**OR Clone Full Repo**:
```bash
git clone https://github.com/wpilibsuite/allwpilib.git
cd allwpilib/wpilibjExamples/src/main/java/edu/wpi/first/wpilibj/examples/armbot
```

**Pass Criteria**: Have Java robot code folder with Robot.java file

### Test 18: Analyze Java Code in GUI
**Purpose**: Verify GUI recognizes Java projects
**Steps**:
1. Launch GUI
2. Robot Code tab → Browse
3. Select armbot folder (from Test 17)

**Expected**:
- Path shows in text box
- Info panel shows: "Project Type: Java/C++ (Gradle)"
- Shows .java files found
- Displays simulation command

**Pass Criteria**: GUI detects Gradle project, shows Java files

### Test 19: Java Robot Code Full Integration
**Purpose**: End-to-end test with Java code

**Prerequisites**:
- Java JDK 17+ installed
- Downloaded armbot example (Test 17)

**Setup - Terminal 1 (SubsystemSim)**:
```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json
```

**Setup - Terminal 2 (Java Robot Code)**:
```bash
cd path/to/armbot
gradlew simulateJava -Phalsim
```

**Expected**:
- Terminal 1: "✓ Connected to HAL simulation WebSocket"
- Terminal 2: Robot code compiles and runs
- PyBullet: Arm moves according to Java code logic
- WPILib Simulator GUI opens (optional)

**Pass Criteria**:
- Java code connects
- Arm responds to commands
- Encoder feedback works

**Troubleshooting**:
- If `gradlew` not found: Robot code may not be complete Gradle project
- If connection fails: Check firewall allows localhost:3300
- If motors don't move: Verify HAL port numbers match config

---

## Phase 5: Demo Preparation

### Test 20: Complete Demo Workflow
**Purpose**: Practice the full demo flow

**Demo Script**:
1. **Launch**: `python subsystemsim_app.py`
2. **Load Example**: Menu → Examples → Load Simple Arm Example
3. **Show CAD**: Switch to CAD Import tab, show imported meshes
4. **Show Config**: Switch to Configuration tab, explain JSON structure
5. **Show Robot Code**: Switch to Robot Code tab, show detected Python project
6. **Run Simulation**: Switch to Run Simulation tab, click Start
7. **Connect Robot Code**: In separate terminal: `cd examples/simple_arm && python -m robotpy sim`
8. **Show Working**: Point out:
   - PyBullet window showing moving arm
   - Terminal logs showing motor commands
   - Real robot code controlling simulation

**Alternate Demo with CAD Import**:
1. Launch GUI
2. Show downloading CAD from GrabCAD (Examples → Download FRC CAD Resources)
3. Import custom OBJ files
4. Auto-generate config
5. Edit config in GUI
6. Show Java examples menu
7. Run simulation with custom subsystem

**Pass Criteria**: Can execute demo smoothly in under 5 minutes

---

## Test Results Checklist

Mark each test as you complete it:

**Phase 1: Core Components**
- [ ] Test 1: PyBullet Basic Rendering
- [ ] Test 2: Data Model Validation
- [ ] Test 3: JSON Config Loading
- [ ] Test 4: URDF Generation
- [ ] Test 5: Motor Physics Models
- [ ] Test 6: Joint Movement
- [ ] Test 7: HAL Bridge Initialization

**Phase 2: GUI Application**
- [ ] Test 8: GUI Launch
- [ ] Test 9: Load Built-in Example
- [ ] Test 10: CAD Import (Manual)
- [ ] Test 11: Auto-Generate Config
- [ ] Test 12: Config Validation
- [ ] Test 13: Save/Load Config

**Phase 3: WebSocket Bridge**
- [ ] Test 14: WebSocket Bridge Standalone
- [ ] Test 15: GUI-Launched Simulation
- [ ] Test 16: Python Robot Code Connection

**Phase 4: Java Integration**
- [ ] Test 17: Download Java Example Code
- [ ] Test 18: Analyze Java Code in GUI
- [ ] Test 19: Java Robot Code Full Integration

**Phase 5: Demo Prep**
- [ ] Test 20: Complete Demo Workflow

---

## Known Limitations

1. **STEP File Import**: Not automatic - requires online conversion to OBJ
2. **CAD Origin/Orientation**: May need manual adjustment in config
3. **Python HAL WebSocket**: May not work with current RobotPy - use Java if issues
4. **Joint Axes**: Auto-generated as Z-axis, may need editing for complex mechanisms

---

## Quick Reference - Important Files

**Core**:
- `subsystemsim/physics/engine.py` - PyBullet physics wrapper
- `subsystemsim/physics/actuators.py` - Motor models
- `subsystemsim/hal_bridge/websocket_bridge.py` - WebSocket bridge

**GUI**:
- `subsystemsim_app.py` - Main GUI application

**Examples**:
- `examples/simple_arm/` - Complete working example
- `examples/simple_arm/arm_config.json` - Config reference

**Documentation**:
- `WEBSOCKET_BRIDGE_GUIDE.md` - WebSocket bridge usage
- `BUG_FIX_REPORT.md` - Physics bug fixes documentation

---

## For Your Demo Tomorrow

**Minimum Viable Demo** (if pressed for time):
1. Launch GUI
2. Load simple arm example
3. Start simulation
4. Show PyBullet physics working
5. Explain CAD/config/robot code workflow

**Full Demo** (if you have Java code working):
1. Launch GUI
2. Load simple arm example
3. Explain each tab
4. Start WebSocket bridge
5. Run Java robot code
6. Show live integration

**Backup Plan** (if WebSocket issues):
1. Launch GUI
2. Demo CAD import and config generation
3. Run tests 1-7 to show physics working
4. Explain that WebSocket bridge is implemented (show code)

---

## Success Criteria

✓ **Core physics works** (Tests 1-7 pass)
✓ **GUI functional** (Tests 8-13 pass)
✓ **WebSocket bridge runs** (Test 14-15 pass)
✓ **Either Python OR Java connects** (Test 16 or 19 passes)
✓ **Can demonstrate complete workflow** (Test 20)

If all these pass, your project successfully demonstrates a universal FRC subsystem simulator!
