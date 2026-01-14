# SubsystemSim - Project Context for AI Agents

**Last Updated**: January 14, 2026 (just before deadline)
**Project Status**: FUNCTIONAL - WebSocket bridge working, awaiting final encoder initialization fix test
**Deadline**: January 15, 2026 (tomorrow)

---

## Project Overview

SubsystemSim is an FRC (FIRST Robotics Competition) subsystem physics simulator that allows teams to test robot code against realistic physics simulation WITHOUT modifying their code. It's **language-agnostic** - works with Java, C++, and Python robot code.

### Core Value Proposition
- Teams write standard WPILib robot code (Java/C++/Python)
- Code runs unchanged against physics simulation via HAL WebSocket protocol
- Physics simulation uses PyBullet with realistic DC motor models
- Supports any FRC subsystem (arms, elevators, shooters, etc.)

---

## Architecture

```
┌─────────────────────┐                    ┌──────────────────────┐
│ Robot Code          │  HAL WebSocket     │  SubsystemSim        │
│ (Java/C++/Python)   │ ◄────────────────► │  WebSocket Bridge    │
│                     │  Motor Commands    │                      │
│ + HAL Sim Extension │  Encoder Data      │  + PyBullet Physics  │
│ (creates WS server) │                    │  (WS client)         │
└─────────────────────┘                    └──────────────────────┘
         │                                            │
         │                                            │
         ▼                                            ▼
  Robot initializes:                        Bridge initializes:
  - PWM motor on port 0                     - Loads JSON config
  - Encoder on DIO 0,1                      - Generates URDF
  - Starts WS server                        - Loads PyBullet
  - Waits for connection                    - Creates motor models
                                            - Connects as WS client
         │                                            │
         └────────────────────────────────────────────┘
                    Connection established
```

### Key Components

