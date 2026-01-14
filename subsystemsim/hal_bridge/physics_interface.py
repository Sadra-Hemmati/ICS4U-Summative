"""
WPILib HAL bridge for SubsystemSim.

Implements the PhysicsEngine interface expected by pyfrc to integrate
PyBullet simulation with real WPILib robot code.

This file is the core integration point:
- Reads motor commands from HAL (via robot code)
- Applies torques to PyBullet joints
- Reads joint states from PyBullet
- Writes encoder values back to HAL
"""

from pathlib import Path
from typing import Dict, Optional
import math

# WPILib imports (will be available when robot code runs)
try:
    import hal
    import hal.simulation
    HAL_AVAILABLE = True
except ImportError:
    print("Warning: WPILib HAL not available. Install with: pip install robotpy[all]")
    HAL_AVAILABLE = False

from ..core.config import load_config
from ..core.model import SubsystemModel, Motor, Sensor
from ..physics.urdf_generator import generate_urdf
from ..physics.engine import PhysicsEngine
from ..physics.actuators import DCMotor


class SubsystemPhysicsEngine:
    """
    Physics engine for pyfrc simulation.

    This class implements the interface that pyfrc expects:
    - __init__(physics_controller)
    - update_sim(now, tm_diff)

    It bridges WPILib HAL <-> PyBullet simulation.
    """

    def __init__(self, physics_controller, config_path: str):
        """
        Initialize physics engine for simulation.

        Args:
            physics_controller: pyfrc PhysicsController object (provides HAL access)
            config_path: Path to subsystem JSON config file
        """
        self.hal = physics_controller  # Store for HAL access
        config_path = Path(config_path)

        print("\n=== Initializing SubsystemSim Physics Engine ===")
        print(f"Config: {config_path}\n")

        # 1. Load subsystem model
        self.model = load_config(config_path)
        print(f"Loaded model: {self.model}\n")

        # 2. Generate URDF
        # Use absolute path for output directory to avoid path resolution issues
        # Place generated URDFs in project root, not relative to cwd
        config_abs_path = Path(config_path).absolute()
        project_root = config_abs_path.parent.parent.parent  # Go up from examples/simple_arm/config
        urdf_output_dir = project_root / "generated_urdfs"
        urdf_path = generate_urdf(self.model, output_dir=str(urdf_output_dir))
        print()

        # 3. Initialize PyBullet
        self.engine = PhysicsEngine(gui=True)
        body_id = self.engine.load_urdf(urdf_path, name=self.model.name)
        print()

        # 4. Create motor models
        print("Initializing motor models...")
        self.motors: Dict[str, tuple] = {}  # joint_name -> (DCMotor, gear_ratio, hal_port)

        for motor_config in self.model.motors:
            dc_motor = DCMotor(motor_config.motor_type.value)
            self.motors[motor_config.joint_name] = (
                dc_motor,
                motor_config.gear_ratio,
                motor_config.hal_port
            )
            print(f"  - {motor_config.name} on joint '{motor_config.joint_name}' "
                  f"(HAL port {motor_config.hal_port})")
        print()

        # 5. Create sensor mappings
        print("Initializing sensor mappings...")
        self.sensors: Dict[str, tuple] = {}  # joint_name -> (hal_ports, ticks_per_rev)

        for sensor_config in self.model.sensors:
            if sensor_config.sensor_type == "encoder":
                self.sensors[sensor_config.joint_name] = (
                    sensor_config.hal_ports,
                    sensor_config.ticks_per_revolution
                )
                print(f"  - {sensor_config.name} on joint '{sensor_config.joint_name}' "
                      f"(DIO ports {sensor_config.hal_ports})")
        print()

        print("[OK] SubsystemSim ready!\n")

    def update_sim(self, now: float, tm_diff: float):
        """
        Called by pyfrc every simulation tick (~20ms).

        This is the main simulation loop:
        1. Read motor commands from HAL
        2. Calculate torques using motor models
        3. Apply torques to PyBullet joints
        4. Step physics simulation
        5. Read joint states from PyBullet
        6. Write encoder values back to HAL

        Args:
            now: Current simulation time (seconds)
            tm_diff: Time since last update (seconds)
        """
        # 1 & 2 & 3: Read motor commands and apply torques
        for joint_name, (motor, gear_ratio, hal_port) in self.motors.items():
            # Read PWM value from HAL (-1.0 to 1.0)
            if HAL_AVAILABLE:
                try:
                    pwm_sim = hal.simulation.PWMSim(hal_port)
                    pwm_value = pwm_sim.getSpeed()  # -1.0 to 1.0
                except Exception as e:
                    # Fallback if HAL not properly initialized
                    pwm_value = 0.0
            else:
                pwm_value = 0.0  # No motor command if HAL not available

            # Convert PWM to voltage
            voltage = pwm_value * 12.0  # FRC nominal voltage

            # Get current joint state
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # Calculate torque using motor model
            torque = motor.calculate_torque(voltage, velocity, gear_ratio)

            # Apply to PyBullet
            self.engine.apply_joint_torque(self.model.name, joint_name, torque)

        # 4: Step physics simulation
        # Calculate number of sub-steps for stability
        num_substeps = max(1, int(tm_diff / self.engine.TIMESTEP))
        self.engine.step(num_substeps)

        # 5 & 6: Read joint states and write encoder values
        for joint_name, (hal_ports, ticks_per_rev) in self.sensors.items():
            # Get joint position (radians)
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # Convert to encoder ticks
            ticks = self._angle_to_ticks(position, ticks_per_rev)

            # Write to HAL
            if HAL_AVAILABLE and len(hal_ports) >= 2:
                try:
                    # Create encoder simulation for the DIO ports
                    encoder_sim = hal.simulation.EncoderSim.createForChannel(hal_ports[0])
                    encoder_sim.setCount(ticks)
                    # Also set distance for integrated encoders
                    encoder_sim.setDistance(position)  # In radians
                except Exception as e:
                    pass  # Silently fail if encoder not initialized yet

    def _angle_to_ticks(self, angle_radians: float, ticks_per_rev: int) -> int:
        """
        Convert angle in radians to encoder ticks.

        Args:
            angle_radians: Joint angle in radians
            ticks_per_rev: Encoder resolution (ticks per revolution)

        Returns:
            Encoder tick count
        """
        revolutions = angle_radians / (2 * math.pi)
        ticks = int(revolutions * ticks_per_rev)
        return ticks


# For standalone testing
if __name__ == "__main__":
    print("=== Testing HAL Bridge ===\n")
    print("Note: Full testing requires running with pyfrc.\n")
    print("For now, we'll test model loading and initialization.\n")

    # Create a mock physics controller
    class MockPhysicsController:
        pass

    # Test initialization
    try:
        config_path = "examples/simple_arm/arm_config.json"
        engine = SubsystemPhysicsEngine(MockPhysicsController(), config_path)
        print("[OK] HAL bridge initialized successfully!")
        print("\nTo test with real robot code, run:")
        print("  python -m pyfrc sim examples/simple_arm/robot.py")
    except Exception as e:
        print(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()
