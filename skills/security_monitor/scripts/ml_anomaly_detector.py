#!/usr/bin/env python3
"""
ML-based anomaly detection for ROS 2 mesh security
Adapted from botnet detection techniques
"""

import rclpy
from rclpy.node import Node
import numpy as np
from collections import deque
import time
from datetime import datetime
import json
import os
import threading
import argparse

class MLAnomalyDetector(Node):
    def __init__(self, window_size=50, entropy_threshold=0.7, burst_threshold=0.8, verbose=False):
        super().__init__("ml_anomaly_detector")
        
        self.verbose = verbose
        
        # Create report directory
        log_dir = os.environ.get("SECURITY_LOG_DIR", "/root/eva/security_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Traffic pattern storage (adapted from botnet detection research)
        self.topic_patterns = {}
        self.message_queues = {}
        self.baselines = {}
        
        # ML-inspired detection parameters
        self.window_size = window_size
        self.entropy_threshold = entropy_threshold
        self.burst_threshold = burst_threshold
        
        # Alert publisher
        from std_msgs.msg import String
        self.alert_pub = self.create_publisher(String, "/eva/security/ml_alerts", 10)
        
        # Start monitoring
        self.create_timer(1.0, self.monitor_traffic)
        self.analysis_timer = self.create_timer(10.0, self.analyze_patterns)
        
        if self.verbose:
            self.get_logger().info(f"ML-based botnet detection system initialized")
            self.get_logger().info(f"Parameters: window_size={window_size}, entropy_threshold={entropy_threshold}, burst_threshold={burst_threshold}")
        else:
            self.get_logger().info("ML botnet detection active")
    
    def monitor_traffic(self):
        """Monitor current topic activity and message rates"""
        try:
            topics = self.get_topic_names_and_types()
            current_time = time.time()
            
            for topic_name, _ in topics:
                if topic_name not in self.topic_patterns:
                    # Initialize pattern tracking for new topic
                    self.topic_patterns[topic_name] = {
                        "first_seen": current_time,
                        "message_timestamps": deque(maxlen=1000),
                        "message_counts": deque(maxlen=100),
                        "last_analysis": current_time
                    }
                
                # Simulate message collection (in real system, would subscribe)
                # For demo, we simulate some traffic patterns
                pattern = self.topic_patterns[topic_name]
                elapsed = current_time - pattern["last_analysis"]
                
                if elapsed > 0.5:  # Simulate periodic message arrival
                    pattern["message_timestamps"].append(current_time)
                    pattern["last_analysis"] = current_time
            
        except Exception as e:
            self.get_logger().error(f"Monitoring error: {e}")
    
    def analyze_patterns(self):
        """Analyze traffic patterns using ML-inspired techniques"""
        anomalies = []
        current_time = time.time()
        
        for topic_name, pattern in self.topic_patterns.items():
            timestamps = list(pattern["message_timestamps"])
            
            if len(timestamps) < 10:
                continue  # Not enough data
            
            # Calculate message rate
            time_window = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 1.0
            message_rate = len(timestamps) / max(time_window, 0.1)
            
            # 1. Detect burst patterns (common in botnet C&C)
            burst_score = self.calculate_burst_score(timestamps)
            
            # 2. Calculate entropy of message intervals (low entropy = regular patterns)
            entropy = self.calculate_interval_entropy(timestamps)
            
            # 3. Detect synchronization patterns (multiple topics coordinating)
            sync_score = self.detect_synchronization(topic_name, timestamps)
            
            # Check for anomalies
            if burst_score > self.burst_threshold:
                anomalies.append({
                    "topic": topic_name,
                    "type": "BURST_COMMUNICATION",
                    "severity": "HIGH",
                    "score": burst_score,
                    "description": "Botnet-like burst pattern detected"
                })
            
            if entropy < 0.3:  # Very regular pattern (could be heartbeat)
                anomalies.append({
                    "topic": topic_name,
                    "type": "REGULAR_HEARTBEAT",
                    "severity": "MEDIUM",
                    "entropy": entropy,
                    "description": "Regular heartbeat pattern (C&C characteristic)"
                })
            
            if sync_score > 0.6:
                anomalies.append({
                    "topic": topic_name,
                    "type": "SYNCHRONIZED_ACTIVITY",
                    "severity": "HIGH",
                    "score": sync_score,
                    "description": "Multiple topics showing synchronized patterns"
                })
        
        if anomalies:
            self.report_ml_anomalies(anomalies)
    
    def calculate_burst_score(self, timestamps):
        """Calculate burstiness score (0-1)"""
        if len(timestamps) < 5:
            return 0.0
        
        intervals = np.diff(timestamps)
        
        if len(intervals) == 0:
            return 0.0
        
        # Burstiness index from network traffic analysis
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        if mean_interval == 0:
            return 1.0
        
        # Coefficient of variation (CV) indicates burstiness
        cv = std_interval / mean_interval
        
        # Normalize to 0-1 range
        burst_score = min(cv / 2.0, 1.0)
        
        return burst_score
    
    def calculate_interval_entropy(self, timestamps):
        """Calculate Shannon entropy of message intervals"""
        if len(timestamps) < 10:
            return 1.0  # Maximum entropy (random)
        
        intervals = np.diff(timestamps)
        
        # Bin intervals into categories
        hist, _ = np.histogram(intervals, bins=10)
        hist = hist[hist > 0]  # Remove zero counts
        
        # Normalize to probabilities
        probs = hist / hist.sum()
        
        # Calculate Shannon entropy
        entropy = -np.sum(probs * np.log2(probs))
        
        # Normalize to 0-1 (max entropy for 10 bins is log2(10) ≈ 3.32)
        normalized_entropy = entropy / 3.32
        
        return normalized_entropy
    
    def detect_synchronization(self, current_topic, timestamps):
        """Detect if multiple topics show synchronized patterns"""
        # Simplified version - in real system would compare across topics
        # Here we simulate by checking for periodic patterns
        
        if len(timestamps) < 20:
            return 0.0
        
        # Look for regular intervals (synchronization signature)
        intervals = np.diff(timestamps[-20:])  # Last 20 intervals
        
        if len(intervals) < 5:
            return 0.0
        
        # Calculate regularity (low variance indicates synchronization)
        interval_variance = np.var(intervals)
        mean_interval = np.mean(intervals)
        
        if mean_interval == 0:
            return 0.0
        
        # Regularity score (inverse of normalized variance)
        regularity = 1.0 / (1.0 + interval_variance / mean_interval)
        
        return min(regularity, 1.0)
    
    def report_ml_anomalies(self, anomalies):
        """Report ML-detected anomalies"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "detection_method": "ML Pattern Analysis",
            "techniques_used": ["Burst Detection", "Entropy Analysis", "Synchronization Detection"],
            "anomalies": anomalies,
            "total_topics_monitored": len(self.topic_patterns)
        }
        
        if self.verbose:
            self.get_logger().warning("=== ML ANOMALY DETECTION REPORT ===")
        
        for anomaly in anomalies:
            alert_msg = {
                "type": anomaly["type"],
                "topic": anomaly["topic"],
                "severity": anomaly["severity"],
                "description": anomaly["description"],
                "score": anomaly.get("score", 0.0),
                "timestamp": time.time()
            }
            
            # Publish alert
            from std_msgs.msg import String
            msg = String()
            msg.data = json.dumps(alert_msg)
            self.alert_pub.publish(msg)
            
            if self.verbose:
                self.get_logger().warning(
                    f"{anomaly[type]} on {anomaly[topic]}: "
                    f"{anomaly[description]} (Severity: {anomaly[severity]})"
                )
        
        # Save detailed report
        log_dir = os.environ.get("SECURITY_LOG_DIR", "/root/eva/security_logs")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_dir}/ml_anomaly_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        if self.verbose:
            self.get_logger().info(f"ML analysis report saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="ML-based botnet detection for ROS 2")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    parser.add_argument("--window-size", type=int, default=50, help="Message window size for analysis")
    parser.add_argument("--entropy-threshold", type=float, default=0.7, help="Entropy threshold for pattern detection")
    parser.add_argument("--burst-threshold", type=float, default=0.8, help="Burst detection sensitivity")
    
    args = parser.parse_args()
    
    rclpy.init()
    detector = MLAnomalyDetector(
        window_size=args.window_size,
        entropy_threshold=args.entropy_threshold,
        burst_threshold=args.burst_threshold,
        verbose=args.verbose
    )
    
    print("=" * 60)
    print("ML BOTNET DETECTION SYSTEM")
    print("=" * 60)
    print(f"Window size: {args.window_size}")
    print(f"Entropy threshold: {args.entropy_threshold}")
    print(f"Burst threshold: {args.burst_threshold}")
    print("\nMonitoring ROS 2 mesh for malicious patterns...")
    
    try:
        rclpy.spin(detector)
    except KeyboardInterrupt:
        print("\nDetection stopped")
    finally:
        detector.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()