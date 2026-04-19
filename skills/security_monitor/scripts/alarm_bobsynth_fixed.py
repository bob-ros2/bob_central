#!/usr/bin/env python3
"""
Alarm Synthesis using bob_synth for IDS alerts
Uses /synth_config topic to generate warning tones
"""

import rclpy
from rclpy.node import Node
import json
import time
import argparse
from datetime import datetime

class BobSynthAlarm(Node):
    """Generates warning tones using bob_synth via /synth_config"""
    
    def __init__(self, verbose=False):
        super().__init__("bobsynth_alarm")
        
        self.verbose = verbose
        
        # Severity to bob_synth configuration mapping
        self.severity_configs = {
            "LOW": {
                "frequency": 440.0,
                "waveform": "sine",
                "duration": 1.0,
                "volume": 0.3,
                "pattern": [0.5, 0.5]
            },
            "MEDIUM": {
                "frequency": 880.0,
                "waveform": "sine", 
                "duration": 0.8,
                "volume": 0.5,
                "pattern": [0.3, 0.2, 0.3, 0.2]
            },
            "HIGH": {
                "frequency": 1760.0,
                "waveform": "square",
                "duration": 0.6,
                "volume": 0.7,
                "pattern": [0.2, 0.1, 0.2, 0.1, 0.2, 0.1]
            },
            "CRITICAL": {
                "frequency": 3520.0,
                "waveform": "sawtooth",
                "duration": 0.4,
                "volume": 0.9,
                "pattern": [0.1, 0.05, 0.1, 0.05, 0.1, 0.05, 0.1, 0.05]
            }
        }
        
        # Subscribe to security alerts
        from std_msgs.msg import String
        self.create_subscription(
            String,
            "/eva/security/alerts",
            self.alert_callback,
            10
        )
        
        # Publisher for bob_synth configuration
        self.synth_pub = self.create_publisher(String, "/synth_config", 10)
        
        if self.verbose:
            self.get_logger().info("BobSynth Alarm system initialized")
        else:
            self.get_logger().info("BobSynth alarm active")
    
    def alert_callback(self, msg):
        """Receive security alerts and generate bob_synth tones"""
        try:
            alert = json.loads(msg.data)
            severity = alert.get("severity", "MEDIUM")
            
            if self.verbose:
                self.get_logger().info(f"Processing {severity} alert")
            
            # Generate tone using bob_synth
            self.generate_bob_synth_tone(severity, alert)
            
        except Exception as e:
            self.get_logger().error(f"Error processing alert: {e}")
    
    def generate_bob_synth_tone(self, severity, alert):
        """Generate tone using bob_synth configuration"""
        if severity not in self.severity_configs:
            severity = "MEDIUM"
        
        config = self.severity_configs[severity]
        
        # Create bob_synth configuration message
        synth_config = {
            "command": "play",
            "frequency": config["frequency"],
            "waveform": config["waveform"],
            "duration": config["duration"],
            "volume": config["volume"],
            "metadata": {
                "alert_severity": severity,
                "alert_type": alert.get("type", "unknown"),
                "timestamp": time.time()
            }
        }
        
        # Publish to bob_synth
        from std_msgs.msg import String
        msg = String()
        msg.data = json.dumps(synth_config)
        
        self.synth_pub.publish(msg)
        
        if self.verbose:
            self.get_logger().info(f"Sent {severity} tone to bob_synth")

def main():
    parser = argparse.ArgumentParser(description="Alarm synthesis using bob_synth")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    
    args = parser.parse_args()
    
    rclpy.init()
    alarm = BobSynthAlarm(verbose=args.verbose)
    
    print("=" * 60)
    print("BOB_SYNTH ALARM SYSTEM")
    print("=" * 60)
    print("Using bob_synth via /synth_config topic")
    print("\nListening for alerts on /eva/security/alerts...")
    
    try:
        rclpy.spin(alarm)
    except KeyboardInterrupt:
        print("\nBobSynth alarm stopped")
    finally:
        alarm.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()