"""
Simple test: Apply constant torque to see if joint can move at all.

This test demonstrates angle wrapping: the reported position wraps to
the (-180deg, 180deg] range, allowing continuous rotation without limit
constraints interfering.
"""

import sys
import time
from pathlib import Path

# Get project root and add to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.physics.engine import PhysicsEngine
import pybullet as p

# Initialize engine
engine = PhysicsEngine(gui=True)

# Load arm URDF
urdf_path = str(project_root / "generated_urdfs/simple_arm.urdf")
body_id = engine.load_urdf(urdf_path, name="arm")

print("\n=== Joint Movement Test with Angle Wrapping ===")
print("Applying constant 1.0 Nm torque to shoulder joint...")
print("Position wraps to (-180deg, 180deg] range for continuous rotation.\n")

try:
    step = 0
    while True:
        # Apply constant torque
        engine.apply_joint_torque("arm", "shoulder", 1.0)

        # Step simulation
        engine.step()
        time.sleep(engine.TIMESTEP)

        # Print status every 0.5 seconds
        step += 1
        if step % 120 == 0:
            pos, vel = engine.get_joint_state("arm", "shoulder")
            time_s = step / 240.0
            print(f"t={time_s:5.2f}s: pos={pos:7.3f} rad ({pos*57.3:7.1f}deg), vel={vel:6.3f} rad/s")

except KeyboardInterrupt:
    print("\nStopping...")

engine.disconnect()
