"""
URDF generator for SubsystemSim.

Converts SubsystemModel to URDF XML format that PyBullet can load.
URDF (Unified Robot Description Format) is the standard format for robot kinematics.
"""

import os
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from ..core.model import SubsystemModel, Link, Joint, JointType


def generate_urdf(model: SubsystemModel, output_dir: str = None,
                  joint_damping: float = 0.5, joint_friction: float = 0.0) -> str:
    """
    Generate URDF file from SubsystemModel.

    Args:
        model: The subsystem model to convert
        output_dir: Directory to save URDF (default: temp directory)
        joint_damping: Damping coefficient for all joints (Nm/(rad/s))
                       Higher values = more resistance to motion = more realistic
                       Default 0.5 provides good balance for FRC mechanisms
        joint_friction: Coulomb friction coefficient for joints
                        Default 0.0 for smooth motor-driven joints

    Returns:
        Path to generated URDF file

    Raises:
        ValueError: If model is invalid
    """
    # Validate model first
    errors = model.validate()
    if errors:
        raise ValueError(f"Invalid model:\n  " + "\n  ".join(errors))

    # Create output directory
    if output_dir is None:
        output_dir = Path(".") / "generated_urdfs"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create URDF XML tree
    robot = ET.Element("robot", name=model.name)

    # Calculate URDF path first (needed for relative paths)
    urdf_path = output_dir / f"{model.name}.urdf"

    # Add all links (pass urdf_path for relative path calculation)
    for link in model.links:
        robot.append(_create_link_element(link, urdf_path))

    # Add all joints with damping for realistic motor behavior
    for joint in model.joints:
        robot.append(_create_joint_element(joint, damping=joint_damping, friction=joint_friction))

    # Convert to pretty XML string
    xml_string = _prettify_xml(robot)
    with open(urdf_path, 'w') as f:
        f.write(xml_string)

    print(f"Generated URDF: {urdf_path}")
    print(f"  Joint damping: {joint_damping} Nm/(rad/s)")
    return str(urdf_path.absolute())


def _create_link_element(link: Link, urdf_path: Path) -> ET.Element:
    """
    Create a URDF <link> element from Link object.

    URDF link structure:
    <link name="...">
      <visual><geometry><mesh filename="..."/></geometry></visual>
      <collision><geometry><mesh filename="..."/></geometry></collision>
      <inertial><mass value="..."/><inertia .../></inertial>
    </link>
    """
    link_elem = ET.Element("link", name=link.name)

    # Calculate relative path from URDF directory to mesh file
    # This avoids issues with PyBullet prepending working directory on Windows
    import os
    mesh_abs_path = Path(link.mesh_path).absolute()
    urdf_dir = urdf_path.parent.absolute()

    try:
        # Use os.path.relpath for proper relative path calculation
        mesh_rel_path = os.path.relpath(mesh_abs_path, urdf_dir)
        mesh_path_str = mesh_rel_path.replace('\\', '/')
    except ValueError:
        # If relative path fails (different drives on Windows), use absolute with forward slashes
        mesh_path_str = str(mesh_abs_path).replace('\\', '/')

    # Visual geometry
    visual = ET.SubElement(link_elem, "visual")
    visual_geom = ET.SubElement(visual, "geometry")
    ET.SubElement(visual_geom, "mesh", filename=mesh_path_str)

    # Collision geometry (same as visual for simplicity)
    collision = ET.SubElement(link_elem, "collision")
    collision_geom = ET.SubElement(collision, "geometry")
    ET.SubElement(collision_geom, "mesh", filename=mesh_path_str)

    # Inertial properties
    inertial = ET.SubElement(link_elem, "inertial")

    # Origin (center of mass offset)
    com_xyz = " ".join(map(str, link.center_of_mass))
    ET.SubElement(inertial, "origin", xyz=com_xyz, rpy="0 0 0")

    # Mass
    ET.SubElement(inertial, "mass", value=str(link.mass))

    # Inertia tensor (3x3 matrix)
    # URDF format: ixx, ixy, ixz, iyy, iyz, izz
    inertia_matrix = link.inertia
    ET.SubElement(
        inertial, "inertia",
        ixx=str(inertia_matrix[0][0]),
        ixy=str(inertia_matrix[0][1]),
        ixz=str(inertia_matrix[0][2]),
        iyy=str(inertia_matrix[1][1]),
        iyz=str(inertia_matrix[1][2]),
        izz=str(inertia_matrix[2][2])
    )

    return link_elem


