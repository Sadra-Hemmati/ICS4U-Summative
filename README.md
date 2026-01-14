# SubsystemSim - FRC Subsystem Simulator

**A physics-based simulator for FRC subsystems that runs real robot code without modifications.**

SubsystemSim allows FRC teams to:
- Import CAD subsystems (STEP files)
- Define joints, motors, and sensors via JSON
- Run their **existing WPILib code unchanged** against a physics simulation
- Test mechanism behavior before hardware is built

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (Python 3.10+)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install pybullet numpy trimesh pyyaml
pip install robotpy[all] pyntcore
```

**Note**: RobotPy installation may take 5-10 minutes (compiles native extensions).

### 2. Run the Example

```bash
# Test PyBullet installation
python tests/test_pybullet.py

# Test arm simulation (motor control)
python tests/test_arm_simulation.py

# Run full WPILib simulation (robot code → physics)
python -m pyfrc sim examples/simple_arm/robot.py
```

---

## Architecture

```
CAD (STEP) → Meshes (OBJ) → JSON Config
                ↓
         SubsystemModel
                ↓
         URDF Generator
                ↓
      PyBullet Physics ←→ HAL Bridge ←→ Robot Code
```

**Key Components:**

1. **Data Model** (`subsystemsim/core/model.py`): Internal representation (Links, Joints, Motors, Sensors)
2. **Config Loader** (`subsystemsim/core/config.py`): JSON ↔ Model conversion
3. **URDF Generator** (`subsystemsim/physics/urdf_generator.py`): Model → URDF XML
4. **Physics Engine** (`subsystemsim/physics/engine.py`): PyBullet wrapper
5. **Motor Models** (`subsystemsim/physics/actuators.py`): Realistic FRC motor physics (NEO, CIM, Falcon)
6. **HAL Bridge** (`subsystemsim/hal_bridge/physics_interface.py`): WPILib ↔ PyBullet integration

---

## Creating a Subsystem

### Step 1: Create Mesh Files

Convert STEP CAD to OBJ meshes:
- **Option A**: FreeCAD GUI: File → Export → OBJ
- **Option B**: Use provided placeholder meshes

Save meshes to: `examples/your_subsystem/meshes/`

### Step 2: Define Configuration

Create `examples/your_subsystem/config.json`:

```json
{
  "name": "my_subsystem",
  "links": [
    {
      "name": "base",
      "mesh": "meshes/base.obj",
      "mass": 2.0
    },
    {
      "name": "arm",
      "mesh": "meshes/arm.obj",
      "mass": 1.5
    }
  ],
  "joints": [
    {
      "name": "shoulder",
      "type": "revolute",
      "parent": "base",
      "child": "arm",
      "axis": [0.0, 0.0, 1.0],
      "limits": [-1.57, 1.57]
    }
  ],
  "motors": [
    {
      "name": "shoulder_motor",
      "type": "neo",
      "joint": "shoulder",
      "gear_ratio": 60.0,
      "hal_port": 0
    }
  ],
  "sensors": [
    {
      "name": "arm_encoder",
      "type": "encoder",
      "joint": "shoulder",
      "hal_ports": [0, 1],
      "ticks_per_rev": 2048
    }
  ]
}
```

### Step 3: Write Robot Code

Create `examples/your_subsystem/robot.py`:

```python
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        self.motor = wpilib.PWMMotorController(0)
        self.encoder = wpilib.Encoder(0, 1)
        self.encoder.setDistancePerPulse((2 * 3.14159) / 2048)

    def teleopPeriodic(self):
        # Your control logic here
        self.motor.set(0.5)
        print(f"Position: {self.encoder.getDistance():.2f} rad")

if __name__ == "__main__":
    wpilib.run(MyRobot)
```

### Step 4: Create Physics Bridge

Create `examples/your_subsystem/physics.py`:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from subsystemsim.hal_bridge.physics_interface import SubsystemPhysicsEngine

class PhysicsEngine:
    def __init__(self, physics_controller):
        config_path = Path(__file__).parent / "config.json"
        self.sim = SubsystemPhysicsEngine(physics_controller, str(config_path))

    def update_sim(self, now: float, tm_diff: float):
        self.sim.update_sim(now, tm_diff)
```

### Step 5: Run Simulation

```bash
python -m pyfrc sim examples/your_subsystem/robot.py
```

---

## Configuration Reference

### Joint Types

- **`revolute`**: Rotational joint (hinge) - use for arms, wrists, turrets
- **`prismatic`**: Linear joint (slider) - use for elevators, extenders
- **`fixed`**: Rigid connection - use for mounting plates

### Motor Types

Supported FRC motors:
- `neo` - REV NEO (5676 RPM free, 2.6 Nm stall)
- `cim` - VEX CIM (5330 RPM free, 2.41 Nm stall)
- `falcon500` - CTRE Falcon 500 (6380 RPM free, 4.69 Nm stall)
- `neo550` - REV NEO 550 (11000 RPM free, 0.97 Nm stall)
- `minicim` - VEX MiniCIM
- `bag` - VEX BAG Motor
- `venom` - Playing With Fusion Venom

Motor model uses full DC motor physics: `V = IR + Kv*ω`, `τ = Kt*I`

### Coordinate System

- **Z-up, right-handed** (URDF/ROS standard)
- PyBullet and URDF both use Z-up by default
- Joint axes: `[x, y, z]` unit vector (e.g., `[0, 0, 1]` = Z-axis rotation)

