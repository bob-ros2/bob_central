#!/usr/bin/env python3
"""
Simple botnet detection for ROS 2 mesh security
Basic pattern monitoring without ML dependencies
"""

import rclpy
from rclpy.node import Node
import time
from datetime import datetime
import json
import os
import argparse

class SimpleBotnetDetector(Node):
    def __init__(self, verbose=False):
        super().__init__("simple_botnet_detector")
        
        self.verbose = verbose
        
        # Create report directory
        log_dir = os.environ.get("SECURITY_LOG_DIR", "/root/eva/security_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Store topic activity
        self.topic_activity = {}
        self.start_time = time.time()
        
        # Alert publisher
        from std_msgs.msg import String
        self.alert_pub = self.create_publisher(String, "/eva/security/simple_alerts", 10)
        
        # Monitor topic list periodically
        self.create_timer(5.0, self.check_topics)
        
        if self.verbose:
            self.get_logger().info("Simple botnet detector initialized")
        else:
            self.get_logger().info("Simple detection active")
    
    def check_topics(self):
        """Check current topics and detect anomalies"""
        try:
            topics = self.get_topic_names_and_types()
            current_time = time.time()
            
            anomalies = []
            
            for topic_name, _ in topics:
                if topic_name not in self.topic_activity:
                    self.topic_activity[topic_name] = {
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "check_count": 1
                    }
                else:
                    self.topic_activity[topic_name]["last_seen"] = current_time
                    self.topic_activity[topic_name]["check_count"] += 1
            
            # Detect anomalies: topics appearing/disappearing rapidly
            elapsed = current_time - self.start_time
            if elapsed > 10:  # After warmup period
                for topic, data in self.topic_activity.items():
                    lifetime = data["last_seen"] - data["first_seen"]
                    if lifetime < 2.0 and data["check_count"] > 5:
                        # Topic appeared and disappeared rapidly (botnet-like churn)
                        alert = {
                            "topic": topic,
                            "type": "RAPID_CHURN",
                            "severity": "MEDIUM",
                            "description": "Topic appearing/disappearing rapidly (botnet node rotation)",
                            "lifetime_seconds": lifetime,
                            "checks": data["check_count"],
                            "timestamp": current_time
                        }
                        
                        anomalies.append(alert)
                        
                        # Publish alert
                        from std_msgs.msg import String
                        msg = String()
                        msg.data = json.dumps(alert)
                        self.alert_pub.publish(msg)
            
            if anomalies:
                self.report_anomalies(anomalies, len(topics))
                
        except Exception as e:
            self.get_logger().error(f"Error checking topics: {e}")
    
    def report_anomalies(self, anomalies, total_topics):
        """Report detected anomalies"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_topics": total_topics,
            "anomalies": anomalies,
            "system": "Simple Botnet Detector"
        }
        
        for anomaly in anomalies:
            if self.verbose:
                self.get_logger().warning(
                    f"ANOMALY: {anomaly[type]} on {anomaly[topic]} "
                    f"(Lifetime: {anomaly[lifetime_seconds]:.2f}s)"
                )
        
        # Save report
        log_dir = os.environ.get("SECURITY_LOG_DIR", "/root/eva/security_logs")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_dir}/simple_detection_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        if self.verbose:
            self.get_logger().info(f"Report saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Simple botnet detection for ROS 2")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    
    args = parser.parse_args()
    
    rclpy.init()
    detector = SimpleBotnetDetector(verbose=args.verbose)
    
    print("=" * 60)
    print("SIMPLE BOTNET DETECTION SYSTEM")
    print("=" * 60)
    print("\nMonitoring ROS 2 topics for rapid churn patterns...")
    print("Detects topics appearing/disappearing rapidly (botnet node rotation)")
    
    try:
        rclpy.spin(detector)
    except KeyboardInterrupt:
        print("\nDetection stopped")
    finally:
        detector.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()