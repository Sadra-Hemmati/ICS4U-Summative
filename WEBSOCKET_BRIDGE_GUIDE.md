# HAL WebSocket Bridge - Universal Language Support

SubsystemSim now supports robot code written in **Java, C++, and Python** through the HAL WebSocket Bridge.

## How It Works

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│  Robot Code     │ ◄────────────────────────► │  SubsystemSim    │
│  (Java/C++/Py)  │    Motor Commands          │  WebSocket Bridge│
│                 │    Encoder Feedback        │                  │
│  + HAL Sim WS   │                            │  + PyBullet      │
└─────────────────┘                            └──────────────────┘
```

1. Robot code runs with HAL WebSocket extension (creates WS server)
2. SubsystemSim connects as WebSocket client
3. Motor commands flow: Robot Code → SubsystemSim → PyBullet
4. Sensor data flows back: PyBullet → SubsystemSim → Robot Code

## Installation

Install the websockets library:

```bash
pip install websockets
```

Or reinstall all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Start SubsystemSim WebSocket Bridge

In one terminal, start the physics simulator:

```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config examples/simple_arm/arm_config.json
```

You should see:

```
SubsystemSim HAL WebSocket Bridge
==================================================
Waiting for WebSocket connection...
```

### Step 2: Run Your Robot Code

The SubsystemSim bridge is now waiting for your robot code to connect.

#### For Java Robot Code

```bash
cd /path/to/your/java/robot/project
./gradlew simulateJava -Phalsim
```

Or on Windows:

```bash
gradlew.bat simulateJava -Phalsim
```

The `-Phalsim` flag enables the HAL WebSocket simulation extension.

#### For C++ Robot Code

```bash
cd /path/to/your/cpp/robot/project
./gradlew simulateNative -Phalsim
```

Or on Windows:

```bash
gradlew.bat simulateNative -Phalsim
```

#### For Python Robot Code

```bash
cd /path/to/your/python/robot
python robot.py sim
```

Python robot code automatically loads the HAL sim WebSocket extension.

### Step 3: Control the Robot

Once connected, you'll see in the SubsystemSim terminal:

```
✓ Connected to HAL simulation WebSocket
Subscribed to PWM[0]
Starting simulation loop...
Robot code is now controlling the simulation!
```

The PyBullet window will show your mechanism moving based on your robot code!

## Example: Java Robot Code

Here's a minimal Java robot program that works with SubsystemSim:

```java
package frc.robot;

import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.motorcontrol.PWMSparkMax;
import edu.wpi.first.wpilibj.Encoder;

public class Robot extends TimedRobot {
    private PWMSparkMax motor;
    private Encoder encoder;

    @Override
    public void robotInit() {
        motor = new PWMSparkMax(0);  // PWM port 0
        encoder = new Encoder(0, 1);  // DIO ports 0, 1
        encoder.setDistancePerPulse((2.0 * Math.PI) / 2048.0);  // Radians per tick
    }

    @Override
    public void autonomousPeriodic() {
        // Simple position control
        double targetPosition = 1.0;  // 1 radian (~57 degrees)
        double currentPosition = encoder.getDistance();
        double error = targetPosition - currentPosition;

        // P controller
        double motorCommand = 0.5 * error;
        motorCommand = Math.max(-1.0, Math.min(1.0, motorCommand));

        motor.set(motorCommand);

        System.out.println("Position: " + currentPosition + ", Command: " + motorCommand);
    }
}
```

## Example: C++ Robot Code

```cpp
#include <frc/TimedRobot.h>
#include <frc/motorcontrol/PWMSparkMax.h>
#include <frc/Encoder.h>

class Robot : public frc::TimedRobot {
private:
    frc::PWMSparkMax motor{0};  // PWM port 0
    frc::Encoder encoder{0, 1};  // DIO ports 0, 1

public:
    void RobotInit() override {
        encoder.SetDistancePerPulse((2.0 * 3.14159) / 2048.0);  // Radians per tick
    }

    void AutonomousPeriodic() override {
        // Simple position control
        double targetPosition = 1.0;  // 1 radian
        double currentPosition = encoder.GetDistance();
        double error = targetPosition - currentPosition;

        // P controller
        double motorCommand = 0.5 * error;
        motorCommand = std::clamp(motorCommand, -1.0, 1.0);

        motor.Set(motorCommand);
    }
};

int main() {
    return frc::StartRobot<Robot>();
}
```

## Configuration

### WebSocket Port

By default, SubsystemSim connects to `ws://localhost:3300`. To change this:

```bash
python -m subsystemsim.hal_bridge.websocket_bridge --config your_config.json --ws-uri ws://localhost:3300
```

### Motor and Sensor Mapping

SubsystemSim reads motor and sensor mappings from your JSON config file:

```json
{
  "motors": [
    {
      "name": "arm_motor",
      "type": "neo",
      "joint": "shoulder",
      "gear_ratio": 60.0,
      "hal_port": 0,  ← Maps to PWM port in robot code
      "inverted": false
    }
  ],
  "sensors": [
    {
      "name": "arm_encoder",
      "type": "encoder",
      "joint": "shoulder",
      "hal_ports": [0, 1],  ← Maps to DIO ports in robot code
      "ticks_per_rev": 2048
    }
  ]
}
```

**Important**: Your robot code's PWM/DIO port numbers must match the `hal_port` and `hal_ports` in the config!

## Troubleshooting

### "Failed to connect" Error

**Problem**: SubsystemSim can't connect to robot code

**Solutions**:
- Make sure robot code is running FIRST
- Verify you're using the `-Phalsim` flag (Java/C++)
- Check that ports match (default is 3300)
- Verify firewall isn't blocking localhost connections

### Motors Not Moving

**Problem**: Physics loads but motors don't respond

**Solutions**:
- Check PWM port numbers match between robot code and config
- Verify robot code is actually sending motor commands (add print statements)
- Make sure robot is in the correct mode (Autonomous/Teleop, not Disabled)

### Encoder Values Always Zero

**Problem**: Robot code reads encoder as always 0

**Solutions**:
- Check DIO port numbers match between robot code and config
- Verify encoder is initialized with correct `distancePerPulse`
- Check that physics simulation is running (PyBullet window updating)

## Advantages Over pyfrc-Only Approach

| Feature | pyfrc (Old) | WebSocket Bridge (New) |
|---------|-------------|------------------------|
| Java Support | ✗ No | ✓ Yes |
| C++ Support | ✗ No | ✓ Yes |
| Python Support | ✓ Yes | ✓ Yes |
| Runs unmodified robot code | ✗ No | ✓ Yes |
| FRC Team compatibility | ~10% | ~100% |
| Requires code changes | Yes | No |

## Next Steps

1. Create your subsystem config JSON file
2. Start SubsystemSim WebSocket bridge
3. Run your robot code with HAL sim WebSocket enabled
4. Your real robot code now controls the physics simulation!

---

**Note**: This approach is language-agnostic and works with ANY WPILib robot code that uses the standard HAL simulation framework.
