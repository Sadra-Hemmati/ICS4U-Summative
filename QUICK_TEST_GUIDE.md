# Quick Test Guide - Run These Tests Now

Follow these tests in order. Mark each as you complete it.

---

## Phase 1: Core Components (Foundation)

These verify your physics engine works correctly.

### ✅ Test 1: PyBullet Rendering
```bash
python tests/test_pybullet.py
```
**Expected:** PyBullet window opens, cube falls
**Duration:** 5 seconds
**Pass if:** Cube falls smoothly under gravity

---

### ✅ Test 2: Data Model
```bash
python -c "from subsystemsim.core.model import SubsystemModel; from subsystemsim.core.config import load_config; model = load_config('examples/simple_arm/arm_config.json'); print('✓ Model loaded:', model.name); print('✓ Validation:', model.validate())"
```
**Expected:** Prints model info, validation = True
**Pass if:** No errors, validation returns (True, "")

---

### ✅ Test 3: URDF Generation
```bash
python regenerate_urdf.py
```
**Expected:** Creates/updates `generated_urdfs/simple_arm.urdf`
**Pass if:** File exists, no errors

---

### ✅ Test 4: Motor Physics
```bash
python -c "from subsystemsim.physics.actuators import DCMotor; motor = DCMotor('neo'); torque = motor.calculate_torque(6.0, 50.0, 60.0); print(f'✓ NEO motor torque: {torque:.3f} Nm'); assert torque > 0"
```
**Expected:** Prints torque value > 0
**Pass if:** No assertion error

---

### ✅ Test 5: Joint Movement
```bash
python tests/test_joint_movement.py
```
**Expected:** Arm rotates continuously, position wraps at ±180°
**Duration:** 30 seconds (or Ctrl+C to stop)
**Pass if:**
- Arm visible and rotating
- Velocity increases
- Position wraps correctly

---

### ✅ Test 6: HAL Bridge Init
```bash
python tests/test_hal_bridge.py
```
**Expected:** Initializes physics, motors, sensors
**Pass if:** All checks pass, "TEST 7: PASSED ✓"

---

## Phase 2: GUI Tests

These verify your GUI application works.

### ✅ Test 7: GUI Launch
```bash
python subsystemsim_app.py
```
**Expected:** Window opens with 4 tabs
**Pass if:**
- Window appears
- All tabs visible (CAD Import, Configuration, Robot Code, Run Simulation)
- No errors

**Don't close yet - continue to Test 8**

---

### ✅ Test 8: Load Example
**In the GUI (keep it open from Test 7):**
1. Menu → Examples → Load Simple Arm Example
2. Check all tabs populate

**Expected:**
- CAD Import: Shows 2 files (base.obj, arm.obj)
- Configuration: JSON editor shows config
- Robot Code: Shows path to examples/simple_arm
- Popup confirms success

**Pass if:** All tabs show data, no errors

---

### ✅ Test 9: Config Validation
**In the GUI (still open):**
1. Go to Configuration tab
2. Click "Validate" button

**Expected:** Popup says "Configuration is valid!" with counts
**Pass if:** Validation passes

---

### ✅ Test 10: STEP Converter Button
**In the GUI:**
1. Go to CAD Import tab
2. Click "Convert STEP Online →"

**Expected:**
- Popup with instructions
- Browser opens to https://convert3d.org/step-to-obj
- Website loads correctly

**Pass if:** Website opens and is a STEP converter

**You can close the GUI now**

---

## Phase 3: WebSocket Bridge

### ✅ Test 11: WebSocket Bridge Standalone
```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json
```

**Expected:**
- Prints initialization messages
- PyBullet window opens showing arm
- "Waiting for WebSocket connection..."
- No errors

**Pass if:** Bridge starts, PyBullet visible, waits for connection

**Press Ctrl+C to stop**

---

## Quick Results Checklist

Mark each test:

**Phase 1 - Core:**
- [ ] Test 1: PyBullet Rendering
- [ ] Test 2: Data Model
- [ ] Test 3: URDF Generation
- [ ] Test 4: Motor Physics
- [ ] Test 5: Joint Movement
- [ ] Test 6: HAL Bridge Init

**Phase 2 - GUI:**
- [ ] Test 7: GUI Launch
- [ ] Test 8: Load Example
- [ ] Test 9: Config Validation
- [ ] Test 10: STEP Converter

**Phase 3 - WebSocket:**
- [ ] Test 11: WebSocket Bridge

---

## If Any Test Fails

**Don't panic!** Report what happened:
1. Which test?
2. What error message?
3. What did you see?

I'll help you fix it.

---

## After All Tests Pass

You'll be ready to:
1. Practice your demo workflow
2. Prepare talking points
3. Test with Java code (optional)

---

## Estimated Time

- Phase 1: ~5 minutes
- Phase 2: ~5 minutes
- Phase 3: ~2 minutes

**Total: ~12 minutes** to verify everything works!

---

**Start with Test 1 now!** Run:
```bash
python tests/test_pybullet.py
```

Let me know when you complete it or if anything fails.
