#!/usr/bin/env python3
"""
Autonomous Alarm Synthesis System for IDS Alerts - Version 2
Uses bob_synth for high-quality audio generation and directs output to Mixer Channel i
"""

import rclpy
from rclpy.node import Node
import numpy as np
import json
import argparse
import time
import threading
from datetime import datetime
from std_msgs.msg import String

class BobSynthAlarmSynthesizer(Node):
    """Generates warning tones using bob_synth synthesizer node"""
    
    def __init__(self, volume_scale=1.0, test_tone=False, verbose=False, mixer_channel='i'):
        super().__init__('bob_synth_alarm_synthesizer')
        
        self.volume_scale = volume_scale
        self.verbose = verbose
        self.mixer_channel = mixer_channel
        
        # Alert severity levels with bob_synth parameters
        self.severity_configs = {
            'LOW': {
                'frequency': 440.0,      # A4
                'waveform': 'sine',
                'amplitude': 0.3 * volume_scale,
                'filter_cutoff': 2000.0,
                'filter_resonance': 0.3,
                'attack': 0.05,
                'decay': 0.1,
                'sustain': 0.7,
                'release': 0.3,
                'pattern': [1, 0, 1, 0],
                'duration': 0.5
            },
            'MEDIUM': {
                'frequency': 880.0,      # A5
                'waveform': 'square',
                'amplitude': 0.5 * volume_scale,
                'filter_cutoff': 1500.0,
                'filter_resonance': 0.5,
                'attack': 0.02,
                'decay': 0.08,
                'sustain': 0.8,
                'release': 0.2,
                'pattern': [1, 1, 0, 1, 1, 0],
                'duration': 0.3
            },
            'HIGH': {
                'frequency': 1760.0,     # A6
                'waveform': 'sawtooth',
                'amplitude': 0.7 * volume_scale,
                'filter_cutoff': 1000.0,
                'filter_resonance': 0.7,
                'attack': 0.01,
                'decay': 0.05,
                'sustain': 0.9,
                'release': 0.15,
                'pattern': [1, 1, 1, 0, 1, 1, 1, 0],
                'duration': 0.2
            },
            'CRITICAL': {
                'frequency': 3520.0,     # A7
                'waveform': 'square',
                'amplitude': 0.9 * volume_scale,
                'filter_cutoff': 500.0,
                'filter_resonance': 0.9,
                'attack': 0.005,
                'decay': 0.03,
                'sustain': 1.0,
                'release': 0.1,
                'pattern': [1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
                'duration': 0.1
            }
        }
        
        # Publisher for bob_synth control
        self.synth_pub = self.create_publisher(
            String,
            '/synth_config',
            10
        )
        
        # Alert queue
        self.alert_queue = []
        self.queue_lock = threading.Lock()
        
        # Active alert tracking
        self.active_alert = None
        self.alert_thread = None
        
        # Subscribe to security alerts
        self.create_subscription(
            String,
            '/eva/security/alerts',
            self.alert_callback,
            10
        )
        
        # Also subscribe to ML-based alerts
        self.create_subscription(
            String,
            '/eva/security/ml_alerts',
            self.alert_callback,
            10
        )
        
        if test_tone:
            self.generate_test_tone()
        
        # Start alert processor thread
        self.processor_thread = threading.Thread(target=self.process_alerts)
        self.processor_thread.daemon = True
        self.processor_thread.start()
        
        self.get_logger().info(f'BobSynth alarm synthesis initialized (mixer_channel={mixer_channel})')
        
    def generate_test_tone(self):
        """Generate a test tone on startup"""
        test_alert = {
            'type': 'SYSTEM_TEST',
            'severity': 'MEDIUM',
            'description': 'BobSynth alarm system test',
            'timestamp': time.time()
        }
        
        with self.queue_lock:
            self.alert_queue.append(test_alert)
        
        self.get_logger().info('Test tone queued')
    
    def alert_callback(self, msg):
        """Receive security alerts and queue them for audio synthesis"""
        try:
            alert = json.loads(msg.data)
            
            with self.queue_lock:
                self.alert_queue.append(alert)
                
            if self.verbose:
                self.get_logger().info(f'Alert received: {alert.get("severity", "UNKNOWN")} - {alert.get("type", "Unknown")}')
            
        except Exception as e:
            self.get_logger().error(f'Error parsing alert: {e}')
    
    def process_alerts(self):
        """Process queued alerts and generate audio warnings"""
        while rclpy.ok():
            with self.queue_lock:
                if self.alert_queue:
                    alert = self.alert_queue.pop(0)
                else:
                    alert = None
            
            if alert:
                severity = alert.get('severity', 'MEDIUM')
                alert_type = alert.get('type', 'Unknown')
                
                # Stop any currently playing alert
                self.stop_current_alert()
                
                # Generate new alert pattern
                self.play_alert_pattern(severity, alert_type, alert)
                
                # Log the alert
                self.log_alert(alert)
            
            time.sleep(0.1)
    
    def play_alert_pattern(self, severity, alert_type, alert_data):
        """Play alert pattern using bob_synth"""
        if severity not in self.severity_configs:
            severity = 'MEDIUM'
        
        config = self.severity_configs[severity]
        
        # Create alert thread
        self.active_alert = {
            'severity': severity,
            'config': config,
            'running': True
        }
        
        self.alert_thread = threading.Thread(
            target=self._play_pattern_thread,
            args=(config, alert_type)
        )
        self.alert_thread.daemon = True
        self.alert_thread.start()
        
        if self.verbose:
            self.get_logger().info(f'Playing {severity} alert: {alert_type}')
    
    def _play_pattern_thread(self, config, alert_type):
        """Thread function to play the alert pattern"""
        pattern = config['pattern']
        duration = config['duration']
        
        for i, pattern_bit in enumerate(pattern):
            if not self.active_alert or not self.active_alert['running']:
                break
            
            if pattern_bit:  # 1 = note on
                # Send note_on command with configuration
                synth_msg = {
                    'note_on': True,
                    'frequency': config['frequency'],
                    'waveform': config['waveform'],
                    'amplitude': config['amplitude'],
                    'filter_cutoff': config['filter_cutoff'],
                    'filter_resonance': config['filter_resonance'],
                    'attack': config['attack'],
                    'decay': config['decay'],
                    'sustain': config['sustain'],
                    'release': config['release']
                }
                
                # Add mixer channel routing if specified
                if self.mixer_channel:
                    synth_msg['mixer_channel'] = self.mixer_channel
                
                self.send_synth_command(synth_msg)
            
            # Wait for note duration
            time.sleep(duration)
            
            if pattern_bit:  # Turn off note after duration
                self.send_synth_command({'note_on': False})
            
            # Small pause between pattern elements
            time.sleep(0.05)
        
        # Clean up
        if self.active_alert:
            self.active_alert['running'] = False
    
    def send_synth_command(self, params):
        """Send JSON command to bob_synth"""
        try:
            msg = String()
            msg.data = json.dumps(params)
            self.synth_pub.publish(msg)
            
            if self.verbose:
                self.get_logger().debug(f'Sent synth command: {params}')
                
        except Exception as e:
            self.get_logger().error(f'Error sending synth command: {e}')
    
    def stop_current_alert(self):
        """Stop any currently playing alert"""
        if self.active_alert and self.active_alert['running']:
            self.active_alert['running'] = False
            
            # Send note_off command
            self.send_synth_command({'note_on': False})
            
            # Wait for thread to finish
            if self.alert_thread and self.alert_thread.is_alive():
                self.alert_thread.join(timeout=1.0)
            
            self.active_alert = None
            self.alert_thread = None
    
    def log_alert(self, alert):
        """Log alert to file for audit trail"""
        import os
        
        log_dir = os.environ.get('SECURITY_LOG_DIR', '/root/eva/security_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'alert': alert,
            'synthesizer': 'BobSynth',
            'mixer_channel': self.mixer_channel,
            'system': 'AlarmSynthesisV2'
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'alarm_bobsynth_{timestamp}.json')
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)
        except Exception as e:
            self.get_logger().error(f'Error logging alert: {e}')


