"""
Simple Arm Robot - Example WPILib robot code.

This is REAL robot code that runs unchanged in both:
- Real hardware (FRC robot)
- Simulation (SubsystemSim)

No simulation-specific code needed!
"""

import wpilib


class ArmRobot(wpilib.TimedRobot):
    """
    Simple robot with a single-joint arm.

    Controls:
    - Motor on PWM port 0
    - Encoder on DIO ports 0, 1
    """

    def robotInit(self):
        """Initialize robot hardware."""
        print("\n=== Arm Robot Initializing ===")

        # Create motor controller (PWM port 0)
        # Using PWMSparkMax as a generic PWM motor controller
        self.motor = wpilib.PWMSparkMax(0)
        print("[OK] Motor controller initialized (PWM port 0)")

        # Create encoder (DIO ports 0, 1)
        self.encoder = wpilib.Encoder(0, 1)
        # Set distance per pulse (radians per tick)
        # For 2048 ticks/rev: 2*pi / 2048
        self.encoder.setDistancePerPulse((2.0 * 3.14159) / 2048.0)
        print("[OK] Encoder initialized (DIO ports 0, 1)")

        # Control parameters
        self.target_position = 0.0  # Target angle in radians
        self.kP = 0.5  # Proportional gain for simple P control

        print("[OK] Robot initialized!\n")

    def autonomousInit(self):
        """Called when autonomous mode starts."""
        print("\n--- Autonomous Mode ---")
        self.target_position = 1.0  # Move to ~60 degrees
        self.encoder.reset()

    def autonomousPeriodic(self):
        """Called periodically during autonomous mode."""
        self._runControl()

    def teleopInit(self):
        """Called when teleop mode starts."""
        print("\n--- Teleop Mode ---")
        self.target_position = 0.0  # Return to zero
        self.encoder.reset()

    def teleopPeriodic(self):
        """Called periodically during teleop mode."""
        # Simple sinusoidal motion for demo
        import math
        time = wpilib.Timer.getFPGATimestamp()
        self.target_position = math.sin(time * 0.5) * 1.0  # Oscillate +/-1 radian

        self._runControl()

    def _runControl(self):
        """
        Simple proportional controller.

        This is the core control logic that would work identically on real hardware.
        """
        # Get current position from encoder
        current_position = self.encoder.getDistance()  # Radians

        # Calculate error
        error = self.target_position - current_position

        # Simple P control: motor voltage = kP * error
        motor_command = self.kP * error

        # Clamp to [-1, 1]
        motor_command = max(-1.0, min(1.0, motor_command))

        # Send command to motor
        self.motor.set(motor_command)

        # Print status occasionally (every 50 cycles = 1 second)
        if hasattr(self, '_print_counter'):
            self._print_counter += 1
        else:
            self._print_counter = 0

        if self._print_counter % 50 == 0:
            print(f"[t={wpilib.Timer.getFPGATimestamp():.1f}s] "
                  f"target={self.target_position:.3f} rad, "
                  f"current={current_position:.3f} rad, "
                  f"error={error:.3f}, "
                  f"motor={motor_command:.3f}")

    def disabledInit(self):
        """Called when robot is disabled."""
        print("\n--- Disabled ---")
        self.motor.set(0.0)  # Stop motor
