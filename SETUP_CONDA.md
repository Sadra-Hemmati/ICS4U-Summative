# SubsystemSim - Conda Setup Guide

This guide walks you through switching from venv to conda for SubsystemSim.

---

## Why Conda?

SubsystemSim now uses **PythonOCC** for advanced CAD import (STEP files with assembly structure). PythonOCC requires OpenCASCADE libraries that are only available via conda.

---

## Step-by-Step Setup

### Step 1: Install Miniconda (if not already installed)

**Download Miniconda:**
- Go to: https://docs.conda.io/en/latest/miniconda.html
- Download: **Miniconda3 Windows 64-bit**
- Run the installer

**During installation:**
- Install for "Just Me" (recommended)
- Use default install location: `C:\Users\YourName\miniconda3`
- **IMPORTANT:** Check "Add Miniconda3 to my PATH environment variable"
- Check "Register Miniconda3 as my default Python"

**Verify installation** (open NEW terminal):
```bash
conda --version
```
Should show something like: `conda 24.x.x`

---

### Step 2: Create the SubsystemSim Environment

Open a terminal in the project directory:

```bash
cd C:\Users\sadra\ICS4U\ICS4U-Summative
```

Create the environment from the yml file:

```bash
conda env create -f environment.yml
```

This will:
- Create a new environment named `subsystemsim`
- Install Python 3.11
- Install pythonocc-core 7.9.0 (CAD library)
- Install all pip dependencies (pybullet, robotpy, etc.)

**This may take 5-10 minutes** - conda needs to download ~500MB of packages.

---

### Step 3: Activate the Environment

```bash
conda activate subsystemsim
```

Your prompt should change to show `(subsystemsim)` at the start.

**Verify everything installed:**
```bash
python -c "from OCC.Core.STEPControl import STEPControl_Reader; print('PythonOCC OK')"
python -c "import pybullet; print('PyBullet OK')"
python -c "import websockets; print('WebSockets OK')"
```

All three should print "OK".

---

### Step 4: Delete Old venv (Optional but Recommended)

Once conda is working, you can delete the old virtual environment:

```bash
# From project directory
rmdir /s /q venv
```

Or just delete the `venv` folder manually in File Explorer.

---

### Step 5: Test the Application

```bash
conda activate subsystemsim
python subsystemsim_app.py
```

The GUI should launch. Try loading the simple arm example.

---

## Daily Usage

Every time you open a new terminal to work on SubsystemSim:

```bash
conda activate subsystemsim
cd C:\Users\sadra\ICS4U\ICS4U-Summative
python subsystemsim_app.py
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Activate environment | `conda activate subsystemsim` |
| Deactivate environment | `conda deactivate` |
| List environments | `conda env list` |
| Update all packages | `conda update --all` |
| Install new pip package | `pip install package_name` |
| Install new conda package | `conda install package_name` |
| Delete environment | `conda env remove -n subsystemsim` |
| Recreate from yml | `conda env create -f environment.yml` |

---

## Troubleshooting

### "conda is not recognized"

Miniconda wasn't added to PATH. Either:
1. Reinstall Miniconda with "Add to PATH" checked, OR
2. Use "Anaconda Prompt" from Start Menu instead of regular terminal

### "Solving environment: failed"

Channel priority issue. Run:
```bash
conda config --set channel_priority flexible
conda env create -f environment.yml
```

### "pythonocc-core not found"

Make sure conda-forge channel is added:
```bash
conda config --add channels conda-forge
conda install pythonocc-core=7.9.0
```

### Import errors after installation

Make sure you activated the environment:
```bash
conda activate subsystemsim
```

Check you're using the right Python:
```bash
where python
```
Should show path inside `miniconda3\envs\subsystemsim\`

---

## For Other Developers

To set up this project on a new machine:

```bash
# Clone the repository
git clone <repo-url>
cd ICS4U-Summative

# Create conda environment
conda env create -f environment.yml

# Activate and run
conda activate subsystemsim
python subsystemsim_app.py
```

---

## Environment Structure

After setup, your project uses:

```
C:\Users\sadra\miniconda3\envs\subsystemsim\
    ├── python.exe          (Python 3.11)
    ├── Lib\
    │   └── site-packages\
    │       ├── OCC\        (PythonOCC - CAD library)
    │       ├── pybullet\   (Physics engine)
    │       ├── websockets\ (WebSocket client)
    │       └── ...
    └── Scripts\
        └── pip.exe
```

The old `venv\` folder in your project is no longer needed.