def main():
    parser = argparse.ArgumentParser(description='BobSynth alarm synthesis for IDS alerts')
    parser.add_argument('--volume-scale', type=float, default=1.0, help='Global volume multiplier')
    parser.add_argument('--test-tone', action='store_true', help='Generate test tone on startup')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logging')
    parser.add_argument('--mixer-channel', type=str, default='i', help='Mixer channel for audio output')
    
    args = parser.parse_args()
    
    rclpy.init()
    synthesizer = BobSynthAlarmSynthesizer(
        volume_scale=args.volume_scale,
        test_tone=args.test_tone,
        verbose=args.verbose,
        mixer_channel=args.mixer_channel
    )
    
    print('=' * 60)
    print('BOB_SYNTH ALARM SYNTHESIS SYSTEM')
    print('=' * 60)
    print(f'Volume scale: {args.volume_scale}')
    print(f'Mixer channel: {args.mixer_channel}')
    print(f'Test tone: {"Yes" if args.test_tone else "No"}')
    print('\nListening for security alerts...')
    print('- /eva/security/alerts')
    print('- /eva/security/ml_alerts')
    
    try:
        rclpy.spin(synthesizer)
    except KeyboardInterrupt:
        print('\nAlarm synthesis stopped')
    finally:
        synthesizer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()