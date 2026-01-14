from __future__ import annotations
import typing
import wpilib._wpilib
import wpilib.interfaces._interfaces
import wpimath.geometry._geometry
import wpimath.units
__all__: list[str] = ['XRPGyro', 'XRPMotor', 'XRPOnBoardIO', 'XRPRangefinder', 'XRPReflectanceSensor', 'XRPServo']
class XRPGyro:
    """
    Use a rate gyro to return the robots heading relative to a starting position.
    
    This class is for the XRP onboard gyro, and will only work in
    simulation/XRP mode. Only one instance of a XRPGyro is supported.
    """
    def __init__(self) -> None:
        """
        Constructs an XRPGyro.
        
        Only one instance of a XRPGyro is supported.
        """
    def getAngle(self) -> wpimath.units.radians:
        """
        Return the actual angle in radians that the robot is currently facing.
        
        The angle is based on integration of the returned rate form the gyro.
        The angle is continuous, that is, it will continue from 2π->2.1π.
        This allows algorithms that wouldn't want to see a discontinuity in the
        gyro output as it sweeps from 2π to 0 radians on the second time around.
        
        :returns: the current heading of the robot in radians.
        """
    def getAngleX(self) -> wpimath.units.radians:
        """
        Gets the currently reported angle around the X-axis.
        
        :returns: current angle around X-axis in radians
        """
    def getAngleY(self) -> wpimath.units.radians:
        """
        Gets the currently reported angle around the Y-axis.
        
        :returns: current angle around Y-axis in radians
        """
    def getAngleZ(self) -> wpimath.units.radians:
        """
        Gets the currently reported angle around the Z-axis.
        
        :returns: current angle around Z-axis in radians
        """
    def getRate(self) -> wpimath.units.radians_per_second:
        """
        Return the rate of rotation of the gyro
        
        The rate is based on the most recent reading of the gyro.
        
        :returns: the current rate in radians per second
        """
    def getRateX(self) -> wpimath.units.radians_per_second:
        """
        Gets the rate of turn in radians-per-second around the X-axis.
        
        :returns: rate of turn in radians-per-second
        """
    def getRateY(self) -> wpimath.units.radians_per_second:
        """
        Gets the rate of turn in radians-per-second around the Y-axis.
        
        :returns: rate of turn in radians-per-second
        """
    def getRateZ(self) -> wpimath.units.radians_per_second:
        """
        Gets the rate of turn in radians-per-second around the Z-axis.
        
        :returns: rate of turn in radians-per-second
        """
    def getRotation2d(self) -> wpimath.geometry._geometry.Rotation2d:
        """
        Gets the angle the robot is facing.
        
        :returns: A Rotation2d with the current heading.
        """
    def reset(self) -> None:
        """
        Reset the gyro angles to 0.
        """
class XRPMotor(wpilib.interfaces._interfaces.MotorController, wpilib._wpilib.MotorSafety):
    """
    XRPMotor.
    
    A SimDevice based motor controller representing the motors on an XRP robot
    """
    def __init__(self, deviceNum: typing.SupportsInt) -> None:
        """
        Constructs an XRPMotor.
        
        :param deviceNum: the motor channel
        """
    def disable(self) -> None:
        ...
    def get(self) -> float:
        ...
    def getDescription(self) -> str:
        ...
    def getInverted(self) -> bool:
        ...
    def set(self, value: typing.SupportsFloat) -> None:
        ...
    def setInverted(self, isInverted: bool) -> None:
        ...
    def stopMotor(self) -> None:
        ...
class XRPOnBoardIO:
    """
    This class represents the onboard IO of the XRP
    reference robot. This the USER push button and
    LED.
    
    DIO 0 - USER Button (input only)
    DIO 1 - LED (output only)
    """
    kMessageInterval: typing.ClassVar[float] = 1.0
    def __init__(self) -> None:
        ...
    def getLed(self) -> bool:
        """
        Gets the state of the yellow LED.
        
        :returns: True if LED is active, false otherwise.
        """
    def getUserButtonPressed(self) -> bool:
        """
        Gets if the USER button is pressed.
        
        :returns: True if the USER button is currently pressed.
        """
    def setLed(self, value: bool) -> None:
        """
        Sets the yellow LED.
        
        :param value: True to activate LED, false otherwise.
        """
    @property
    def m_nextMessageTime(self) -> wpimath.units.seconds:
        ...
class XRPRangefinder:
    """
    This class represents the ultrasonic rangefinder on an XRP robot.
    """
    def __init__(self) -> None:
        ...
    def getDistance(self) -> wpimath.units.meters:
        """
        Get the measured distance in meters. Distance further than 4m will be
        reported as 4m.
        
        :returns: distance in meters
        """
class XRPReflectanceSensor:
    """
    This class represents the reflectance sensor pair on an XRP robot.
    """
    def __init__(self) -> None:
        ...
    def getLeftReflectanceValue(self) -> float:
        """
        Returns the reflectance value of the left sensor.
        
        :returns: value between 0.0 (white) and 1.0 (black).
        """
    def getRightReflectanceValue(self) -> float:
        """
        Returns the reflectance value of the right sensor.
        
        :returns: value between 0.0 (white) and 1.0 (black).
        """
class XRPServo:
    """
    XRPServo.
    
    A SimDevice based servo
    """
    def __init__(self, deviceNum: typing.SupportsInt) -> None:
        """
        Constructs an XRPServo.
        
        :param deviceNum: the servo channel
        """
    def getAngle(self) -> wpimath.units.radians:
        """
        Get the servo angle.
        
        :returns: Current servo angle in radians
        """
    def getPosition(self) -> float:
        """
        Get the servo position.
        
        :deprecated: Use GetAngle() instead
        
        :returns: Current servo position
        """
    def setAngle(self, angle: wpimath.units.radians) -> None:
        """
        Set the servo angle.
        
        :param angle: Desired angle in radians
        """
    def setPosition(self, position: typing.SupportsFloat) -> None:
        """
        Set the servo position.
        
        :deprecated: Use SetAngle() instead
        
        :param position: Desired position (Between 0.0 and 1.0)
        """
