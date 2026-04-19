#!/usr/bin/env python3
"""
Bridging Eva's Security Alerts to BobSynth Engine
Translates security severity into synthesizer parameters
"""

import rclpy
from rclpy.node import Node
import json
from std_msgs.msg import String

class AlarmBobSynthBridge(Node):
    def __init__(self):
        super().__init__("alarm_bobsynth_bridge")
        
        # Severity to Synth Mapping
        # Mapping severity to oscillator frequencies and patterns
        self.severity_map = {
            "LOW": {
                "freq": 440.0,
                "wave": "sine",
                "attack": 0.1,
                "decay": 0.2,
                "sustain": 0.5,
                "release": 0.2,
                "volume": 0.4
            },
            "MEDIUM": {
                "freq": 880.0,
                "wave": "sawtooth",
                "attack": 0.05,
                "decay": 0.1,
                "sustain": 0.6,
                "release": 0.1,
                "volume": 0.6
            },
            "HIGH": {
                "freq": 1760.0,
                "wave": "square",
                "attack": 0.01,
                "decay": 0.05,
                "sustain": 0.8,
                "release": 0.05,
                "volume": 0.8
            },
            "CRITICAL": {
                "freq": 3520.0,
                "wave": "square",
                "attack": 0.005,
                "decay": 0.03,
                "sustain": 1.0,
                "release": 0.03,
                "volume": 1.0
            }
        }

        # Publisher to BobSynth Config
        self.pub_synth = self.create_publisher(
            String,
            "/eva/sounds/synth_config",
            10
        )

        # Subscriber to Security Alerts
        self.create_subscription(
            String,
            "/eva/security/alerts",
            self.alert_callback,
            10
        )

        self.get_logger().info("Alarm to BobSynth Bridge initialized")
        self.get_logger().info("Target Topic: /eva/sounds/synth_config")

    def alert_callback(self, msg):
        try:
            alert = json.loads(msg.data)
            severity = alert.get("severity", "MEDIUM")
            
            if severity in self.severity_map:
                params = self.severity_map[severity]
                
                # Construct Flat BobSynth Commands (as expected by C++ parser)
                base_cmd = {
                    "frequency": params["freq"],
                    "waveform": params["wave"],
                    "attack": params["attack"],
                    "decay": params["decay"],
                    "sustain": params["sustain"],
                    "release": params["release"],
                    "amplitude": params["volume"]
                }
                
                # 1. Trigger NOTE ON
                on_cmd = base_cmd.copy()
                on_cmd["note_on"] = True
                
                on_msg = String()
                on_msg.data = json.dumps(on_cmd)
                self.pub_synth.publish(on_msg)
                
                # 2. Trigger NOTE OFF after a short duration (to allow envelope)
                # We use a timer to send the release signal
                duration = 1.0 if severity != "CRITICAL" else 0.5
                import threading
                def trigger_off():
                    off_cmd = base_cmd.copy()
                    off_cmd["note_on"] = False
                    off_msg = String()
                    off_msg.data = json.dumps(off_cmd)
                    self.pub_synth.publish(off_msg)
                
                threading.Timer(duration, trigger_off).start()
                
                self.get_logger().info(f"Triggered {severity} alarm sequence on BobSynth")
            
        except Exception as e:
            self.get_logger().error(f"Bridge error: {e}")

def main():
    rclpy.init()
    node = AlarmBobSynthBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
