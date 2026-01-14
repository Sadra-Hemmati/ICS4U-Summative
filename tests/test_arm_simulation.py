"""
Day 4 Test: Load arm from URDF and control with motor models.

This script demonstrates:
1. Loading arm configuration from JSON
2. Generating URDF from the model
3. Loading URDF into PyBullet
4. Applying motor torques to joints
5. Simulating realistic motor physics
"""

import sys
import time
import math
from pathlib import Path

# Get project root and add to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.core.config import load_config
from subsystemsim.physics.urdf_generator import generate_urdf
from subsystemsim.physics.engine import PhysicsEngine
from subsystemsim.physics.actuators import DCMotor


def main():
    print("=== Arm Simulation Test (Day 4) ===\n")

    # 1. Load arm configuration
    print("1. Loading arm configuration...")
    config_path = project_root / "examples/simple_arm/arm_config.json"
    model = load_config(config_path)
    print(f"   Loaded: {model}\n")

    # 2. Generate URDF
    print("2. Generating URDF...")
    urdf_path = generate_urdf(model, output_dir=str(project_root / "generated_urdfs"))
    print()

    # 3. Initialize physics engine
    print("3. Initializing physics engine...")
    engine = PhysicsEngine(gui=True)
    print()

    # 4. Load URDF into simulation
    print("4. Loading arm into simulation...")
    body_id = engine.load_urdf(urdf_path, name="arm", base_position=(0, 0, 0))
    print()

    # 5. Get motor from model
    shoulder_motor_config = model.motors[0]
    print(f"5. Initializing motor: {shoulder_motor_config.name}")
    motor = DCMotor(shoulder_motor_config.motor_type.value)
    gear_ratio = shoulder_motor_config.gear_ratio
    print(f"   Gear ratio: {gear_ratio}:1")
    print()

    # 6. Run simulation with motor control
    print("6. Starting simulation...")
    print("   The arm will rotate back and forth.\n")
    print("   Press Ctrl+C to stop\n")

    try:
        step_count = 0
        simulation_time = 0.0

        while True:
            # Calculate desired voltage (sinusoidal for demo)
            # Oscillate between -6V and +6V
            voltage = 6.0 * math.sin(simulation_time * 0.5)

            # Get current joint state
            position, velocity = engine.get_joint_state("arm", "shoulder")

            # Calculate torque from motor model
            torque = motor.calculate_torque(voltage, velocity, gear_ratio)

            # Apply torque to joint
            engine.apply_joint_torque("arm", "shoulder", torque)

            # Step physics
            engine.step()
            time.sleep(engine.TIMESTEP)

            # Print status every 0.5 seconds
            step_count += 1
            simulation_time += engine.TIMESTEP

            if step_count % 120 == 0:  # 120 steps ~ 0.5s
                position_deg = position * 180 / math.pi
                velocity_rpm = velocity * 60 / (2 * math.pi)
                print(f"t={simulation_time:5.2f}s: "
                      f"V={voltage:5.2f}V, "
                      f"pos={position_deg:6.1f}deg, "
                      f"vel={velocity_rpm:6.1f} RPM, "
                      f"T={torque:6.2f} Nm")

    except KeyboardInterrupt:
        print("\n\nStopping simulation...")

    # Cleanup
    engine.disconnect()
    print("\n[OK] Day 4 test complete: Motor control working!\n")


if __name__ == "__main__":
    main()
