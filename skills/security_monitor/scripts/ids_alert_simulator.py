#!/usr/bin/env python3
"""
IDS Alert Simulator for testing alarm synthesis system
"""

import rclpy
from rclpy.node import Node
import json
import time
import random
import argparse
from datetime import datetime

class IDSSimulator(Node):
    """Simulates IDS alerts for testing alarm synthesis"""
    
    def __init__(self, interval=5.0, severity_filter=None, count=None, verbose=False):
        super().__init__("ids_simulator")
        
        self.interval = interval
        self.severity_filter = severity_filter
        self.max_count = count
        self.verbose = verbose
        self.alert_count = 0
        
        # Publisher for security alerts
        from std_msgs.msg import String
        self.alert_pub = self.create_publisher(String, "/eva/security/alerts", 10)
        
        # Alert types based on our botnet detection research
        self.alert_types = [
            {
                "type": "BURST_COMMUNICATION",
                "description": "Botnet-like burst pattern detected",
                "severity": "HIGH"
            },
            {
                "type": "REGULAR_HEARTBEAT", 
                "description": "C&C heartbeat pattern identified",
                "severity": "MEDIUM"
            },
            {
                "type": "SYNCHRONIZED_ACTIVITY",
                "description": "Multiple nodes coordinating",
                "severity": "CRITICAL"
            },
            {
                "type": "RAPID_CHURN",
                "description": "Rapid node rotation detected",
                "severity": "LOW"
            },
            {
                "type": "UNAUTHORIZED_ACCESS",
                "description": "Unauthorized service discovery attempt",
                "severity": "HIGH"
            }
        ]
        
        # Filter alerts by severity if specified
        if severity_filter:
            self.alert_types = [a for a in self.alert_types if a["severity"] == severity_filter]
            if not self.alert_types:
                self.get_logger().error(f"No alert types match severity filter: {severity_filter}")
                return
        
        # Start simulation
        self.simulation_timer = self.create_timer(interval, self.generate_alert)
        
        if self.verbose:
            self.get_logger().info(f"IDS Alert Simulator initialized (interval={interval}s)")
            self.get_logger().info(f"Alert types: {len(self.alert_types)} patterns")
            if severity_filter:
                self.get_logger().info(f"Severity filter: {severity_filter}")
            if count:
                self.get_logger().info(f"Maximum alerts: {count}")
        else:
            self.get_logger().info("Alert simulator active")
    
    def generate_alert(self):
        """Generate a simulated IDS alert"""
        if self.max_count and self.alert_count >= self.max_count:
            self.get_logger().info(f"Reached maximum alert count: {self.max_count}")
            self.destroy_node()
            return
        
        alert = random.choice(self.alert_types)
        
        # Add additional details
        alert_details = {
            **alert,
            "timestamp": time.time(),
            "source": f"node_{random.randint(1, 100)}",
            "topic": random.choice([
                "/eva/streamer/control",
                "/eva/browser/command", 
                "/eva/llm_stream",
                "/eva/repl/input",
                "/eva/security/alerts"
            ]),
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "recommendation": random.choice([
                "Investigate immediately",
                "Monitor closely",
                "Isolate affected node",
                "Increase logging level",
                "Review access controls"
            ]),
            "simulated": True
        }
        
        # Publish alert
        from std_msgs.msg import String
        msg = String()
        msg.data = json.dumps(alert_details)
        
        self.alert_pub.publish(msg)
        
        self.alert_count += 1
        
        if self.verbose:
            self.get_logger().warning(
                f"Generated {alert_details[severity]} alert #{self.alert_count}: "
                f"{alert_details[type]} on {alert_details[topic]}"
            )
        
        # Randomize next alert interval (±50%)
        if self.interval > 0:
            variation = random.uniform(0.5, 1.5)
            new_interval = max(0.5, self.interval * variation)
            self.simulation_timer.timer_period_ns = int(new_interval * 1e9)


def main():
    parser = argparse.ArgumentParser(description="IDS Alert Simulator")
    parser.add_argument("--interval", type=float, default=5.0, help="Alert generation interval in seconds")
    parser.add_argument("--severity", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], help="Filter alerts by severity")
    parser.add_argument("--count", type=int, help="Number of alerts to generate before stopping")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    
    args = parser.parse_args()
    
    rclpy.init()
    simulator = IDSSimulator(
        interval=args.interval,
        severity_filter=args.severity,
        count=args.count,
        verbose=args.verbose
    )
    
    print("=" * 60)
    print("IDS ALERT SIMULATION SYSTEM")
    print("=" * 60)
    print(f"Interval: {args.interval} seconds")
    if args.severity:
        print(f"Severity filter: {args.severity}")
    if args.count:
        print(f"Maximum alerts: {args.count}")
    print("\nGenerating simulated security alerts...")
    print("Alerts will trigger audio warning tones via alarm synthesis")
    print("Press Ctrl+C to stop\n")
    
    try:
        rclpy.spin(simulator)
    except KeyboardInterrupt:
        print(f"\nSimulation stopped after {simulator.alert_count} alerts")
    finally:
        simulator.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()