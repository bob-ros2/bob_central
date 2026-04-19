#!/usr/bin/env python3
"""
Test script for BobSynth alarm synthesis system
Generates test alerts to verify audio output
"""

import rclpy
from rclpy.node import Node
import json
import time
from std_msgs.msg import String

class AlarmTester(Node):
    def __init__(self):
        super().__init__('alarm_tester')
        
        # Publisher for alert topics
        self.alert_pub = self.create_publisher(String, '/eva/security/alerts', 10)
        self.ml_alert_pub = self.create_publisher(String, '/eva/security/ml_alerts', 10)
        
        self.get_logger().info('Alarm tester initialized')
    
    def send_test_alert(self, severity='MEDIUM', alert_type='TEST'):
        """Send a test alert"""
        alert = {
            'type': alert_type,
            'severity': severity,
            'description': f'Test {severity} alert',
            'timestamp': time.time(),
            'source': 'tester'
        }
        
        msg = String()
        msg.data = json.dumps(alert)
        
        self.alert_pub.publish(msg)
        self.get_logger().info(f'Sent {severity} test alert')
        
        return alert
    
    def send_ml_alert(self, severity='HIGH', confidence=0.85):
        """Send ML-based anomaly alert"""
        ml_alert = {
            'type': 'ML_ANOMALY',
            'severity': severity,
            'confidence': confidence,
            'pattern': 'burst_detection',
            'description': 'ML detected anomalous traffic pattern',
            'timestamp': time.time()
        }
        
        msg = String()
        msg.data = json.dumps(ml_alert)
        
        self.ml_alert_pub.publish(msg)
        self.get_logger().info(f'Sent ML {severity} alert (confidence: {confidence})')


def main():
    rclpy.init()
    tester = AlarmTester()
    
    print('\n' + '=' * 60)
    print('BOB_SYNTH ALARM TESTER')
    print('=' * 60)
    print('This will send test alerts to verify the alarm synthesis system.')
    print('Make sure alarm_synthesis_v2.py is running first!')
    print('\nPress Ctrl+C to stop...')
    
    try:
        # Wait a moment for subscribers to connect
        time.sleep(2)
        
        # Test sequence
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for severity in severities:
            print(f'\nTesting {severity} alert...')
            tester.send_test_alert(severity, f'{severity}_TEST')
            time.sleep(3)  # Wait for pattern to complete
        
        # Test ML alert
        print('\nTesting ML anomaly alert...')
        tester.send_ml_alert('HIGH', 0.92)
        time.sleep(3)
        
        print('\nTest sequence complete!')
        
        # Keep node alive
        rclpy.spin(tester)
        
    except KeyboardInterrupt:
        print('\nTest stopped by user')
    finally:
        tester.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()