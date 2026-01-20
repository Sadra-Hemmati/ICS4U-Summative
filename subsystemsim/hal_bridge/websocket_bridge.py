"""
HAL WebSocket Bridge for SubsystemSim.

This bridge enables SubsystemSim to work with robot code written in ANY language
(Java, C++, or Python) by connecting to the WPILib HAL simulation WebSocket protocol.

Architecture:
1. Robot code runs with HALSIM_WS extension (creates WebSocket server)
2. This script connects as a WebSocket client
3. Subscribes to motor PWM outputs
4. Publishes encoder/sensor inputs
5. Runs PyBullet physics simulation

This replaces the pyfrc-specific physics.py approach and works universally.
"""

import asyncio
import websockets
import json
import time
import gc
import re
from pathlib import Path
from typing import Dict, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.core.config import load_config
from subsystemsim.core.warnings import WarningSystem, WarningType
from subsystemsim.physics.urdf_generator import generate_urdf
from subsystemsim.physics.engine import PhysicsEngine
from subsystemsim.physics.actuators import DCMotor


class HALWebSocketBridge:
    """
    WebSocket client that bridges WPILib HAL simulation to PyBullet physics.

    Connects to robot code (any language) via HAL sim WebSocket protocol.
    """

    # Pre-compiled regex patterns for CAN ID parsing (performance optimization)
    _RE_BRACKET = re.compile(r'\[(\d+)\]')  # [5], [12]
    _RE_DASH = re.compile(r'[-–]\s*(\d+)')  # - 1, – 1
    _RE_SPACE_NUM = re.compile(r'\s(\d+)(?:\s|$)')  # " 5" at end

    def __init__(self, config_path: str, ws_uri: str = "ws://localhost:3300/wpilibws"):
        """
        Initialize WebSocket bridge.

        Args:
            config_path: Path to subsystem JSON config
            ws_uri: WebSocket URI for HAL sim server (default: ws://localhost:3300/wpilibws)
        """
        self.ws_uri = ws_uri
        self.websocket = None
        self.running = False
        self._msg_count = 0  # For debug logging rate limiting

        print("\n" + "="*70)
        print("SubsystemSim HAL WebSocket Bridge")
        print("="*70)
        print(f"Config: {config_path}")
        print(f"WebSocket URI: {ws_uri}\n")

        # Load subsystem model
        print("Loading subsystem model...")
        self.model = load_config(config_path)
        print(f"[OK] Loaded: {self.model}\n")

        # Generate URDF
        print("Generating URDF...")
        # Use relative path from current working directory
        # This works whether config is in project or external
        urdf_output_dir = Path("generated_urdfs")
        urdf_path = generate_urdf(self.model, output_dir=str(urdf_output_dir))
        print(f"[OK] URDF: {urdf_path}\n")

        # Initialize PyBullet
        print("Initializing PyBullet physics engine...")
        self.engine = PhysicsEngine(gui=True)
        self.engine.load_urdf(urdf_path, name=self.model.name)
        print("[OK] Physics engine ready\n")

        # Initialize warning system (can be connected to GUI via callbacks)
        self.warnings = WarningSystem(history_size=100, rate_limit_seconds=1.0)

        # Create motor models - separate mappings for PWM and CAN
        # tuple: (joint_name, DCMotor, gear_ratio, inverted, drum_radius, is_prismatic, effort_limit)
        print("Initializing motor models...")
        self.pwm_motors: Dict[int, tuple] = {}
        self.can_motors: Dict[int, tuple] = {}

        # Track effort limits per joint (for force clamping when multiple motors drive same joint)
        self.joint_effort_limits: Dict[str, float] = {}

        for motor_config in self.model.motors:
            dc_motor = DCMotor(motor_config.motor_type.value)
            inverted = getattr(motor_config, 'inverted', False)
            controller_type = getattr(motor_config, 'controller_type', 'pwm')
            drum_radius = getattr(motor_config, 'drum_radius', 0.019)

            # Check if the joint is prismatic and get effort_limit
            joint = self.model.get_joint(motor_config.joint_name)
            is_prismatic = joint and joint.joint_type.value == "prismatic"
            effort_limit = joint.effort_limit if joint else 100.0

            # Store effort limit for this joint
            self.joint_effort_limits[motor_config.joint_name] = effort_limit

            motor_tuple = (
                motor_config.joint_name,
                dc_motor,
                motor_config.gear_ratio,
                inverted,
                drum_radius,
                is_prismatic,
                effort_limit
            )

            if controller_type == "can":
                self.can_motors[motor_config.hal_port] = motor_tuple
                joint_type_str = "prismatic" if is_prismatic else "revolute"
                print(f"  CAN[{motor_config.hal_port}] -> {motor_config.joint_name} "
                      f"({motor_config.motor_type.value}, ratio={motor_config.gear_ratio}, {joint_type_str}, limit={effort_limit}N)")
            else:
                self.pwm_motors[motor_config.hal_port] = motor_tuple
                joint_type_str = "prismatic" if is_prismatic else "revolute"
                print(f"  PWM[{motor_config.hal_port}] -> {motor_config.joint_name} "
                      f"({motor_config.motor_type.value}, ratio={motor_config.gear_ratio}, {joint_type_str}, limit={effort_limit}N)")
        print()

        # Create sensor mappings
        print("Initializing sensor mappings...")
        self.encoders: Dict[int, tuple] = {}  # dio_port -> (joint_name, ticks_per_rev)
        for sensor_config in self.model.sensors:
            if sensor_config.sensor_type == "encoder" and len(sensor_config.hal_ports) >= 1:
                dio_port = sensor_config.hal_ports[0]  # Use first DIO port as ID
                self.encoders[dio_port] = (
                    sensor_config.joint_name,
                    sensor_config.ticks_per_revolution
                )
                print(f"  Encoder[{dio_port}] -> {sensor_config.joint_name} "
                      f"({sensor_config.ticks_per_revolution} ticks/rev)")
        print()

        # Motor command storage (values from robot code)
        self.pwm_commands: Dict[int, float] = {port: 0.0 for port in self.pwm_motors.keys()}
        self.can_commands: Dict[int, float] = {can_id: 0.0 for can_id in self.can_motors.keys()}

        # Encoder state tracking for delta-based updates
        self.last_encoder_count: Dict[int, int] = {port: 0 for port in self.encoders.keys()}
        # Initialize all encoders as "initialized" to start sending data immediately
        self.encoder_initialized: Dict[int, bool] = {port: True for port in self.encoders.keys()}

        # Track seen SimDevices for debugging
        self._seen_sim_devices: set = set()

        # Simulation timing
        self.last_update = time.time()
        self.sim_rate = 50  # Hz (20ms per update)

        total_motors = len(self.pwm_motors) + len(self.can_motors)
        print("="*70)
        print("Bridge initialized! Waiting for WebSocket connection...")
        print(f"Physics ready for model '{self.model.name}' with {total_motors} motors and {len(self.encoders)} encoders")
        print(f"  PWM motors: {list(self.pwm_motors.keys())}")
        print(f"  CAN motors: {list(self.can_motors.keys())}")
        print("="*70 + "\n")

    async def connect(self, max_retries: int = 300, retry_delay: float = 1.0):
        """
        Connect to HAL simulation WebSocket server with retries.

        Args:
            max_retries: Maximum number of connection attempts (default 300 = ~5 minutes)
                         Robot code may take 2+ minutes to compile on first run.
            retry_delay: Delay between retries in seconds
        """
        print(f"Connecting to {self.ws_uri}...")
        print("(Waiting for robot code to start WebSocket server...)")
        print("(This may take 2+ minutes if robot code needs to compile)\n")

        for attempt in range(max_retries):
            try:
                # Simple connect without aggressive timeout
                # The websockets library has its own reasonable timeout
                self.websocket = await websockets.connect(self.ws_uri)
                print(f"\n[OK] Connected to HAL simulation WebSocket (attempt {attempt + 1})\n")
                return True
            except ConnectionRefusedError:
                # Server not listening yet - this is expected during compilation
                if attempt % 10 == 0:
                    print(f"  Waiting for WebSocket server... ({attempt + 1}s)")
            except OSError as e:
                # Various connection errors (e.g., "No route to host")
                if attempt % 10 == 0:
                    print(f"  Connection error: {e} ({attempt + 1}s)")
            except Exception as e:
                if attempt % 10 == 0:
                    print(f"  Waiting... {type(e).__name__}: {e} ({attempt + 1}s)")

            await asyncio.sleep(retry_delay)

        print(f"\n[FAILED] Could not connect after {max_retries} seconds")
        print("\nMake sure robot code is running with HAL WebSocket extension:")
        print("  Java: ./gradlew simulateJava")
        print("  C++:  ./gradlew simulateNative")
        print("  Python: python robot.py sim")
        return False

    async def subscribe_to_devices(self):
        """No subscription needed - robot code sends device states automatically."""
        print("Waiting for robot code to send device states...")
        print(f"Expecting PWM device(s): {list(self.pwm_motors.keys())}")
        print(f"Expecting CAN device(s): {list(self.can_motors.keys())}")
        print(f"Will publish Encoder device(s): {list(self.encoders.keys())}")
        print()

    def handle_message(self, message: str):
        """Handle incoming WebSocket message from robot code. Optimized for performance."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            # Fast path: Handle CAN motor commands - Phoenix 6 uses "CANMotor" type
            # This is the most common message type, so check it first
            if msg_type == "CANMotor":
                device_str = data.get("device", "")
                msg_data = data.get("data", {})

                # Only log new devices (one-time cost)
                if device_str not in self._seen_sim_devices:
                    self._seen_sim_devices.add(device_str)
                    can_id_preview = self._parse_can_id(device_str)
                    print(f"[NEW CANMotor] '{device_str}' (CAN ID: {can_id_preview})")

                # Parse CAN ID and update command
                can_id = self._parse_can_id(device_str)
                if can_id is not None and can_id in self.can_motors:
                    if "<dutyCycle" in msg_data:
                        self.can_commands[can_id] = msg_data["<dutyCycle"]
                    elif "<motorVoltage" in msg_data:
                        self.can_commands[can_id] = msg_data["<motorVoltage"] / 12.0
                return

            # Handle PWM motor commands (robot output)
            if msg_type == "PWM":
                device_str = data.get("device", "")
                try:
                    pwm_port = int(device_str)
                    if pwm_port in self.pwm_motors:
                        msg_data = data.get("data", {})
                        if "<speed" in msg_data:
                            self.pwm_commands[pwm_port] = msg_data["<speed"]
                except ValueError:
                    pass
                return

            # Handle SimDevice messages (REV SPARK MAX, etc.) - less common
            if msg_type == "SimDevice":
                device_str = data.get("device", "")
                msg_data = data.get("data", {})

                if device_str not in self._seen_sim_devices:
                    self._seen_sim_devices.add(device_str)
                    can_id_preview = self._parse_can_id(device_str)
                    print(f"[NEW SimDevice] '{device_str}' (CAN ID: {can_id_preview})")

                can_id = self._parse_can_id(device_str)

                if can_id is not None and can_id in self.can_motors:
                    if msg_data.get("<init", False):
                        print(f"[OK] CAN[{can_id}] ({device_str}) initialized by robot code")

                    # Try different field names for motor output (REV/SPARK MAX style)
                    speed = None
                    for field in ["<Applied Output", "<speed", "<Duty Cycle", "<Output"]:
                        if field in msg_data:
                            speed = msg_data[field]
                            break

                    if speed is not None:
                        self.can_commands[can_id] = speed
                        if self._msg_count % 50 == 0:
                            print(f"[MOTOR] CAN[{can_id}] = {speed:.3f}")

            # Handle Encoder initialization (robot queries)
            elif msg_type == "Encoder":
                device_str = data.get("device", "")
                try:
                    dio_port = int(device_str)

                    if dio_port in self.encoders:
                        msg_data = data.get("data", {})

                        if msg_data.get("<init", False):
                            self.encoder_initialized[dio_port] = True
                            print(f"[OK] Encoder[{dio_port}] initialized by robot code")

                except ValueError:
                    pass

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error handling message: {e}")

    def _parse_can_id(self, device_str: str) -> Optional[int]:
        """
        Parse CAN ID from device string.

        Supports various formats:
        - 'SPARK MAX [5]' -> 5
        - 'Talon FX[7]' -> 7
        - 'TalonFX Sim[1]' -> 1
        - 'Talon FX (v6) [1]' -> 1
        - 'CANSparkMax[5]' -> 5
        - 'Talon FX - 1 (v6) Sim State' -> 1
        - 'Talon FX - 1 (v6) Motor Sim' -> 1
        """
        # Use pre-compiled patterns for performance
        # Try bracket format first: [5], [12], etc.
        match = self._RE_BRACKET.search(device_str)
        if match:
            return int(match.group(1))

        # Try "- N" format (Phoenix 6 style): "Talon FX - 1 (v6)"
        match = self._RE_DASH.search(device_str)
        if match:
            return int(match.group(1))

        # Try just a number at the end after a space: "Device 5"
        match = self._RE_SPACE_NUM.search(device_str)
        if match:
            return int(match.group(1))

        return None

    async def publish_encoder_data(self):
        """Publish encoder data to robot code (delta-based updates only)."""
        for dio_port, (joint_name, ticks_per_rev) in self.encoders.items():
            # Only send data for encoders that have been initialized by robot code
            if not self.encoder_initialized[dio_port]:
                continue  # Encoder not initialized yet, skip

            # Get joint position from physics
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # Convert to encoder ticks
            revolutions = position / (2 * 3.14159)
            ticks = int(revolutions * ticks_per_rev)

            # Only send if count has changed (delta-based update)
            if ticks == self.last_encoder_count[dio_port]:
                continue  # No change, skip sending

            # Update last sent count
            self.last_encoder_count[dio_port] = ticks

            # Calculate period (time between pulses)
            # If velocity is 0, use large period; otherwise calculate from velocity
            if abs(velocity) > 0.001:  # Avoid division by zero
                rev_per_sec = abs(velocity) / (2 * 3.14159)
                pulses_per_sec = rev_per_sec * ticks_per_rev
                period = 1.0 / pulses_per_sec if pulses_per_sec > 0 else 1.0
            else:
                period = 1.0  # Stationary

            # Send encoder count via WebSocket
            # Device is just the port number as string
            # Use ">count" and ">period" (input TO robot code)
            encoder_msg = {
                "type": "Encoder",
                "device": str(dio_port),
                "data": {
                    ">count": ticks,
                    ">period": period
                }
            }

            try:
                await self.websocket.send(json.dumps(encoder_msg))
            except Exception as e:
                print(f"Error sending encoder data: {e}")
                # If send fails, connection might be dead - let it propagate
                raise

    def _check_joint_limits(self, joint_forces: Dict[str, list]):
        """
        Check if any joints are at their limits with force applied into the limit.

        Issues warnings through the warning system when detected.
        This method is designed to be called after forces are calculated
        but can check current joint state at any time.

        Args:
            joint_forces: Dict of {joint_name: [force, is_prismatic, effort_limit]}
        """
        # Tolerance for "at limit" detection (prevents false positives from float precision)
        LIMIT_TOLERANCE = 0.005  # 5mm for prismatic, 0.005 rad (~0.3 deg) for revolute

        for joint_name, (force, is_prismatic, effort_limit) in joint_forces.items():
            # Get joint configuration and current state
            joint_config = self.model.get_joint(joint_name)
            if not joint_config or joint_config.limits is None:
                continue  # No limits defined

            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)
            lower_limit, upper_limit = joint_config.limits

            # Check upper limit: position at/near upper AND force pushing upward (positive)
            at_upper = position >= (upper_limit - LIMIT_TOLERANCE)
            force_into_upper = force > 1.0  # More than 1N/Nm pushing into limit

            if at_upper and force_into_upper:
                self.warnings.warn_joint_at_limit(
                    joint_name=joint_name,
                    position=position,
                    limit=upper_limit,
                    force=force,
                    is_upper=True
                )

            # Check lower limit: position at/near lower AND force pushing downward (negative)
            at_lower = position <= (lower_limit + LIMIT_TOLERANCE)
            force_into_lower = force < -1.0  # More than 1N/Nm pushing into limit

            if at_lower and force_into_lower:
                self.warnings.warn_joint_at_limit(
                    joint_name=joint_name,
                    position=position,
                    limit=lower_limit,
                    force=force,
                    is_upper=False
                )

    def update_physics(self):
        """Update PyBullet physics simulation."""
        # Calculate time delta
        now = time.time()
        tm_diff = now - self.last_update
        self.last_update = now

        # Accumulate forces/torques per joint (for multiple motors driving same joint)
        # Structure: {joint_name: (accumulated_force, is_prismatic, effort_limit)}
        joint_forces: Dict[str, list] = {}

        # Process PWM motors
        for pwm_port, pwm_value in self.pwm_commands.items():
            joint_name, motor, gear_ratio, inverted, drum_radius, is_prismatic, effort_limit = self.pwm_motors[pwm_port]

            # Apply inversion
            if inverted:
                pwm_value = -pwm_value

            # Coast mode: when command is near zero, don't apply motor forces
            # This prevents regenerative braking from fighting gravity
            if abs(pwm_value) < 0.01:
                continue  # Skip this motor, let gravity work freely

            # Convert PWM to voltage
            voltage = pwm_value * 12.0  # FRC nominal voltage

            # Get current joint state
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # For prismatic joints, convert linear velocity to angular for motor model
            if is_prismatic:
                motor_velocity = velocity / drum_radius  # linear velocity -> angular velocity
            else:
                motor_velocity = velocity

            # Calculate torque using motor model
            torque = motor.calculate_torque(voltage, motor_velocity, gear_ratio)

            # For prismatic joints, convert torque to force
            if is_prismatic:
                force = torque / drum_radius  # torque -> linear force
            else:
                force = torque

            # Accumulate force for this joint
            if joint_name not in joint_forces:
                joint_forces[joint_name] = [0.0, is_prismatic, effort_limit]
            joint_forces[joint_name][0] += force

        # Process CAN motors
        for can_id, can_value in self.can_commands.items():
            joint_name, motor, gear_ratio, inverted, drum_radius, is_prismatic, effort_limit = self.can_motors[can_id]

            # Apply inversion
            if inverted:
                can_value = -can_value

            # Coast mode: when command is near zero, don't apply motor forces
            # This prevents regenerative braking from fighting gravity
            # Real motors have coast vs brake modes - this implements coast
            if abs(can_value) < 0.01:
                continue  # Skip this motor, let gravity work freely

            # Convert to voltage (CAN values are also -1.0 to 1.0)
            voltage = can_value * 12.0

            # Get current joint state
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # For prismatic joints, convert linear velocity to angular for motor model
            if is_prismatic:
                motor_velocity = velocity / drum_radius  # linear velocity -> angular velocity
            else:
                motor_velocity = velocity

            # Calculate torque using motor model
            torque = motor.calculate_torque(voltage, motor_velocity, gear_ratio)

            # For prismatic joints, convert torque to force
            if is_prismatic:
                force = torque / drum_radius  # torque -> linear force
            else:
                force = torque

            # Accumulate force for this joint
            if joint_name not in joint_forces:
                joint_forces[joint_name] = [0.0, is_prismatic, effort_limit]
            joint_forces[joint_name][0] += force

        # Apply accumulated and clamped forces to each joint
        for joint_name, (total_force, is_prismatic, effort_limit) in joint_forces.items():
            # Clamp force to effort limit (prevents physics instability)
            unclamped_force = total_force
            total_force = max(-effort_limit, min(effort_limit, total_force))

            # Apply the clamped force
            self.engine.apply_joint_torque(self.model.name, joint_name, total_force)

            # Store for debug output
            if not hasattr(self, '_last_applied_forces'):
                self._last_applied_forces = {}
            self._last_applied_forces[joint_name] = (unclamped_force, total_force, is_prismatic)

        # Step physics simulation
        num_substeps = max(1, int(tm_diff / self.engine.TIMESTEP))
        self.engine.step(num_substeps)

        # Check for joint limit violations (uses clamped forces from _last_applied_forces)
        # Convert _last_applied_forces to format expected by _check_joint_limits
        if hasattr(self, '_last_applied_forces'):
            forces_for_check = {
                name: [clamped, is_pris, self.joint_effort_limits.get(name, 100.0)]
                for name, (unclamped, clamped, is_pris) in self._last_applied_forces.items()
            }
            self._check_joint_limits(forces_for_check)

        # Debug output every 2 seconds
        if int(now * 0.5) != getattr(self, '_last_debug_time', 0):
            self._last_debug_time = int(now * 0.5)
            # Show joint states for first joint
            first_joint = None
            first_cmd = 0.0
            if self.pwm_motors:
                first_port = list(self.pwm_motors.keys())[0]
                first_joint = self.pwm_motors[first_port][0]
                first_cmd = self.pwm_commands.get(first_port, 0.0)
            elif self.can_motors:
                first_id = list(self.can_motors.keys())[0]
                first_joint = self.can_motors[first_id][0]
                first_cmd = self.can_commands.get(first_id, 0.0)

            if first_joint:
                pos, vel = self.engine.get_joint_state(self.model.name, first_joint)
                # Determine unit based on joint type
                joint_config = self.model.get_joint(first_joint)
                is_pris = joint_config and joint_config.joint_type.value == "prismatic"
                pos_unit, vel_unit = ("m", "m/s") if is_pris else ("rad", "rad/s")
                force_unit = "N" if is_pris else "Nm"

                # Get applied force info
                force_info = ""
                if hasattr(self, '_last_applied_forces') and first_joint in self._last_applied_forces:
                    unclamped, clamped, _ = self._last_applied_forces[first_joint]
                    if abs(unclamped - clamped) > 0.1:
                        force_info = f", force={clamped:.1f}{force_unit} (CLAMPED from {unclamped:.1f})"
                    else:
                        force_info = f", force={clamped:.1f}{force_unit}"

                print(f"[PHYSICS] pos={pos:.3f}{pos_unit}, vel={vel:.3f}{vel_unit}, cmd={first_cmd:.3f}{force_info}", flush=True)

    async def run(self):
        """Main simulation loop."""
        # Connect to WebSocket
        if not await self.connect():
            return

        # Subscribe to devices
        await self.subscribe_to_devices()

        print("Starting simulation loop...")
        print("Robot code is now controlling the simulation!")
        print("Physics simulation is running - PyBullet window should be visible\n")

        self.running = True
        last_physics_time = time.time()
        last_gc_time = time.time()
        physics_interval = 1.0 / self.sim_rate  # 20ms at 50Hz
        gc_interval = 5.0  # Run garbage collection every 5 seconds

        # Disable automatic garbage collection for more predictable performance
        gc.disable()

        try:
            while self.running:
                current_time = time.time()
                time_until_physics = (last_physics_time + physics_interval) - current_time

                if time_until_physics <= 0:
                    # Time for physics update
                    last_physics_time = current_time
                    self.update_physics()
                    await self.publish_encoder_data()
                    time_until_physics = physics_interval

                # Periodic garbage collection to prevent memory buildup
                if current_time - last_gc_time >= gc_interval:
                    gc.collect()
                    last_gc_time = current_time

                # Process messages until next physics tick (but cap iterations)
                # This processes all pending messages efficiently
                for _ in range(50):  # Max 50 messages per batch
                    try:
                        # Short timeout to not block physics updates
                        timeout = min(0.002, time_until_physics)  # Max 2ms
                        message = await asyncio.wait_for(
                            self.websocket.recv(),
                            timeout=timeout
                        )
                        self.handle_message(message)
                        self._msg_count += 1
                    except asyncio.TimeoutError:
                        break  # No more messages, wait for physics tick

                # Minimal sleep if we processed messages quickly
                await asyncio.sleep(0.0001)

                # # Rate limit debug output
                # if self._msg_count % 1000 == 0:
                #     print(f"[DEBUG] Processed {self._msg_count} messages")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\n\nSimulation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n\nShutting down...")
            self.running = False
            gc.enable()  # Re-enable automatic garbage collection
            gc.collect()  # Final cleanup
            self.engine.disconnect()
            print("Physics engine disconnected")


async def main():
    """Entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SubsystemSim HAL WebSocket Bridge - Universal robot code simulator"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="examples/simple_arm/arm_config.json",
        help="Path to subsystem config JSON file"
    )
    parser.add_argument(
        "--ws-uri",
        type=str,
        default="ws://localhost:3300/wpilibws",
        help="WebSocket URI for HAL simulation server"
    )

    args = parser.parse_args()

    # Create and run bridge
    bridge = HALWebSocketBridge(args.config, args.ws_uri)
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