def _create_joint_element(joint: Joint, damping: float = 0.5, friction: float = 0.0) -> ET.Element:
    """
    Create a URDF <joint> element from Joint object.

    URDF joint structure:
    <joint name="..." type="...">
      <parent link="..."/>
      <child link="..."/>
      <origin xyz="..." rpy="..."/>
      <axis xyz="..."/>
      <limit lower="..." upper="..." velocity="..." effort="..."/>
      <dynamics damping="..." friction="..."/>
    </joint>

    Args:
        joint: Joint object from model
        damping: Damping coefficient for joint (Nm/(rad/s) for revolute, N/(m/s) for prismatic)
                 This creates velocity-proportional resistance, similar to motor back-EMF.
                 Higher values = more resistance to motion = stops faster when force removed.
                 Typical values: 0.1-1.0 for small joints, 1.0-5.0 for large joints.
        friction: Coulomb friction coefficient (constant resistance to motion)
                  Set to 0 for smooth motor-driven joints.
    """
    # Map our JointType enum to URDF type strings
    joint_type_map = {
        JointType.REVOLUTE: "revolute",
        JointType.PRISMATIC: "prismatic",
        JointType.FIXED: "fixed"
    }
    urdf_type = joint_type_map[joint.joint_type]

    joint_elem = ET.Element("joint", name=joint.name, type=urdf_type)

    # Parent and child links
    ET.SubElement(joint_elem, "parent", link=joint.parent_link)
    ET.SubElement(joint_elem, "child", link=joint.child_link)

    # Joint origin (position in parent frame)
    origin_xyz = " ".join(map(str, joint.origin))
    ET.SubElement(joint_elem, "origin", xyz=origin_xyz, rpy="0 0 0")

    # Joint axis (for revolute/prismatic joints)
    if joint.joint_type != JointType.FIXED:
        axis_xyz = " ".join(map(str, joint.axis))
        ET.SubElement(joint_elem, "axis", xyz=axis_xyz)

        # Joint limits (only if joint is limited)
        # Unlimited joints (limits=None) allow continuous rotation
        if joint.limits is not None:
            ET.SubElement(
                joint_elem, "limit",
                lower=str(joint.limits[0]),
                upper=str(joint.limits[1]),
                velocity=str(joint.velocity_limit),
                effort=str(joint.effort_limit)
            )
        else:
            # For unlimited joints, still need a limit element in URDF
            # but we use very large values that won't be reached in practice
            ET.SubElement(
                joint_elem, "limit",
                lower=str(-1e6),
                upper=str(1e6),
                velocity=str(joint.velocity_limit),
                effort=str(joint.effort_limit)
            )

        # Add dynamics element for realistic motor behavior
        # damping: creates velocity-proportional resistance (like motor back-EMF)
        # friction: constant resistance to motion (like static friction)
        ET.SubElement(
            joint_elem, "dynamics",
            damping=str(damping),
            friction=str(friction)
        )

    return joint_elem


def _prettify_xml(elem: ET.Element) -> str:
    """
    Convert XML element to pretty-printed string.

    Args:
        elem: Root XML element

    Returns:
        Pretty-printed XML string
    """
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


if __name__ == "__main__":
    # Test: Generate URDF from the example arm config
    print("=== Testing URDF Generator ===\n")

    from ..core.config import load_config

    # Load arm configuration
    config_path = Path("examples/simple_arm/arm_config.json")
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        print("Run this test from the project root directory.")
        exit(1)

    model = load_config(config_path)
    print(f"Loaded model: {model}\n")

    # Generate URDF
    urdf_path = generate_urdf(model, output_dir="generated_urdfs")
    print(f"\nGenerated URDF at: {urdf_path}")

    # Display the generated URDF
    print("\n--- Generated URDF Content ---")
    with open(urdf_path, 'r') as f:
        print(f.read())

    print("\n[OK] URDF generation successful!")
