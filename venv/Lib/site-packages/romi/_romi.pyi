from __future__ import annotations
import typing
import wpilib._wpilib
import wpimath.units
__all__: list[str] = ['OnBoardIO', 'RomiGyro', 'RomiMotor']
class OnBoardIO:
    """
    This class represents the onboard IO of the Romi
    reference robot. This includes the pushbuttons and
    LEDs.
    
    DIO 0 - Button A (input only)
    DIO 1 - Button B (input) or Green LED (output)
    DIO 2 - Button C (input) or Red LED (output)
    DIO 3 - Yellow LED (output only)
    """
    class ChannelMode:
        """
        Mode for Romi onboard IO
        
        Members:
        
          INPUT : Input
        
          OUTPUT : Output
        """
        INPUT: typing.ClassVar[OnBoardIO.ChannelMode]  # value = <ChannelMode.INPUT: 0>
        OUTPUT: typing.ClassVar[OnBoardIO.ChannelMode]  # value = <ChannelMode.OUTPUT: 1>
        __members__: typing.ClassVar[dict[str, OnBoardIO.ChannelMode]]  # value = {'INPUT': <ChannelMode.INPUT: 0>, 'OUTPUT': <ChannelMode.OUTPUT: 1>}
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    kMessageInterval: typing.ClassVar[float] = 1.0
    def __init__(self, dio1: OnBoardIO.ChannelMode, dio2: OnBoardIO.ChannelMode) -> None:
        ...
    def getButtonAPressed(self) -> bool:
        """
        Gets if the A button is pressed.
        """
    def getButtonBPressed(self) -> bool:
        """
        Gets if the B button is pressed.
        """
    def getButtonCPressed(self) -> bool:
        """
        Gets if the C button is pressed.
        """
    def setGreenLed(self, value: bool) -> None:
        """
        Sets the green LED.
        """
    def setRedLed(self, value: bool) -> None:
        """
        Sets the red LED.
        """
    def setYellowLed(self, value: bool) -> None:
        """
        Sets the yellow LED.
        """
    @property
    def m_nextMessageTime(self) -> wpimath.units.seconds:
        ...
class RomiGyro:
    """
    Use a rate gyro to return the robots heading relative to a starting position.
    
    This class is for the Romi onboard gyro, and will only work in
    simulation/Romi mode. Only one instance of a RomiGyro is supported.
    """
    def __init__(self) -> None:
        ...
    def getAngle(self) -> wpimath.units.radians:
        """
        Return the actual angle in radians that the robot is currently facing.
        
        The angle is based on integration of the returned rate form the gyro.
        The angle is continuous, that is, it will continue from 2π->3π radians.
        This allows algorithms that wouldn't want to see a discontinuity in the
        gyro output as it sweeps from 2π to 0 on the second time around.
        
        :returns: The current heading of the robot.
        """
    def getAngleX(self) -> wpimath.units.radians:
        """
        Get the currently reported angle around the X-axis.
        
        :returns: Current angle around X-axis.
        """
    def getAngleY(self) -> wpimath.units.radians:
        """
        Get the currently reported angle around the Y-axis.
        
        :returns: Current angle around Y-axis.
        """
    def getAngleZ(self) -> wpimath.units.radians:
        """
        Get the currently reported angle around the Z-axis.
        
        :returns: Current angle around Z-axis.
        """
    def getRate(self) -> wpimath.units.radians_per_second:
        """
        Return the rate of rotation of the gyro
        
        The rate is based on the most recent reading of the gyro.
        
        :returns: The current rate.
        """
    def getRateX(self) -> wpimath.units.radians_per_second:
        """
        Get the rate of turn in around the X-axis.
        
        :returns: Rate of turn.
        """
    def getRateY(self) -> wpimath.units.radians_per_second:
        """
        Get the rate of turn in around the Y-axis.
        
        :returns: Rate of turn.
        """
    def getRateZ(self) -> wpimath.units.radians_per_second:
        """
        Get the rate of turn around the Z-axis.
        
        :returns: Rate of turn.
        """
    def reset(self) -> None:
        """
        Resets the gyro
        """
class RomiMotor(wpilib._wpilib.PWMMotorController):
    """
    RomiMotor
    
    A general use PWM motor controller representing the motors on a Romi robot
    """
    def __init__(self, channel: typing.SupportsInt) -> None:
        """
        Constructor for a RomiMotor.
        
        :param channel: The PWM channel that the RomiMotor is attached to.
                        0 is left, 1 is right
        """
