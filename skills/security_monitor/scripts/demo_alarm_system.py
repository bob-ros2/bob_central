#!/usr/bin/env python3
"""
Demonstration of Autonomous Alarm Synthesis System
Shows complete integration with bob_synth for IDS alerts
"""

import rclpy
from rclpy.node import Node
import json
import time
from std_msgs.msg import String

class AlarmSystemDemo(Node):
    def __init__(self):
        super().__init__('alarm_system_demo')
        
        # Publisher for alert topics
        self.alert_pub = self.create_publisher(String, '/eva/security/alerts', 10)
        
        self.get_logger().info('Alarm system demo initialized')
    
    def demonstrate_severity_levels(self):
        """Demonstrate all severity levels"""
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        print('\n' + '=' * 60)
        print('DEMONSTRATING ALARM SYNTHESIS SYSTEM')
        print('=' * 60)
        print('This will generate audio alerts for each severity level.')
        print('Make sure alarm_synthesis_v2_fixed.py is running!')
        print('\nStarting demonstration in 3 seconds...')
        time.sleep(3)
        
        for severity in severities:
            print(f'\n--- {severity} ALERT ---')
            
            alert = {
                'type': f'{severity}_DEMO',
                'severity': severity,
                'description': f'Demonstration of {severity.lower()} severity alert',
                'timestamp': time.time(),
                'source': 'demo'
            }
            
            msg = String()
            msg.data = json.dumps(alert)
            self.alert_pub.publish(msg)
            
            print(f'Sent {severity} alert to synthesis system')
            print(f'Expected: {self.get_expected_pattern(severity)}')
            
            # Wait for pattern to complete
            wait_time = self.get_pattern_duration(severity)
            print(f'Waiting {wait_time:.1f} seconds for pattern...')
            time.sleep(wait_time + 1)  # Extra second for safety
        
        print('\n' + '=' * 60)
        print('DEMONSTRATION COMPLETE')
        print('=' * 60)
        print('The autonomous alarm synthesis system is now operational.')
        print('It will automatically generate audio warnings for any IDS alerts.')
        print('\nAlert topics monitored:')
        print('- /eva/security/alerts')
        print('- /eva/security/ml_alerts')
    
    def get_expected_pattern(self, severity):
        """Return expected pattern description"""
        patterns = {
            'LOW': 'Two beeps (440Hz sine wave)',
            'MEDIUM': 'Four beeps (880Hz square wave)', 
            'HIGH': 'Six beeps (1760Hz sawtooth)',
            'CRITICAL': 'Eight beeps (3520Hz square wave)'
        }
        return patterns.get(severity, 'Unknown pattern')
    
    def get_pattern_duration(self, severity):
        """Calculate total pattern duration"""
        base_durations = {
            'LOW': 0.5,
            'MEDIUM': 0.3,
            'HIGH': 0.2,
            'CRITICAL': 0.1
        }
        
        pattern_lengths = {
            'LOW': 4,
            'MEDIUM': 6,
            'HIGH': 8,
            'CRITICAL': 10
        }
        
        duration = base_durations.get(severity, 0.3)
        length = pattern_lengths.get(severity, 4)
        
        # Each pattern element has duration + 0.05s pause
        return length * (duration + 0.05)


def main():
    rclpy.init()
    demo = AlarmSystemDemo()
    
    try:
        demo.demonstrate_severity_levels()
        
        # Keep node alive briefly
        time.sleep(2)
        
    except KeyboardInterrupt:
        print('\nDemo stopped by user')
    finally:
        demo.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()