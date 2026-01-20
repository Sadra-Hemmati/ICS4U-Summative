"""
Diagnostic tool to see exactly what messages WPILib HAL Sim sends.
Run this INSTEAD of the normal bridge to see all WebSocket traffic.
"""

import asyncio
import websockets
import json
from collections import defaultdict

class WSDiagnostic:
    def __init__(self, ws_uri: str = "ws://localhost:3300/wpilibws"):
        self.ws_uri = ws_uri
        self.message_types = defaultdict(int)
        self.device_types = defaultdict(set)  # type -> set of device names
        self.device_fields = defaultdict(set)  # device_name -> set of field names
        self.can_devices = {}  # device_name -> latest data
        self.total_messages = 0

    async def run(self):
        print(f"Connecting to {self.ws_uri}...")
        print("This will show ALL WebSocket messages from WPILib HAL Sim")
        print("Press Ctrl+C to stop and see summary\n")

        try:
            async with websockets.connect(self.ws_uri) as ws:
                print("[OK] Connected!\n")
                print("="*70)
                print("LIVE MESSAGE LOG (first 100 of each type)")
                print("="*70 + "\n")

                type_counts = defaultdict(int)

                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.1)
                        self.total_messages += 1

                        data = json.loads(msg)
                        msg_type = data.get("type", "unknown")
                        device = data.get("device", "")
                        msg_data = data.get("data", {})

                        self.message_types[msg_type] += 1
                        self.device_types[msg_type].add(device)

                        key = f"{msg_type}:{device}"
                        for field in msg_data.keys():
                            self.device_fields[key].add(field)

                        type_counts[msg_type] += 1

                        # Log SimDevice messages in detail (motors are here)
                        if msg_type == "SimDevice":
                            self.can_devices[device] = msg_data
                            # Always print SimDevice messages (limited)
                            if type_counts[msg_type] <= 100:
                                print(f"[SimDevice] {device}")
                                print(f"    Fields: {list(msg_data.keys())}")
                                # Print non-init fields
                                for k, v in msg_data.items():
                                    if not k.startswith("<init") and v != 0:
                                        print(f"    {k}: {v}")
                                print()

                        # Log PWM messages
                        elif msg_type == "PWM" and type_counts[msg_type] <= 50:
                            print(f"[PWM] device={device}, data={msg_data}")

                        # Log other potentially interesting types
                        elif msg_type not in ["DriverStation", "RoboRIO", "Joystick"] and type_counts[msg_type] <= 20:
                            print(f"[{msg_type}] device={device}, data={msg_data}")

                    except asyncio.TimeoutError:
                        pass

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}")

        print("\n\n" + "="*70)
        print("DIAGNOSTIC SUMMARY")
        print("="*70)

        print(f"\nTotal messages received: {self.total_messages}")

        print("\n--- Message Types ---")
        for msg_type, count in sorted(self.message_types.items(), key=lambda x: -x[1]):
            print(f"  {msg_type}: {count} messages")

        print("\n--- Devices by Type ---")
        for msg_type, devices in sorted(self.device_types.items()):
            print(f"\n  {msg_type}:")
            for device in sorted(devices):
                key = f"{msg_type}:{device}"
                fields = self.device_fields.get(key, set())
                print(f"    - {device or '(empty)'}")
                if fields:
                    print(f"      Fields: {sorted(fields)}")

        print("\n--- CAN/SimDevice Details ---")
        for device, data in sorted(self.can_devices.items()):
            print(f"\n  {device}:")
            for k, v in sorted(data.items()):
                print(f"    {k}: {v}")

        print("\n" + "="*70)
        print("Use this info to update websocket_bridge.py to match actual field names")
        print("="*70)


if __name__ == "__main__":
    import sys
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:3300/wpilibws"
    asyncio.run(WSDiagnostic(uri).run())
