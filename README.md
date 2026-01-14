# SubsystemSim - FRC Subsystem Simulator

A physics-based simulator for FRC robot subsystems that runs real robot code **without modifications**.

## Features

- **Language Agnostic**: Works with Java, C++, and Python robot code via HAL WebSocket
- **CAD Import**: Load STEP files and visually define links and joints
- **Realistic Physics**: DC motor models (NEO, CIM, Falcon, etc.) with PyBullet simulation
- **No Code Changes**: Robot code runs unchanged against physics simulation

## Quick Start

### 1. Install (Conda Required)

```bash
# Install Miniconda from https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda env create -f environment.yml

# Activate
conda activate subsystemsim
```

See [SETUP_CONDA.md](SETUP_CONDA.md) for detailed instructions.

### 2. Run the GUI

```bash
conda activate subsystemsim
python subsystemsim_app.py
```

### 3. Run with Robot Code

**Terminal 1 - Start SubsystemSim:**
```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json
```

**Terminal 2 - Start Robot Code:**
```bash
# Python
cd examples/simple_arm
python -m robotpy sim --ws-server

# Java/C++
cd your_robot_project
gradlew simulateJava -Phalsim
```

## Architecture

```
Robot Code (Java/C++/Python)
        │
        │ HAL WebSocket (port 3300)
        │ - PWM motor commands
        │ - Encoder feedback
        ▼
SubsystemSim WebSocket Bridge
        │
        │ Motor physics + URDF
        ▼
PyBullet Physics Engine
```

## Project Structure

```
subsystemsim/
├── core/           # Data models (Link, Joint, Motor, Sensor)
├── physics/        # PyBullet engine, URDF generation, motor models
├── hal_bridge/     # WebSocket bridge for robot code integration
└── cad/            # CAD import (STEP → OBJ)

examples/
└── simple_arm/     # Working example with Python robot code

tests/              # Unit tests
```

## Documentation

- [SETUP_CONDA.md](SETUP_CONDA.md) - Installation guide
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Technical details for developers

## Requirements

- Python 3.11
- Conda (for pythonocc-core)
- See `environment.yml` for full dependency list

## License

Educational project for ICS4U course.
