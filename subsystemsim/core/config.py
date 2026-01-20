"""
Configuration file loading and saving for SubsystemSim.

Handles JSON serialization/deserialization of SubsystemModel.
"""

import json
import yaml
from pathlib import Path
from typing import Union
from .model import SubsystemModel, Link, Joint, Motor, Sensor, JointType, MotorType


def load_config(config_path: Union[str, Path]) -> SubsystemModel:
    """
    Load subsystem configuration from JSON or YAML file.

    Args:
        config_path: Path to configuration file (.json or .yaml)

    Returns:
        SubsystemModel instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config format is invalid
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load file
    with open(config_path, 'r') as f:
        if config_path.suffix == '.json':
            data = json.load(f)
        elif config_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}. Use .json or .yaml")

    # Parse model name
    name = data.get('name', config_path.stem)

    # Get config file directory for resolving relative paths
    config_dir = config_path.parent.absolute()

    # Parse links
    links = []
    for link_data in data.get('links', []):
        # Resolve mesh path relative to config file location
        mesh_path_raw = link_data['mesh']
        mesh_path_obj = Path(mesh_path_raw)

        # If path is relative, resolve it relative to config file directory
        if not mesh_path_obj.is_absolute():
            mesh_path_resolved = (config_dir / mesh_path_raw).absolute()
        else:
            mesh_path_resolved = mesh_path_obj.absolute()

        link = Link(
            name=link_data['name'],
            mesh_path=str(mesh_path_resolved),
            mass=link_data.get('mass', 1.0),
            center_of_mass=tuple(link_data.get('center_of_mass', [0, 0, 0])),
            inertia=link_data.get('inertia', None)
        )
        links.append(link)

    # Parse joints
    joints = []
    for joint_data in data.get('joints', []):
        # Handle limits: can be null (None for unlimited) or [lower, upper]
        limits_data = joint_data.get('limits', [-3.14, 3.14])
        limits = tuple(limits_data) if limits_data is not None else None
        
        joint = Joint(
            name=joint_data['name'],
            joint_type=JointType(joint_data['type']),
            parent_link=joint_data['parent'],
            child_link=joint_data['child'],
            axis=tuple(joint_data.get('axis', [0, 0, 1])),
            origin=tuple(joint_data.get('origin', [0, 0, 0])),
            limits=limits,
            velocity_limit=joint_data.get('velocity_limit', 10.0),
            effort_limit=joint_data.get('effort_limit', 100.0)
        )
        joints.append(joint)

    # Parse motors
    motors = []
    for motor_data in data.get('motors', []):
        motor = Motor(
            name=motor_data['name'],
            motor_type=MotorType(motor_data['type']),
            joint_name=motor_data['joint'],
            gear_ratio=motor_data.get('gear_ratio', 1.0),
            controller_type=motor_data.get('controller_type', 'pwm'),
            hal_port=motor_data.get('hal_port', 0),
            inverted=motor_data.get('inverted', False),
            drum_radius=motor_data.get('drum_radius', 0.019)  # Default ~1.5" diameter
        )
        motors.append(motor)

    # Parse sensors
    sensors = []
    for sensor_data in data.get('sensors', []):
        sensor = Sensor(
            name=sensor_data['name'],
            sensor_type=sensor_data.get('type', 'encoder'),
            joint_name=sensor_data['joint'],
            controller_type=sensor_data.get('controller_type', 'dio'),
            hal_ports=sensor_data.get('hal_ports', []),
            can_id=sensor_data.get('can_id'),
            ticks_per_revolution=sensor_data.get('ticks_per_rev', 2048),
            offset=sensor_data.get('offset', 0.0)
        )
        sensors.append(sensor)

    # Create model
    model = SubsystemModel(
        name=name,
        links=links,
        joints=joints,
        motors=motors,
        sensors=sensors
    )

    # Validate
    errors = model.validate()
    if errors:
        error_msg = "Invalid configuration:\n  " + "\n  ".join(errors)
        raise ValueError(error_msg)

    return model


def save_config(model: SubsystemModel, config_path: Union[str, Path]):
    """
    Save subsystem configuration to JSON file.

    Args:
        model: SubsystemModel to save
        config_path: Output path (.json recommended)
    """
    config_path = Path(config_path)

    # Convert model to dictionary
    data = {
        'name': model.name,
        'links': [
            {
                'name': link.name,
                'mesh': link.mesh_path,
                'mass': link.mass,
                'center_of_mass': list(link.center_of_mass),
                'inertia': link.inertia
            }
            for link in model.links
        ],
        'joints': [
            {
                'name': joint.name,
                'type': joint.joint_type.value,
                'parent': joint.parent_link,
                'child': joint.child_link,
                'axis': list(joint.axis),
                'origin': list(joint.origin),
                'limits': list(joint.limits),
                'velocity_limit': joint.velocity_limit,
                'effort_limit': joint.effort_limit
            }
            for joint in model.joints
        ],
        'motors': [
            {
                'name': motor.name,
                'type': motor.motor_type.value,
                'joint': motor.joint_name,
                'gear_ratio': motor.gear_ratio,
                'controller_type': motor.controller_type,
                'hal_port': motor.hal_port,
                'inverted': motor.inverted
            }
            for motor in model.motors
        ],
        'sensors': [
            {
                'name': sensor.name,
                'type': sensor.sensor_type,
                'joint': sensor.joint_name,
                'controller_type': sensor.controller_type,
                'hal_ports': sensor.hal_ports,
                'can_id': sensor.can_id,
                'ticks_per_rev': sensor.ticks_per_revolution,
                'offset': sensor.offset
            }
            for sensor in model.sensors
        ]
    }

    # Write file
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved config to: {config_path}")


if __name__ == "__main__":
    # Test: Create a model, save it, then load it back
    print("=== Testing Config Loader ===\n")

    from .model import Link, Joint, Motor, Sensor, JointType, MotorType, SubsystemModel

    # Create test model
    model = SubsystemModel(
        name="test_arm",
        links=[
            Link(name="base", mesh_path="meshes/base.obj", mass=2.0),
            Link(name="arm", mesh_path="meshes/arm.obj", mass=1.5)
        ],
        joints=[
            Joint(
                name="shoulder",
                joint_type=JointType.REVOLUTE,
                parent_link="base",
                child_link="arm",
                axis=(0, 0, 1),
                limits=(-1.57, 1.57)
            )
        ],
        motors=[
            Motor(
                name="shoulder_motor",
                motor_type=MotorType.NEO,
                joint_name="shoulder",
                gear_ratio=60,
                hal_port=0
            )
        ],
        sensors=[
            Sensor(
                name="arm_encoder",
                sensor_type="encoder",
                joint_name="shoulder",
                hal_ports=[0, 1],
                ticks_per_revolution=2048
            )
        ]
    )

    print(f"Original model: {model}\n")

    # Save to JSON
    test_path = Path("test_config.json")
    save_config(model, test_path)

    # Load back
    loaded_model = load_config(test_path)
    print(f"\nLoaded model: {loaded_model}")

    # Verify
    assert loaded_model.name == model.name
    assert len(loaded_model.links) == len(model.links)
    assert len(loaded_model.joints) == len(model.joints)
    assert len(loaded_model.motors) == len(model.motors)
    assert len(loaded_model.sensors) == len(model.sensors)

    print("\n[OK] Config save/load successful!")

    # Clean up
    test_path.unlink()
    print(f"Cleaned up test file: {test_path}")
