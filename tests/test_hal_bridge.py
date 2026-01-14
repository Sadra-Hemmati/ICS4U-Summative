"""
Test 7: HAL Bridge Initialization

Tests the WPILib HAL bridge to ensure:
- Model loading works
- URDF generation works
- PyBullet initialization works
- Motor models are created correctly
- Sensor mappings are created correctly
- update_sim() loop functions without errors
"""

from pathlib import Path
import sys
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.hal_bridge.physics_interface import SubsystemPhysicsEngine


class MockPhysicsController:
    """
    Mock pyfrc PhysicsController for testing.

    In real pyfrc, this provides access to HAL simulation objects.
    For testing, we just need it to exist.
    """
    pass


def test_hal_bridge_initialization():
    """Test that HAL bridge initializes correctly."""
    print("\n" + "="*60)
    print("Test 7: HAL Bridge Initialization")
    print("="*60 + "\n")

    # Get config path
    config_path = project_root / "examples/simple_arm/arm_config.json"

    print("Step 1: Creating HAL bridge with mock physics controller...")
    try:
        engine = SubsystemPhysicsEngine(MockPhysicsController(), str(config_path))
        print("[OK] HAL bridge created successfully\n")
    except Exception as e:
        print(f"[FAILED] Failed to create HAL bridge: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verify components were initialized
    print("\nStep 2: Verifying components...")

    # Check model
    if engine.model is None:
        print("[FAILED] Model not loaded")
        return False
    print(f"[OK] Model loaded: {engine.model.name}")
    print(f"  - {len(engine.model.links)} links")
    print(f"  - {len(engine.model.joints)} joints")
    print(f"  - {len(engine.model.motors)} motors")
    print(f"  - {len(engine.model.sensors)} sensors")

    # Check physics engine
    if engine.engine is None:
        print("[FAILED] Physics engine not initialized")
        return False
    print(f"[OK] Physics engine initialized")

    # Check motors
    if len(engine.motors) == 0:
        print("[FAILED] No motors initialized")
        return False
    print(f"[OK] {len(engine.motors)} motor(s) initialized:")
    for joint_name, (motor, gear_ratio, hal_port) in engine.motors.items():
        print(f"  - Joint '{joint_name}': {motor.motor_type}, "
              f"gear_ratio={gear_ratio}, HAL port {hal_port}")

    # Check sensors
    if len(engine.sensors) == 0:
        print("[FAILED] No sensors initialized")
        return False
    print(f"[OK] {len(engine.sensors)} sensor(s) initialized:")
    for joint_name, (hal_ports, ticks_per_rev) in engine.sensors.items():
        print(f"  - Joint '{joint_name}': DIO ports {hal_ports}, "
              f"{ticks_per_rev} ticks/rev")

    print("\n" + "-"*60)
    print("Step 3: Testing update_sim() loop...")
    print("-"*60 + "\n")

    # Run a few simulation steps without HAL
    # (HAL commands will be 0.0 since HAL not available, but physics should still work)
    print("Running 5 simulation steps with zero motor commands...")
    print("(This verifies the simulation loop runs without crashing)\n")

    start_time = time.time()
    for i in range(5):
        now = time.time() - start_time
        tm_diff = 0.02  # 20ms timestep

        try:
            engine.update_sim(now, tm_diff)

            # Get joint state to verify it's working
            for joint_name in engine.motors.keys():
                position, velocity = engine.engine.get_joint_state(
                    engine.model.name,
                    joint_name
                )
                print(f"Step {i+1}: Joint '{joint_name}' - "
                      f"pos={position:.4f} rad ({position*57.3:.1f}deg), "
                      f"vel={velocity:.4f} rad/s")

        except Exception as e:
            print(f"[FAILED] update_sim() failed on step {i+1}: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n[OK] update_sim() loop completed successfully")

    # Cleanup
    print("\nStep 4: Cleaning up...")
    engine.engine.disconnect()
    print("[OK] Physics engine disconnected")

    print("\n" + "="*60)
    print("TEST 7: PASSED [OK]")
    print("="*60)
    print("\nThe HAL bridge is ready for full WPILib integration!")
    print("\nNext step: Run full simulation with robot code:")
    print("  python -m pyfrc sim examples/simple_arm/robot.py")
    print("\n")

    return True


if __name__ == "__main__":
    success = test_hal_bridge_initialization()
    sys.exit(0 if success else 1)
