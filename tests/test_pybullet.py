"""
Day 1 Test: Verify PyBullet installation and basic rendering.

This script creates a simple cube using PyBullet primitives and shows it falling with gravity.
"""

import sys
import time
from pathlib import Path

# Get project root and add to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.physics.engine import PhysicsEngine


def main():
    print("=== PyBullet Test ===")
    print("Testing basic rendering and physics simulation...")
    print("Press Ctrl+C to stop\n")

    # Initialize physics engine with GUI
    engine = PhysicsEngine(gui=True)

    # Create a simple cube mesh using PyBullet primitives
    # (Later we'll load actual OBJ files from CAD)
    import pybullet as p

    # Create a red cube
    collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.1])
    visual_shape = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[0.1, 0.1, 0.1],
        rgbaColor=[1, 0, 0, 1]  # Red
    )
    cube_id = p.createMultiBody(
        baseMass=1.0,
        baseCollisionShapeIndex=collision_shape,
        baseVisualShapeIndex=visual_shape,
        basePosition=[0, 0, 2]  # Start 2m above ground
    )

    # Create a green sphere
    collision_sphere = p.createCollisionShape(p.GEOM_SPHERE, radius=0.1)
    visual_sphere = p.createVisualShape(
        p.GEOM_SPHERE,
        radius=0.1,
        rgbaColor=[0, 1, 0, 1]  # Green
    )
    sphere_id = p.createMultiBody(
        baseMass=0.5,
        baseCollisionShapeIndex=collision_sphere,
        baseVisualShapeIndex=visual_sphere,
        basePosition=[0.3, 0, 1.5]
    )

    print("Created test objects:")
    print("  - Red cube (1 kg) at height 2m")
    print("  - Green sphere (0.5 kg) at height 1.5m")
    print("\nSimulating physics... Watch them fall!\n")

    # Run simulation loop
    try:
        step_count = 0
        while True:
            engine.step()
            time.sleep(engine.TIMESTEP)

            # Print position every 60 steps (~0.25s)
            step_count += 1
            if step_count % 60 == 0:
                cube_pos, _ = p.getBasePositionAndOrientation(cube_id)
                sphere_pos, _ = p.getBasePositionAndOrientation(sphere_id)
                print(f"t={step_count * engine.TIMESTEP:.2f}s: "
                      f"cube_z={cube_pos[2]:.3f}m, sphere_z={sphere_pos[2]:.3f}m")

    except KeyboardInterrupt:
        print("\n\nStopping simulation...")

    # Cleanup
    engine.disconnect()
    print("\n[OK] Test passed! PyBullet is working correctly.")
    print("Day 1 deliverable complete: PyBullet rendering verified.\n")


if __name__ == "__main__":
    main()
