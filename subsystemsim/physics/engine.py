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
            # Configure camera for better viewing (zoomed out for larger mechanisms)
            p.resetDebugVisualizerCamera(
                cameraDistance=1.5,
                cameraYaw=45,
                cameraPitch=-30,
                cameraTargetPosition=[0, 0, 0.75]
            )
            # Disable unnecessary debug visualizer features for performance
            # These features can accumulate data and cause progressive lag
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)  # Disable side panel GUI
            p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 0)  # Disable shadows
            p.configureDebugVisualizer(p.COV_ENABLE_WIREFRAME, 0)  # Disable wireframe
            p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)  # Keep rendering on
            p.configureDebugVisualizer(p.COV_ENABLE_TINY_RENDERER, 0)  # Disable CPU renderer
            p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)  # Disable RGB preview
            p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)  # Disable depth preview
            p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)  # Disable segmentation
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
        Apply torque/force to a joint.

        For revolute joints: applies torque in Nm
        For prismatic joints: applies force in N

        Args:
            body_name: Name of the body
            joint_name: Name of the joint
            torque: Torque in Nm (revolute) or force in N (prismatic)
        """
        body_id = self.bodies[body_name]
        joint_index = self.joint_indices[joint_name]

        # Use cached joint info for performance (joint properties don't change)
        cache_key = (body_id, joint_index)
        if not hasattr(self, '_joint_cache'):
            self._joint_cache = {}

        if cache_key not in self._joint_cache:
            joint_info = p.getJointInfo(body_id, joint_index)
            self._joint_cache[cache_key] = {
                'type': joint_info[2],  # 0 = revolute, 1 = prismatic
                'axis': joint_info[13],
                'link_index': joint_index
            }

        cached = self._joint_cache[cache_key]
        joint_type = cached['type']
        axis = cached['axis']
        link_index = cached['link_index']

        if joint_type == 1:  # PRISMATIC joint - apply force
            # For prismatic joints, apply force along the joint axis
            force_vector = [axis[0] * torque, axis[1] * torque, axis[2] * torque]

            # Apply force at link center (LINK_FRAME avoids getLinkState call)
            p.applyExternalForce(
                objectUniqueId=body_id,
                linkIndex=link_index,
                forceObj=force_vector,
                posObj=[0, 0, 0],
                flags=p.LINK_FRAME
            )
        else:  # REVOLUTE joint - apply torque
            # Calculate torque vector in world frame
            torque_vector = [axis[0] * torque, axis[1] * torque, axis[2] * torque]

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
