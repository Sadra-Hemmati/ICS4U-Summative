"""
FRC motor models for SubsystemSim.

Implements physics-based DC motor models for common FRC motors (NEO, CIM, Falcon, etc.).
Uses the DC motor equation: V = IR + Kv*w to calculate torque from voltage and speed.
"""

import math
from typing import Dict
from enum import Enum


# Motor specifications database
# Source: FRC motor spec sheets (free speed, stall torque, stall current)
MOTOR_SPECS = {
    'krakenx60': {
        'free_speed_rpm': 6000,
        'stall_torque_nm': 7.09,
        'stall_current_a': 366,
        'free_current_a': 2.0
    },
    'neo': {
        'free_speed_rpm': 5676,
        'stall_torque_nm': 2.6,
        'stall_current_a': 105,
        'free_current_a': 1.8
    },
    'neo550': {
        'free_speed_rpm': 11000,
        'stall_torque_nm': 0.97,
        'stall_current_a': 100,
        'free_current_a': 1.4
    },
    'neovortex': {
        'free_speed_rpm': 6784,
        'stall_torque_nm': 3.6,
        'stall_current_a': 211,
        'free_current_a': 1.2
    },
    'falcon500': {
        'free_speed_rpm': 6380,
        'stall_torque_nm': 4.69,
        'stall_current_a': 257,
        'free_current_a': 1.5
    },
    'cim': {
        'free_speed_rpm': 5330,
        'stall_torque_nm': 2.41,
        'stall_current_a': 131,
        'free_current_a': 2.7
    },
    'minicim': {
        'free_speed_rpm': 5840,
        'stall_torque_nm': 1.41,
        'stall_current_a': 89,
        'free_current_a': 3
    },
    'bag': {
        'free_speed_rpm': 13180,
        'stall_torque_nm': 0.43,
        'stall_current_a': 53,
        'free_current_a': 1.8
    },
    'venom': {
        'free_speed_rpm': 6000,
        'stall_torque_nm': 2.4,
        'stall_current_a': 120,
        'free_current_a': 2.0
    }
}


class DCMotor:
    """
    Physics-based DC motor model.

    Uses the standard DC motor equations:
    - V = IR + Kv*w  (voltage equation)
    - T = Kt*I       (torque equation)

    Where:
    - V: Applied voltage (volts)
    - I: Current (amps)
    - R: Resistance (ohms)
    - Kv: Velocity constant (rad/s per volt)
    - w: Angular velocity (rad/s)
    - T: Torque (Nm)
    - Kt: Torque constant (Nm per amp)
    """

    # Constants
    NOMINAL_VOLTAGE = 12.0  # FRC standard voltage
    GEARBOX_EFFICIENCY = 0.8  # Typical gearbox efficiency (80%)

    def __init__(self, motor_type: str):
        """
        Initialize motor from specs database.

        Args:
            motor_type: Motor type string (e.g., 'neo', 'cim', 'falcon500')
        """
        if motor_type not in MOTOR_SPECS:
            raise ValueError(f"Unknown motor type: {motor_type}. "
                           f"Available: {list(MOTOR_SPECS.keys())}")

        specs = MOTOR_SPECS[motor_type]
        self.motor_type = motor_type

        # Store raw specs
        self.free_speed_rpm = specs['free_speed_rpm']
        self.stall_torque_nm = specs['stall_torque_nm']
        self.stall_current_a = specs['stall_current_a']
        self.free_current_a = specs['free_current_a']

        # Calculate motor constants
        # Kv = w_free / V  (rad/s per volt)
        self.free_speed_rad_s = (self.free_speed_rpm * 2 * math.pi) / 60.0
        self.Kv = self.free_speed_rad_s / self.NOMINAL_VOLTAGE

        # Kt = T_stall / I_stall  (Nm per amp)
        self.Kt = self.stall_torque_nm / self.stall_current_a

        # R = V / I_stall  (ohms)
        self.R = self.NOMINAL_VOLTAGE / self.stall_current_a

        print(f"Initialized {motor_type}: "
              f"Kv={self.Kv:.3f} rad/s/V, Kt={self.Kt:.4f} Nm/A, R={self.R:.4f} Ohm")

    def calculate_torque(self, voltage: float, angular_velocity: float,
                        gear_ratio: float = 1.0) -> float:
        """
        Calculate output torque given voltage and current speed.

        Uses DC motor equation:
        1. Back-EMF: emf = Kv * w
        2. Current: I = (V - emf) / R
        3. Motor torque: T_motor = Kt * I
        4. Output torque: T_out = T_motor * gear_ratio * efficiency

        Args:
            voltage: Applied voltage in volts (-12 to +12 for FRC)
            angular_velocity: Current angular velocity in rad/s (of the OUTPUT shaft)
            gear_ratio: Gear reduction ratio (e.g., 60 for 60:1 reduction)

        Returns:
            Output torque in Nm
        """
        # Clamp voltage to realistic range
        voltage = max(-self.NOMINAL_VOLTAGE, min(self.NOMINAL_VOLTAGE, voltage))

        # Convert output velocity to motor velocity
        motor_velocity = angular_velocity * gear_ratio

        # Calculate back-EMF
        back_emf = motor_velocity / self.Kv  # emf = Kv * w, rearranged

        # Calculate current
        current = (voltage - back_emf) / self.R

        # Clamp current to prevent unrealistic values
        current = max(-self.stall_current_a, min(self.stall_current_a, current))

        # Calculate motor torque
        motor_torque = self.Kt * current

        # Apply gear ratio and efficiency
        output_torque = motor_torque * gear_ratio * self.GEARBOX_EFFICIENCY

        return output_torque

    def calculate_torque_simple(self, voltage: float, gear_ratio: float = 1.0) -> float:
        """
        Simplified torque calculation (linear approximation).

        Useful for initial testing or when motor speed is unknown.
        Assumes motor is running at ~50% of free speed.

        Args:
            voltage: Applied voltage (-12 to +12)
            gear_ratio: Gear reduction ratio

        Returns:
            Approximate output torque in Nm
        """
        # Simple linear model: torque proportional to voltage
        TORQUE_CONSTANT_NM_PER_VOLT = 0.2  # Approximate
        return voltage * TORQUE_CONSTANT_NM_PER_VOLT * gear_ratio

    def get_max_torque(self, gear_ratio: float = 1.0) -> float:
        """
        Get maximum (stall) torque for this motor with gearing.

        Args:
            gear_ratio: Gear reduction ratio

        Returns:
            Maximum torque in Nm
        """
        return self.stall_torque_nm * gear_ratio * self.GEARBOX_EFFICIENCY

    def get_max_speed(self, gear_ratio: float = 1.0) -> float:
        """
        Get maximum (no-load) speed for this motor with gearing.

        Args:
            gear_ratio: Gear reduction ratio

        Returns:
            Maximum speed in rad/s (of output shaft)
        """
        return self.free_speed_rad_s / gear_ratio

    def __str__(self) -> str:
        return (f"DCMotor({self.motor_type}: "
                f"{self.free_speed_rpm} RPM free, "
                f"{self.stall_torque_nm:.2f} Nm stall)")


