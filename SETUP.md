# SubsystemSim Setup Guide

## Quick Start (Day 1)

### 1. Create Python Virtual Environment

```bash
# Create venv with Python 3.11 (or 3.10+)
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### 2. Install Core Dependencies

```bash
# Install minimum dependencies for Day 1 test
pip install pybullet numpy

# OR install all dependencies at once
pip install -r requirements.txt
```

**Note**: RobotPy installation may take several minutes as it compiles native extensions.

### 3. Test PyBullet Installation

```bash
python tests/test_pybullet.py
```

You should see:
- A PyBullet GUI window opens
- A red cube and green sphere fall and bounce
- Console shows falling positions every 0.25s
- Press Ctrl+C to stop

### 4. Verify Project Structure

```
ICS4U-Summative/
├── subsystemsim/
│   ├── core/          ✓ Created
│   ├── physics/       ✓ Created (engine.py exists)
│   ├── hal_bridge/    ✓ Created
│   └── importers/     ✓ Created
├── examples/
│   └── simple_arm/    ✓ Created
├── requirements.txt   ✓ Created
└── test_pybullet.py   ✓ Created
```

## Troubleshooting

### Python Version
SubsystemSim requires Python 3.10 or newer. Check with:
```bash
python --version
```

### PyBullet GUI Not Showing
If you're on a headless server or WSL without X11:
- Edit `test_pybullet.py` line 18: change `gui=True` to `gui=False`
- The simulation will run without visualization

### Import Errors
Make sure you're in the project root directory:
```bash
cd C:\Users\sadra\ICS4U\ICS4U-Summative
python test_pybullet.py
```

## Next Steps

Once `test_pybullet.py` runs successfully:
- **Day 1 Complete**: PyBullet rendering verified ✓
- **Day 2**: Implement data model classes (see plan)
