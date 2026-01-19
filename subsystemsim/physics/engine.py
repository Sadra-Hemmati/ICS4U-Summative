"""
PyBullet physics engine wrapper for SubsystemSim.
Handles initialization, URDF loading, and simulation stepping.
"""

import pybullet as p
import pybullet_data
import numpy as np
from typing import Tuple, Optional


class PhysicsEngine:
    """Wrapper for PyBullet physics simulation."""

    # Simulation constants
    GRAVITY = -9.81  # m/s^2 (Z-up convention)
    TIMESTEP = 1.0 / 240.0  # 240 Hz simulation (PyBullet default)

    def __init__(self, gui: bool = True):
        """
        Initialize PyBullet physics engine.

        Args:
            gui: If True, use GUI mode. If False, use DIRECT mode (headless).
        """
        # Connect to PyBullet
        if gui:
            self.physics_client = p.connect(p.GUI)
            # Configure camera for better viewing
            p.resetDebugVisualizerCamera(
                cameraDistance=1.5,
                cameraYaw=50,
                cameraPitch=-35,
                cameraTargetPosition=[0, 0, 0.5]
            )
        else:
            self.physics_client = p.connect(p.DIRECT)

        # Set gravity (Z-up convention)
        p.setGravity(0, 0, self.GRAVITY)

        # Add search path for default URDFs
        p.setAdditionalSearchPath(pybullet_data.getDataPath())

        # Load ground plane
        self.plane_id = p.loadURDF("plane.urdf")

        # Store loaded bodies
        self.bodies = {}  # name -> body_id mapping
        self.joint_indices = {}  # name -> joint_index mapping

        print(f"PhysicsEngine initialized (GUI={gui})")

    def load_urdf(self, urdf_path: str, name: str = "robot",
                   base_position: Tuple[float, float, float] = (0, 0, 0),
                   base_orientation: Optional[Tuple[float, float, float, float]] = None) -> int:
        """
        Load a URDF file into the simulation.

        Args:
            urdf_path: Path to URDF file
            name: Name to identify this body
            base_position: (x, y, z) position of the robot base
            base_orientation: Quaternion (x, y, z, w) or None for default (0, 0, 0, 1)

        Returns:
            PyBullet body ID
        """
        if base_orientation is None:
            base_orientation = [0, 0, 0, 1]  # No rotation

        body_id = p.loadURDF(
            urdf_path,
            basePosition=base_position,
            baseOrientation=base_orientation,
            useFixedBase=True  # Fix base to ground (for now)
        )

        self.bodies[name] = body_id

        # Get joint information and enable dynamics
        num_joints = p.getNumJoints(body_id)
        
        # Also disable damping on the base link
        p.changeDynamics(body_id, -1, linearDamping=0.0, angularDamping=0.0, jointDamping=0.0)
        
        for i in range(num_joints):
            joint_info = p.getJointInfo(body_id, i)
            joint_name = joint_info[1].decode('utf-8')
            self.joint_indices[joint_name] = i
            print(f"  Joint {i}: {joint_name} (type={joint_info[2]})")

            # Reset joint to zero position
            p.resetJointState(body_id, i, targetValue=0.0, targetVelocity=0.0)

            # Note: Joint damping is now primarily set in the URDF <dynamics> element
            # This provides more realistic motor behavior (velocity-proportional resistance).
            # The URDF damping value takes precedence over changeDynamics if specified.
            # We keep linearDamping and angularDamping at 0 so only joint damping applies.
            p.changeDynamics(
                body_id, i,
                linearDamping=0.0,
                angularDamping=0.0
            )

            # Disable motor by setting velocity control with zero force
            # This prevents PyBullet's default motor from interfering
            p.setJointMotorControl2(
                bodyUniqueId=body_id,
                jointIndex=i,
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=0,
                force=0
            )

            # Enable joint force/torque sensor (for stress monitoring later)
            p.enableJointForceTorqueSensor(body_id, i, enableSensor=True)

        print(f"Loaded URDF: {name} (body_id={body_id}, {num_joints} joints)")
        return body_id

    def load_mesh(self, mesh_path: str, name: str = "mesh",
                   position: Tuple[float, float, float] = (0, 0, 1),
                   mass: float = 1.0) -> int:
        """
        Load a mesh file (OBJ) as a rigid body.

        Args:
            mesh_path: Path to OBJ file
            name: Name for this body
            position: (x, y, z) starting position
            mass: Mass in kg

        Returns:
            PyBullet body ID
        """
        # Create collision shape from mesh
        collision_shape = p.createCollisionShape(
            shapeType=p.GEOM_MESH,
            fileName=mesh_path
        )

        # Create visual shape from same mesh
        visual_shape = p.createVisualShape(
            shapeType=p.GEOM_MESH,
            fileName=mesh_path,
            rgbaColor=[0.7, 0.7, 0.7, 1.0]  # Gray color
        )

        # Create multi-body
        body_id = p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=position
        )

        self.bodies[name] = body_id
        print(f"Loaded mesh: {name} (body_id={body_id}, mass={mass}kg)")
        return body_id

    def get_joint_state(self, body_name: str, joint_name: str) -> Tuple[float, float]:
        """
        Get the state of a joint.

        Args:
            body_name: Name of the body
            joint_name: Name of the joint

        Returns:
            Tuple of (position in radians/meters, velocity in rad/s or m/s)
            
        Note:
            For revolute joints, position is normalized to (-pi, pi] range.
            This allows proper joint limits without needing extreme values.
        """
        body_id = self.bodies[body_name]
        joint_index = self.joint_indices[joint_name]

        joint_state = p.getJointState(body_id, joint_index)
        position = joint_state[0]  # Joint position
        velocity = joint_state[1]  # Joint velocity

        # Get joint info to check if it's revolute (rotational)
        joint_info = p.getJointInfo(body_id, joint_index)
        joint_type = joint_info[2]  # Joint type
        
        # For revolute joints (type 0), normalize position to (-pi, pi]
        if joint_type == 0:  # REVOLUTE
            import math
            # Normalize to (-pi, pi]
            position = ((position + math.pi) % (2 * math.pi)) - math.pi
            if position == -math.pi:
                position = math.pi

        return position, velocity

    def apply_joint_torque(self, body_name: str, joint_name: str, torque: float):
        """
        Apply torque to a joint (force control).

        Args:
            body_name: Name of the body
            joint_name: Name of the joint
            torque: Torque in Nm (or force in N for prismatic joints)
        """
        body_id = self.bodies[body_name]
        joint_index = self.joint_indices[joint_name]

        # Get joint info to determine which link this joint drives
        joint_info = p.getJointInfo(body_id, joint_index)
        link_index = joint_index  # In PyBullet, link index matches joint index for driven links
        
        # Get the joint axis
        axis = joint_info[13]  # Joint axis from joint info
        
        # Calculate torque vector in world frame
        # Torque = magnitude * axis direction
        torque_vector = [axis[0] * torque, axis[1] * torque, axis[2] * torque]

        # Apply external torque to the link driven by this joint
        p.applyExternalTorque(
            objectUniqueId=body_id,
            linkIndex=link_index,
            torqueObj=torque_vector,
            flags=p.WORLD_FRAME
        )

    def step(self, num_steps: int = 1):
        """
        Step the simulation forward.

        Args:
            num_steps: Number of simulation steps (each is TIMESTEP seconds)
        """
        for _ in range(num_steps):
            p.stepSimulation()

    def disconnect(self):
        """Disconnect from PyBullet."""
        p.disconnect()
        print("PhysicsEngine disconnected")


if __name__ == "__main__":
    # Basic test
    engine = PhysicsEngine(gui=True)

    # Load a simple shape
    import time
    collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.1])
    visual_shape = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.1, 0.1, 0.1], rgbaColor=[1, 0, 0, 1])
    cube_id = p.createMultiBody(baseMass=1, baseCollisionShapeIndex=collision_shape,
                                  baseVisualShapeIndex=visual_shape, basePosition=[0, 0, 1])

    print("Simulating falling cube (press Ctrl+C to stop)...")
    try:
        while True:
            engine.step()
            time.sleep(engine.TIMESTEP)
    except KeyboardInterrupt:
        print("\nStopping simulation")

    engine.disconnect()
