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
from pathlib import Path
from typing import Dict, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from subsystemsim.core.config import load_config
from subsystemsim.physics.urdf_generator import generate_urdf
from subsystemsim.physics.engine import PhysicsEngine
from subsystemsim.physics.actuators import DCMotor


class HALWebSocketBridge:
    """
    WebSocket client that bridges WPILib HAL simulation to PyBullet physics.

    Connects to robot code (any language) via HAL sim WebSocket protocol.
    """

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

        # Create motor models
        print("Initializing motor models...")
        self.motors: Dict[int, tuple] = {}  # hal_port -> (joint_name, DCMotor, gear_ratio)
        for motor_config in self.model.motors:
            dc_motor = DCMotor(motor_config.motor_type.value)
            self.motors[motor_config.hal_port] = (
                motor_config.joint_name,
                dc_motor,
                motor_config.gear_ratio
            )
            print(f"  PWM[{motor_config.hal_port}] -> {motor_config.joint_name} "
                  f"({motor_config.motor_type.value}, ratio={motor_config.gear_ratio})")
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

        # Motor command storage (PWM values from robot code)
        self.motor_commands: Dict[int, float] = {port: 0.0 for port in self.motors.keys()}

        # Encoder state tracking for delta-based updates
        self.last_encoder_count: Dict[int, int] = {port: 0 for port in self.encoders.keys()}
        # Initialize all encoders as "initialized" to start sending data immediately
        self.encoder_initialized: Dict[int, bool] = {port: True for port in self.encoders.keys()}

        # Simulation timing
        self.last_update = time.time()
        self.sim_rate = 50  # Hz (20ms per update)

        print("="*70)
        print("Bridge initialized! Waiting for WebSocket connection...")
        print(f"Physics ready for model '{self.model.name}' with {len(self.motors)} motors and {len(self.encoders)} encoders")
        print("="*70 + "\n")

    async def connect(self):
        """Connect to HAL simulation WebSocket server."""
        try:
            print(f"Connecting to {self.ws_uri}...")
            self.websocket = await websockets.connect(self.ws_uri)
            print("[OK] Connected to HAL simulation WebSocket\n")
            return True
        except Exception as e:
            print(f"[FAILED] Failed to connect: {e}")
            print("\nMake sure robot code is running with HAL WebSocket extension:")
            print("  Java: gradle simulateJava -Phalsim")
            print("  C++:  gradle simulateNative -Phalsim")
            print("  Python: python robot.py sim")
            return False

    async def subscribe_to_devices(self):
        """No subscription needed - robot code sends device states automatically."""
        print("Waiting for robot code to send device states...")
        print(f"Expecting PWM device(s): {list(self.motors.keys())}")
        print(f"Will publish Encoder device(s): {list(self.encoders.keys())}")
        print()

    async def handle_message(self, message: str):
        """Handle incoming WebSocket message from robot code."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            # Handle PWM motor commands (robot output)
            if msg_type == "PWM":
                # Device is just the port number as string: "0", "1", etc.
                device_str = data.get("device", "")
                try:
                    pwm_port = int(device_str)

                    if pwm_port in self.motors:
                        msg_data = data.get("data", {})

                        # Check if device was initialized (optional)
                        if msg_data.get("<init", False):
                            print(f"[OK] PWM[{pwm_port}] initialized by robot code")

                        # Get speed value from robot (uses "<speed" = output from robot)
                        if "<speed" in msg_data:
                            speed = msg_data["<speed"]
                            self.motor_commands[pwm_port] = speed
                            # Only print motor commands occasionally to avoid spam
                            if self._msg_count % 50 == 0:
                                print(f"[MOTOR] PWM[{pwm_port}] = {speed:.3f}")

                except ValueError:
                    pass  # Not a valid port number

            # Handle Encoder initialization (robot queries)
            elif msg_type == "Encoder":
                device_str = data.get("device", "")
                try:
                    dio_port = int(device_str)

                    if dio_port in self.encoders:
                        msg_data = data.get("data", {})

                        # Check if device was initialized
                        if msg_data.get("<init", False):
                            self.encoder_initialized[dio_port] = True
                            print(f"[OK] Encoder[{dio_port}] initialized by robot code")

                except ValueError:
                    pass  # Not a valid port number

        except json.JSONDecodeError:
            pass  # Ignore malformed messages
        except Exception as e:
            print(f"Error handling message: {e}")

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

    def update_physics(self):
        """Update PyBullet physics simulation."""
        # Calculate time delta
        now = time.time()
        tm_diff = now - self.last_update
        self.last_update = now

        # Apply motor torques based on PWM commands
        for pwm_port, pwm_value in self.motor_commands.items():
            joint_name, motor, gear_ratio = self.motors[pwm_port]

            # Convert PWM to voltage
            voltage = pwm_value * 12.0  # FRC nominal voltage

            # Get current joint state
            position, velocity = self.engine.get_joint_state(self.model.name, joint_name)

            # Calculate torque using motor model
            torque = motor.calculate_torque(voltage, velocity, gear_ratio)

            # Apply to physics
            self.engine.apply_joint_torque(self.model.name, joint_name, torque)

        # Step physics simulation
        num_substeps = max(1, int(tm_diff / self.engine.TIMESTEP))
        self.engine.step(num_substeps)

        # Debug output every 2 seconds
        if int(now) % 2 == 0 and int(now) != getattr(self, '_last_debug_time', 0):
            self._last_debug_time = int(now)
            # Show joint states for first motor
            if self.motors:
                first_port = list(self.motors.keys())[0]
                joint_name = self.motors[first_port][0]
                pos, vel = self.engine.get_joint_state(self.model.name, joint_name)
                pwm_val = self.motor_commands.get(first_port, 0.0)
                print(f"[PHYSICS t={now:.1f}s] Joint '{joint_name}': pos={pos:.3f} rad, vel={vel:.3f} rad/s, PWM={pwm_val:.3f}")

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

        try:
            while self.running:
                self._msg_count += 1  # Increment message counter

                # Process incoming messages (non-blocking)
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=0.001  # 1ms timeout
                    )
                    await self.handle_message(message)
                except asyncio.TimeoutError:
                    pass  # No message, continue

                # Update physics at fixed rate (50 Hz)
                current_time = time.time()
                if current_time - self.last_update >= 1.0 / self.sim_rate:
                    self.update_physics()
                    await self.publish_encoder_data()

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
            self.engine.disconnect()
            print("Physics engine disconnected")
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