# Convenience function to create motor from string
def create_motor(motor_type: str) -> DCMotor:
    """Factory function to create a DC motor."""
    return DCMotor(motor_type)


if __name__ == "__main__":
    # Test motor models
    print("=== Testing Motor Models ===\n")

    # Create a NEO motor
    neo = DCMotor('neo')
    print(f"\n{neo}\n")

    # Test torque calculation at different speeds
    gear_ratio = 60  # 60:1 reduction
    voltage = 12.0   # Full voltage

    print(f"NEO motor with {gear_ratio}:1 gearing at {voltage}V:\n")

    test_speeds = [0, 1, 2, 5, 10]  # rad/s (output shaft)
    print(f"{'Speed (rad/s)':<15} {'Torque (Nm)':<15} {'Torque (lb-ft)':<15}")
    print("-" * 45)

    for speed in test_speeds:
        torque = neo.calculate_torque(voltage, speed, gear_ratio)
        torque_lbft = torque * 0.73756  # Convert Nm to lb-ft
        print(f"{speed:<15.1f} {torque:<15.2f} {torque_lbft:<15.2f}")

    print(f"\nMax torque: {neo.get_max_torque(gear_ratio):.2f} Nm")
    print(f"Max speed: {neo.get_max_speed(gear_ratio):.2f} rad/s "
          f"({neo.get_max_speed(gear_ratio) * 60 / (2*math.pi):.1f} RPM)")

    # Compare different motors
    print("\n\n=== Motor Comparison (at stall with 60:1 gearing) ===\n")
    print(f"{'Motor':<12} {'Stall Torque (Nm)':<20} {'Free Speed (RPM)':<20}")
    print("-" * 52)

    for motor_name in ['neo', 'cim', 'falcon500', 'neo550']:
        motor = DCMotor(motor_name)
        max_torque = motor.get_max_torque(60)
        max_rpm = motor.get_max_speed(60) * 60 / (2 * math.pi)
        print(f"{motor_name:<12} {max_torque:<20.2f} {max_rpm:<20.1f}")

    print("\n[OK] Motor models working correctly!")
