"""
Core data model for SubsystemSim.

Defines the internal representation of a subsystem:
- Links: Rigid bodies with geometry and mass properties
- Joints: Kinematic connections between links
- Motors: Actuators that drive joints
- Sensors: Feedback devices (encoders, limit switches, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class JointType(Enum):
    """Types of joints supported."""
    REVOLUTE = "revolute"  # Rotational joint (hinge)
    PRISMATIC = "prismatic"  # Linear joint (slider)
    FIXED = "fixed"  # Rigid connection (no movement)


class MotorType(Enum):
    """FRC motor types."""
    KRAKEN_X60 = "krakenx60"
    NEO = "neo"
    NEO_550 = "neo550"
    NEO_VORTEX = "neovortex"
    FALCON_500 = "falcon500"
    CIM = "cim"
    MINI_CIM = "minicim"
    BAG = "bag"
    VENOM = "venom"


@dataclass
class Link:
    """
    A rigid body in the mechanism.

    Attributes:
        name: Unique identifier for this link
        mesh_path: Path to OBJ file for visual/collision geometry
        mass: Mass in kilograms
        center_of_mass: (x, y, z) offset of COM from link origin
        inertia: 3x3 inertia tensor (or None to use default)
    """
    name: str
    mesh_path: str
    mass: float = 1.0
    center_of_mass: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    inertia: Optional[List[List[float]]] = None  # 3x3 matrix

    def __post_init__(self):
        """Generate default inertia if not provided."""
        if self.inertia is None:
            # Simple default: diagonal matrix scaled by mass
            # inertia = mass * 0.01 * I (good enough for MVP)
            self.inertia = [
                [self.mass * 0.01, 0.0, 0.0],
                [0.0, self.mass * 0.01, 0.0],
                [0.0, 0.0, self.mass * 0.01]
            ]


@dataclass
class Joint:
    """
    Kinematic connection between two links.

    Attributes:
        name: Unique identifier for this joint
        joint_type: Type of joint (revolute, prismatic, fixed)
        parent_link: Name of parent link
        child_link: Name of child link
        axis: (x, y, z) axis of rotation/translation in parent frame
        origin: (x, y, z) position of joint in parent frame
        limits: (lower, upper) position limits in radians or meters
                Use None for unlimited joints (continuous rotation)
        velocity_limit: Maximum velocity (rad/s or m/s)
        effort_limit: Maximum force/torque (N or Nm)
    """
    name: str
    joint_type: JointType
    parent_link: str
    child_link: str
    axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)  # Z-axis by default
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    limits: Optional[Tuple[float, float]] = (-3.14, 3.14)  # +/-180deg default, or None for unlimited
    velocity_limit: float = 10.0  # rad/s or m/s
    effort_limit: float = 100.0  # Nm or N

    def __post_init__(self):
        """Convert string joint_type to enum if needed."""
        if isinstance(self.joint_type, str):
            self.joint_type = JointType(self.joint_type)
    
    def is_limited(self) -> bool:
        """Check if this joint has limits."""
        return self.limits is not None


@dataclass
class Motor:
    """
    Actuator that drives a joint.

    Attributes:
        name: Unique identifier for this motor
        motor_type: Type of FRC motor (NEO, CIM, etc.)
        joint_name: Name of joint this motor drives
        gear_ratio: Gear reduction ratio (output:input, e.g., 60 for 60:1)
        controller_type: "pwm" or "can" - type of motor controller
        hal_port: PWM port or CAN ID used in robot code
        inverted: Whether motor direction is inverted
        drum_radius: For prismatic joints, radius of the drum/pulley/sprocket (meters)
                     Used to convert motor torque to linear force. Default 0.019m (~1.5" dia)
    """
    name: str
    motor_type: MotorType
    joint_name: str
    gear_ratio: float = 1.0
    controller_type: str = "pwm"  # "pwm" or "can"
    hal_port: int = 0
    inverted: bool = False
    drum_radius: float = 0.019  # ~1.5" diameter, typical for FRC mechanisms

    def __post_init__(self):
        """Convert string motor_type to enum if needed."""
        if isinstance(self.motor_type, str):
            self.motor_type = MotorType(self.motor_type)


@dataclass
class Sensor:
    """
    Feedback device attached to a joint or link.

    Attributes:
        name: Unique identifier for this sensor
        sensor_type: Type of sensor ("encoder", "cancoder", "duty_cycle", "limit_switch")
        joint_name: Name of joint this sensor measures
        controller_type: "dio" or "can" - type of sensor connection
        hal_ports: DIO ports used in robot code (e.g., [0, 1] for quadrature encoder)
        can_id: CAN ID for CAN-based sensors (CANcoder, etc.)
        ticks_per_revolution: Encoder resolution (for encoders)
        offset: Zero position offset in radians/meters
    """
    name: str
    sensor_type: str  # "encoder", "cancoder", "duty_cycle", "limit_switch"
    joint_name: str
    controller_type: str = "dio"  # "dio" or "can"
    hal_ports: List[int] = field(default_factory=list)
    can_id: Optional[int] = None  # CAN ID for CAN-based sensors
    ticks_per_revolution: int = 2048  # Common value for many FRC encoders
    offset: float = 0.0


@dataclass
class SubsystemModel:
    """
    Complete model of a subsystem.

    Attributes:
        name: Name of the subsystem (e.g., "simple_arm")
        links: List of rigid bodies
        joints: List of kinematic connections
        motors: List of actuators
        sensors: List of feedback devices
    """
    name: str
    links: List[Link] = field(default_factory=list)
    joints: List[Joint] = field(default_factory=list)
    motors: List[Motor] = field(default_factory=list)
    sensors: List[Sensor] = field(default_factory=list)

    def get_link(self, name: str) -> Optional[Link]:
        """Find link by name."""
        for link in self.links:
            if link.name == name:
                return link
        return None

    def get_joint(self, name: str) -> Optional[Joint]:
        """Find joint by name."""
        for joint in self.joints:
            if joint.name == name:
                return joint
        return None

    def get_motor(self, name: str) -> Optional[Motor]:
        """Find motor by name."""
        for motor in self.motors:
            if motor.name == name:
                return motor
        return None

    def get_sensor(self, name: str) -> Optional[Sensor]:
        """Find sensor by name."""
        for sensor in self.sensors:
            if sensor.name == name:
                return sensor
        return None

    def validate(self) -> List[str]:
        """
        Validate the model for consistency.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check that all link names are unique
        link_names = [link.name for link in self.links]
        if len(link_names) != len(set(link_names)):
            errors.append("Duplicate link names found")

        # Check that all joints reference valid links
        for joint in self.joints:
            if joint.parent_link not in link_names:
                errors.append(f"Joint '{joint.name}' references unknown parent link '{joint.parent_link}'")
            if joint.child_link not in link_names:
                errors.append(f"Joint '{joint.name}' references unknown child link '{joint.child_link}'")

        # Check that all motors reference valid joints
        joint_names = [joint.name for joint in self.joints]
        for motor in self.motors:
            if motor.joint_name not in joint_names:
                errors.append(f"Motor '{motor.name}' references unknown joint '{motor.joint_name}'")

        # Check that all sensors reference valid joints
        for sensor in self.sensors:
            if sensor.joint_name not in joint_names:
                errors.append(f"Sensor '{sensor.name}' references unknown joint '{sensor.joint_name}'")

        return errors

    def __str__(self) -> str:
        """Human-readable representation."""
        return (f"SubsystemModel(name='{self.name}', "
                f"{len(self.links)} links, {len(self.joints)} joints, "
                f"{len(self.motors)} motors, {len(self.sensors)} sensors)")


if __name__ == "__main__":
    # Example: Create a simple 2-link arm model
    print("=== Testing Data Model ===\n")

    # Create links
    base = Link(name="base", mesh_path="meshes/base.obj", mass=2.0)
    arm = Link(name="arm", mesh_path="meshes/arm.obj", mass=1.5)

    # Create joint
    shoulder = Joint(
        name="shoulder",
        joint_type=JointType.REVOLUTE,
        parent_link="base",
        child_link="arm",
        axis=(0, 0, 1),  # Rotate around Z-axis
        limits=(-1.57, 1.57)  # +/-90 degrees
    )

    # Create motor
    motor = Motor(
        name="shoulder_motor",
        motor_type=MotorType.NEO,
        joint_name="shoulder",
        gear_ratio=60,
        hal_port=0
    )

    # Create sensor
    encoder = Sensor(
        name="arm_encoder",
        sensor_type="encoder",
        joint_name="shoulder",
        hal_ports=[0, 1],
        ticks_per_revolution=2048
    )

    # Create model
    model = SubsystemModel(
        name="simple_arm",
        links=[base, arm],
        joints=[shoulder],
        motors=[motor],
        sensors=[encoder]
    )

    print(model)
    print()

    # Validate
    errors = model.validate()
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("[OK] Model is valid")

    print("\nModel details:")
    print(f"  Links: {[link.name for link in model.links]}")
    print(f"  Joints: {[joint.name for joint in model.joints]}")
    print(f"  Motors: {[motor.name for motor in model.motors]}")
    print(f"  Sensors: {[sensor.name for sensor in model.sensors]}")
