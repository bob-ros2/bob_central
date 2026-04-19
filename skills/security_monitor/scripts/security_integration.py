#!/usr/bin/env python3
"""
Security Integration Bridge
Routes security alerts between detection systems and alarm synthesis
"""

import rclpy
from rclpy.node import Node
import json
import time
import argparse

class SecurityBridge(Node):
    """Bridge between detection systems and alarm synthesis"""
    
    def __init__(self, verbose=False):
        super().__init__("security_bridge")
        
        self.verbose = verbose
        
        from std_msgs.msg import String
        
        # Subscribe to ML-based alerts
        self.create_subscription(
            String,
            "/eva/security/ml_alerts",
            self.handle_ml_alert,
            10
        )
        
        # Subscribe to simple detector alerts
        self.create_subscription(
            String,
            "/eva/security/simple_alerts", 
            self.handle_simple_alert,
            10
        )
        
        # Publish to alarm system
        self.alarm_pub = self.create_publisher(String, "/eva/security/alerts", 10)
        
        # Alert statistics
        self.alert_count = {"ml": 0, "simple": 0, "total": 0}
        self.start_time = time.time()
        
        # Status timer
        self.create_timer(30.0, self.log_status)
        
        if self.verbose:
            self.get_logger().info("Security Bridge initialized with verbose logging")
        else:
            self.get_logger().info("Security Bridge active")
    
    def handle_ml_alert(self, msg):
        """Route ML-based security alerts to alarm system"""
        self.process_alert(msg, "ml")
    
    def handle_simple_alert(self, msg):
        """Route simple detector alerts to alarm system"""
        self.process_alert(msg, "simple")
    
    def process_alert(self, msg, source):
        """Process and route security alerts"""
        try:
            alert = json.loads(msg.data)
            
            # Add bridge metadata
            alert["processed_by"] = "security_bridge"
            alert["source_detector"] = source
            alert["bridge_timestamp"] = time.time()
            
            # Forward to alarm synthesizer
            from std_msgs.msg import String
            forward_msg = String()
            forward_msg.data = json.dumps(alert)
            
            self.alarm_pub.publish(forward_msg)
            
            # Update statistics
            self.alert_count[source] += 1
            self.alert_count["total"] += 1
            
            if self.verbose:
                self.get_logger().warning(
                    f"Alert routed from {source}: {alert.get(type, UNKNOWN)} "
                    f"(Severity: {alert.get(severity, UNKNOWN)})"
                )
            
        except Exception as e:
            self.get_logger().error(f"Error routing alert from {source}: {e}")
    
    def log_status(self):
        """Log bridge status"""
        elapsed = time.time() - self.start_time
        alerts_per_minute = (self.alert_count["total"] / elapsed) * 60 if elapsed > 0 else 0
        
        status = {
            "timestamp": time.time(),
            "alerts_total": self.alert_count["total"],
            "alerts_ml": self.alert_count["ml"],
            "alerts_simple": self.alert_count["simple"],
            "alerts_per_minute": round(alerts_per_minute, 2),
            "uptime_seconds": round(elapsed, 1)
        }
        
        if self.verbose:
            self.get_logger().info(
                f"Bridge status: {self.alert_count[total]} alerts "
                f"({self.alert_count[ml]} ML, {self.alert_count[simple]} simple) "
                f"in {elapsed:.1f}s ({alerts_per_minute:.1f}/min)"
            )


def main():
    parser = argparse.ArgumentParser(description="Security alert integration bridge")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    
    args = parser.parse_args()
    
    rclpy.init()
    bridge = SecurityBridge(verbose=args.verbose)
    
    print("=" * 50)
    print("SECURITY ALERT INTEGRATION BRIDGE")
    print("=" * 50)
    print("Routing alerts between:")
    print("  • ML Botnet Detection → Alarm Synthesis")
    print("  • Simple Detection → Alarm Synthesis")
    print("\nListening on /eva/security/{ml_alerts,simple_alerts}...")
    
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        print("\nBridge stopped")
    finally:
        bridge.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()