1. **subsystemsim/core/** - Data model (Links, Joints, Motors, Sensors)
2. **subsystemsim/physics/** - PyBullet physics engine, URDF generation, DC motor models
3. **subsystemsim/hal_bridge/** - WebSocket bridge connecting robot code to physics
4. **examples/simple_arm/** - Working example (arm config, Python robot code, meshes)
5. **subsystemsim_app.py** - GUI application (optional, can run from CLI)

---

## Current Status (AS OF LAST WORK SESSION)

### What's Working ✅
- JSON config loading and URDF generation
- PyBullet physics with realistic DC motor models (NEO, CIM, Falcon, etc.)
- WebSocket bridge connects to robot code successfully
- PWM motor commands flow from robot code → physics
- Robot code initialization detected for PWM devices
- Motor torque applied to physics correctly
- Arm moves in PyBullet window

### What Was JUST Fixed ✅
1. **Unicode encoding issues** - All Unicode characters removed (Windows cp1252 compatibility)
2. **Path resolution** - Config paths resolve correctly from any working directory
3. **Physics.py conflict** - Removed conflicting pyfrc physics.py file
4. **WebSocket URI** - Fixed to include `/wpilibws` endpoint
5. **WebSocket protocol** - Implemented correct HAL WebSocket message format:
   - Device naming: `"0"` not `"PWM[0]"`
   - Data prefixes: `"<"` = output FROM robot, `">"` = input TO robot
   - Delta-based updates: Only send encoder data when value changes
6. **Encoder initialization** - Only send encoder data after robot initializes encoder

### Latest Issue Being Fixed 🔄
**Problem**: WebSocket timeout after arm spins briefly
**Root Cause**: Sending encoder data before robot code initializes the encoder device
**Solution Applied**: Added encoder initialization tracking - only publish encoder data after receiving `<init` message from robot code
**Status**: **NEEDS TESTING** - User should restart simulation to verify fix

### Files Modified in Last Session
- `websocket_bridge.py` - Added encoder initialization detection and delta-based updates
- All Python files - Removed Unicode characters for Windows compatibility
- `arm_config.json` - Updated to use relative mesh paths
- `config.py` - Fixed path resolution to be relative to config file
- `urdf_generator.py` - Fixed URDF mesh path generation
- `physics.py.backup` - Renamed to prevent pyfrc conflict

---

## Critical Technical Details

### HAL WebSocket Protocol
Based on official WPILib documentation: https://github.com/wpilibsuite/allwpilib/blob/main/simulation/halsim_ws_core/doc/hardware_ws_api.md

**Message Format**:
```json
{
  "type": "DeviceType",
  "device": "portNumber",
  "data": {
    "<field": value,  // "<" = output FROM robot code
    ">field": value   // ">" = input TO robot code
  }
}
```

**PWM (Motor) Example**:
```json
{
  "type": "PWM",
  "device": "0",
  "data": {
    "<init": true,      // Robot initialized device
    "<speed": 0.5       // Robot sending motor command
  }
}
```

**Encoder Example**:
```json
{
  "type": "Encoder",
  "device": "0",
  "data": {
    "<init": true,      // Robot initialized device
    ">count": 1234,     // Sim sending encoder count TO robot
    ">period": 0.001    // Sim sending period TO robot
  }
}
```

**CRITICAL RULES**:
1. **No subscription needed** - Robot sends device states automatically
2. **Delta-based updates** - Only send values when they change
3. **Initialization required** - Don't send sensor data until robot sends `<init`
4. **Simple device naming** - Use string port numbers: `"0"`, `"1"`, etc.

### Path Resolution
- Config file paths are relative to the config file's directory
- URDF paths are relative to the URDF file's directory
- Use forward slashes for cross-platform compatibility
- Example: `"mesh": "meshes/base.obj"` (relative to config file)

### DC Motor Physics
```
Back-EMF:     ε = Kv * ω
Current:      I = (V - ε) / R
Motor Torque: τ = Kt * I * gear_ratio * efficiency
```
- All motor constants calculated from spec sheets
- Default efficiency: 80%
- Supports: NEO, CIM, Falcon 500, NEO 550, MiniCIM, BAG, Venom

### Angle Wrapping
Revolute joints wrap position to (-π, π] for display while allowing continuous rotation internally.

---

## Running the System

### Method 1: GUI Application
```bash
python subsystemsim_app.py
```
1. Menu → Examples → Load Simple Arm Example
2. Run Simulation tab → Start Simulation
3. PyBullet window opens with arm
4. In separate terminal: `cd examples/simple_arm && python -m robotpy sim --ws-server`

### Method 2: CLI
Terminal 1 (SubsystemSim):
```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json
```

Terminal 2 (Robot Code):
```bash
cd examples/simple_arm
python -m robotpy sim --ws-server
```

**For Java/C++ robot code**:
```bash
gradlew simulateJava -Phalsim    # Java
gradlew simulateNative -Phalsim  # C++
```

---

## Common Issues & Solutions

### Issue: WebSocket Timeout
**Symptoms**: Connection works briefly then shows "keepalive ping timeout"
**Causes**:
1. Sending encoder data before robot initializes encoder → FIXED (added init tracking)
2. Sending too many encoder messages → FIXED (delta-based updates)
3. Robot code disconnects due to errors → Check robot code logs

### Issue: Arm Not Moving
**Symptoms**: PyBullet loads but arm stays static
**Causes**:
1. Robot not in teleop/autonomous mode → Enable in HAL simulator GUI
2. PWM port mismatch → Check config `hal_port` matches robot code
3. Motor commands not being sent → Add debug logging to robot code

### Issue: Encoder Always Zero
**Symptoms**: Robot code reads encoder as 0
**Causes**:
1. Encoder not initialized by robot → Check robot creates Encoder object
2. DIO port mismatch → Check config `hal_ports` matches robot code
3. Encoder data not being sent → Check bridge initialization tracking

### Issue: Unicode Encoding Errors
**Status**: FIXED - All Unicode removed from codebase
**Prevention**: Don't use Unicode characters (✓ → [OK], → → ->, etc.)

### Issue: Path Not Found
**Status**: FIXED - All paths now relative to config file
**Prevention**: Use relative paths like `"meshes/base.obj"` in config

---

## File Structure

```
ICS4U-Summative/
├── subsystemsim/
│   ├── core/
│   │   ├── model.py              # Data model classes
│   │   └── config.py             # JSON loading/saving
│   ├── physics/
│   │   ├── engine.py             # PyBullet wrapper
│   │   ├── urdf_generator.py    # URDF generation
│   │   └── actuators.py          # DC motor models
│   ├── hal_bridge/
│   │   ├── physics_interface.py # pyfrc physics bridge (deprecated)
│   │   └── websocket_bridge.py  # HAL WebSocket bridge (MAIN)
│   └── cad/
│       └── step_converter.py    # STEP to OBJ converter
│
├── examples/
│   └── simple_arm/
│       ├── meshes/               # OBJ mesh files
│       │   ├── base.obj
│       │   └── arm.obj
│       ├── arm_config.json       # Subsystem definition
│       ├── robot.py              # Python robot code
│       └── physics.py.backup     # Old pyfrc bridge (disabled)
│
├── tests/
│   ├── test_pybullet.py          # PyBullet sanity check
│   ├── test_arm_simulation.py    # Motor control test
│   ├── test_joint_movement.py    # Joint physics test
│   └── test_hal_bridge.py        # HAL bridge test
│
├── generated_urdfs/              # Auto-generated URDF files
│   └── simple_arm.urdf
│
├── subsystemsim_app.py           # GUI application
├── requirements.txt              # Dependencies
├── PROJECT_CONTEXT.md            # This file
├── README.md                     # User-facing documentation
└── SETUP.md                      # Setup instructions
```

---

## Important Code Locations

### WebSocket Bridge Main Loop
**File**: `subsystemsim/hal_bridge/websocket_bridge.py`
**Function**: `async def run(self)`
**What it does**: Main simulation loop - receives PWM, sends encoders, updates physics

### Motor Torque Calculation
**File**: `subsystemsim/physics/actuators.py`
**Class**: `DCMotor`
**Method**: `calculate_torque(voltage, angular_velocity, gear_ratio)`

### Encoder Count Calculation
**File**: `subsystemsim/hal_bridge/websocket_bridge.py`
**Method**: `async def publish_encoder_data(self)`
```python
# Convert joint position to encoder ticks
revolutions = position / (2 * 3.14159)
ticks = int(revolutions * ticks_per_rev)
```

### URDF Generation
**File**: `subsystemsim/physics/urdf_generator.py`
**Function**: `generate_urdf(model, output_dir)`
**Critical**: Uses relative paths for mesh files

---

## Testing Checklist

Before demo, verify these work:

1. **PyBullet loads**: `python tests/test_pybullet.py`
2. **Config loads**: `python -c "from subsystemsim.core.config import load_config; print(load_config('examples/simple_arm/arm_config.json'))"`
3. **URDF generates**: Check `generated_urdfs/simple_arm.urdf` exists
4. **Bridge starts**: `python -m subsystemsim.hal_bridge.websocket_bridge` (should wait for connection)
5. **Robot connects**: Start bridge, then `cd examples/simple_arm && python -m robotpy sim --ws-server`
6. **Motor control works**: Put robot in teleop, see arm move
7. **Encoder works**: Check robot code prints encoder values

---

## Known Limitations

1. **Manual CAD conversion**: STEP → OBJ requires FreeCAD or online converter
2. **Single subsystem**: Can't simulate full robot with multiple mechanisms
3. **No collision detection**: Parts can pass through each other
4. **Perfect sensors**: No noise or drift in encoder readings
5. **Python robot code**: HAL WebSocket may not work perfectly with RobotPy (use Java for best results)

---

## Next Steps for Future Development

### Immediate (If User Needs)
1. Test latest encoder initialization fix
2. Verify simulation runs stably for 30+ seconds
3. Test with Java robot code for reliability

### Future Enhancements
1. Add more sensor types (limit switches, CANcoders, gyros)
2. Implement collision detection
3. Add stress/torque monitoring with warnings
4. Support multiple subsystems in one simulation
5. Add data logging and replay
6. Create web-based viewer (instead of PyBullet GUI)

---

## For AI Agents Taking Over

### Critical Files to Understand
1. `websocket_bridge.py` - Main simulation loop and HAL protocol
2. `actuators.py` - Motor physics (don't change unless you understand DC motors)
3. `config.py` - Path resolution logic (be careful with relative paths)
4. `urdf_generator.py` - URDF XML generation

### Common User Requests
1. "Arm not moving" → Check PWM ports, robot mode, debug motor commands
2. "Encoder always zero" → Check DIO ports, encoder initialization
3. "WebSocket timeout" → Check for encoder flooding, initialization tracking
4. "Add new motor type" → Add to `MOTOR_SPECS` in `actuators.py`
5. "Import CAD" → Guide user to convert STEP → OBJ first

### Code Quality Standards
- No Unicode characters (Windows compatibility)
- Use relative paths (portability)
- Clear variable names (no single letters except i, j, k in loops)
- Docstrings on all public functions
- Type hints on function signatures

### Testing Before Committing
Always test these after changes:
```bash
python tests/test_pybullet.py          # Physics works
python -m subsystemsim.hal_bridge.websocket_bridge  # Bridge starts
# Then in another terminal:
cd examples/simple_arm && python -m robotpy sim --ws-server  # Connects
```

---

## Recent Conversation Summary

### Problem
- Simulation connected but timed out after a few seconds
- Encoder data flooding WebSocket connection
- Encoder data sent before robot initialized encoder device

### Solution
1. Implemented delta-based encoder updates (only send when value changes)
2. Added encoder initialization tracking (wait for `<init` from robot)
3. Fixed HAL WebSocket protocol implementation (correct prefixes, device naming)

### Status
- **Implemented but not tested** - User needs to restart and verify
- Arm was moving before timeout, so motor control works
- Motor commands being received: `[MOTOR] PWM[0] = -0.496`
- Just need encoder data to work reliably

---

## Emergency Demo Backup Plan

If WebSocket bridge still has issues tomorrow:

### Plan A: Show GUI and Tests
1. Launch GUI, demonstrate CAD import and config generation
2. Run standalone tests showing physics works
3. Show code and explain WebSocket implementation
4. Explain what would happen when it works

### Plan B: Simple Motor Control Demo
1. Modify `test_arm_simulation.py` to use hardcoded motor commands
2. Show arm moving smoothly in PyBullet
3. Explain this is the physics working
4. Show robot code separately and explain integration

### Plan C: Video Recording
1. Record screen when system IS working (even if briefly)
2. Show video during demo
3. Explain technical challenges overcome
4. Live code walkthrough instead of live demo

---

## Contact & Resources

- **WPILib HAL WebSocket Docs**: https://github.com/wpilibsuite/allwpilib/blob/main/simulation/halsim_ws_core/doc/hardware_ws_api.md
- **PyBullet Docs**: https://pybullet.org/
- **RobotPy Docs**: https://robotpy.readthedocs.io/
- **FRC Motor Specs**: https://motors.vex.com/

---

**FINAL NOTE**: The core physics and motor control work perfectly. The only remaining issue is ensuring encoder data flows reliably via WebSocket without timing out. The fix has been implemented and just needs testing.