---

## Testing Without Robot Code

### Test Individual Components

```bash
# Test data model
python -m subsystemsim.core.model

# Test config loading
python -m subsystemsim.core.config

# Test URDF generation
python -m subsystemsim.physics.urdf_generator

# Test motor models
python -m subsystemsim.physics.actuators

# Test HAL bridge initialization
python -m subsystemsim.hal_bridge.physics_interface
```

### Standalone Simulation (No WPILib)

```bash
# Run arm with manual torque control
python test_arm_simulation.py
```

---

## Project Structure

```
ICS4U-Summative/
├── subsystemsim/              # Main package
│   ├── core/                  # Data model
│   │   ├── model.py          # Link, Joint, Motor, Sensor classes
│   │   └── config.py         # JSON loading/saving
│   ├── physics/               # Simulation
│   │   ├── engine.py         # PyBullet wrapper
│   │   ├── urdf_generator.py # URDF conversion
│   │   └── actuators.py      # Motor models
│   └── hal_bridge/            # WPILib integration
│       └── physics_interface.py  # PhysicsEngine for pyfrc
│
├── examples/
│   └── simple_arm/            # Example subsystem
│       ├── meshes/            # OBJ geometry files
│       ├── arm_config.json   # Subsystem definition
│       ├── robot.py          # WPILib robot code
│       └── physics.py        # Physics bridge
│
├── tests/                     # All test files
│   ├── test_pybullet.py      # Day 1 test
│   ├── test_arm_simulation.py # Day 4 test
│   ├── test_joint_movement.py # Joint control test
│   └── diagnose_physics.py   # Physics diagnostic
│
├── requirements.txt          # Dependencies
├── SETUP.md                  # Setup instructions
└── README.md                 # This file
```

---

## Troubleshooting

### PyBullet GUI Not Showing

If running on WSL or headless server:
```python
# In physics/engine.py, change:
engine = PhysicsEngine(gui=False)  # Use DIRECT mode
```

### Import Errors

Make sure you're in the project root:
```bash
cd C:\Users\sadra\ICS4U\ICS4U-Summative
python -m pyfrc sim examples/simple_arm/robot.py
```

### RobotPy Installation Fails

Try installing without optional dependencies:
```bash
pip install robotpy wpilib pyntcore
```

### Mesh Not Found

Use absolute paths in JSON config:
```json
"mesh": "C:/Users/sadra/ICS4U/ICS4U-Summative/examples/simple_arm/meshes/base.obj"
```

Or ensure you run from project root so relative paths resolve correctly.

---

## Known Limitations (MVP)

- **Manual CAD Conversion**: STEP → OBJ must be done manually (no automated import yet)
- **Encoders Only**: Only quadrature encoders simulated (no CANcoders, limit switches, etc.)
- **No Stress Analysis**: No automatic warnings for over-torque or collisions
- **Single Subsystem**: Cannot simulate full robot with multiple subsystems
- **No Sensor Noise**: Encoder feedback is perfect (no noise or drift)

---

## Future Enhancements

- Automated STEP import via FreeCAD subprocess
- Stress monitoring and failure warnings
- Additional sensor types (limit switches, potentiometers, CANcoders)
- Material property estimation from CAD
- Multi-subsystem simulation (full robot)
- Web-based visualization
- PID tuning interface
- Data logging and replay

---

## Technical Details

### Motor Torque Calculation

SubsystemSim uses physics-based DC motor models:

```
Back-EMF:    ε = Kv * ω
Current:     I = (V - ε) / R
Motor Torque: τ_motor = Kt * I
Output Torque: τ_out = τ_motor * gear_ratio * 0.8  (80% efficiency)
```

Where:
- `Kv` = velocity constant (rad/s per volt)
- `Kt` = torque constant (Nm per amp)
- `R` = resistance (ohms)

All calculated from motor spec sheets (free speed, stall torque, stall current).

### Encoder Simulation

Encoder ticks calculated from joint angle:

```python
ticks = int((angle_radians / (2 * π)) * ticks_per_revolution)
```

Written to HAL via `EncoderSim.setCount(ticks)`.

### Simulation Loop

```
1. Read PWM from HAL: hal.simulation.PWMSim(port).getSpeed()
2. Convert to voltage: voltage = pwm * 12.0
3. Calculate torque: motor.calculate_torque(voltage, velocity, gear_ratio)
4. Apply to PyBullet: setJointMotorControl2(TORQUE_CONTROL, force=torque)
5. Step physics: stepSimulation()
6. Read joint angle: getJointState(joint_index)
7. Write encoder: EncoderSim.setCount(ticks)
```

Runs at ~50 Hz (pyfrc default), PyBullet substeps at 240 Hz.

---

## Credits

**Project**: ICS4U Summative (SubsystemSim)
**Author**: Sadra
**Date**: January 2026
**Technologies**: Python, PyBullet, RobotPy, URDF

**References**:
- [PyBullet Documentation](https://pybullet.org/)
- [RobotPy Documentation](https://robotpy.readthedocs.io/)
- [URDF Format Specification](http://wiki.ros.org/urdf/XML)
- [FRC Motor Specs](https://www.vexrobotics.com/motors.html)

---

## License

This project is for educational purposes (ICS4U course).
