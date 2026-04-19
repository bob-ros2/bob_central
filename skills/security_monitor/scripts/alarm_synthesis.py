#!/usr/bin/env python3
"""
Autonomous Alarm Synthesis System for IDS Alerts
Generates warning tones using synthetic audio techniques
"""

import rclpy
from rclpy.node import Node
import numpy as np
import wave
import tempfile
import os
import threading
import time
from datetime import datetime
import json
import argparse

class AlarmSynthesizer(Node):
    """Generates warning tones for IDS alerts"""
    
    def __init__(self, volume_scale=1.0, test_tone=False, verbose=False):
        super().__init__("alarm_synthesizer")
        
        self.volume_scale = volume_scale
        self.verbose = verbose
        
        # Alert severity levels and corresponding audio patterns
        self.severity_patterns = {
            "LOW": {
                "frequency": 440,  # A4
                "duration": 0.5,
                "pattern": [1, 0, 1, 0],  # Beep pattern
                "volume": 0.3 * volume_scale
            },
            "MEDIUM": {
                "frequency": 880,  # A5  
                "duration": 0.3,
                "pattern": [1, 1, 0, 1, 1, 0],
                "volume": 0.5 * volume_scale
            },
            "HIGH": {
                "frequency": 1760,  # A6
                "duration": 0.2,
                "pattern": [1, 1, 1, 0, 1, 1, 1, 0],
                "volume": 0.7 * volume_scale
            },
            "CRITICAL": {
                "frequency": 3520,  # A7
                "duration": 0.1,
                "pattern": [1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
                "volume": 0.9 * volume_scale
            }
        }
        
        # Audio parameters
        self.sample_rate = 44100
        self.bit_depth = 16
        
        # Alert queue
        self.alert_queue = []
        self.queue_lock = threading.Lock()
        
        # Start alert processor thread
        self.processor_thread = threading.Thread(target=self.process_alerts)
        self.processor_thread.daemon = True
        self.processor_thread.start()
        
        # Subscribe to anomaly alerts
        from std_msgs.msg import String
        self.create_subscription(
            String,
            "/eva/security/alerts",
            self.alert_callback,
            10
        )
        
        if test_tone:
            self.generate_test_tone()
        
        if self.verbose:
            self.get_logger().info(f"Alarm synthesis system initialized (volume_scale={volume_scale})")
            self.get_logger().info(f"Severity patterns: {list(self.severity_patterns.keys())}")
        else:
            self.get_logger().info("Alarm synthesis active")
    
    def generate_test_tone(self):
        """Generate a test tone on startup"""
        test_alert = {
            "type": "TEST_TONE",
            "severity": "MEDIUM",
            "description": "System test tone",
            "timestamp": time.time()
        }
        
        with self.queue_lock:
            self.alert_queue.append(test_alert)
        
        self.get_logger().info("Test tone queued")
    
    def alert_callback(self, msg):
        """Receive security alerts and queue them for audio synthesis"""
        try:
            alert = json.loads(msg.data)
            
            with self.queue_lock:
                self.alert_queue.append(alert)
                
            if self.verbose:
                self.get_logger().info(f"Alert received: {alert.get(severity, UNKNOWN)} - {alert.get(type, Unknown)}")
            
        except Exception as e:
            self.get_logger().error(f"Error parsing alert: {e}")
    
    def process_alerts(self):
        """Process queued alerts and generate audio warnings"""
        while rclpy.ok():
            with self.queue_lock:
                if self.alert_queue:
                    alert = self.alert_queue.pop(0)
                else:
                    alert = None
            
            if alert:
                severity = alert.get("severity", "MEDIUM")
                alert_type = alert.get("type", "Unknown")
                
                # Generate appropriate warning tone
                audio_file = self.generate_warning_tone(severity, alert_type)
                
                if audio_file:
                    self.play_audio(audio_file)
                    
                    # Log the alert
                    self.log_alert(alert, audio_file)
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning
    
    def generate_warning_tone(self, severity, alert_type):
        """Generate WAV file with warning tone pattern"""
        if severity not in self.severity_patterns:
            severity = "MEDIUM"
        
        pattern_config = self.severity_patterns[severity]
        
        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()
        
        try:
            # Generate tone pattern
            samples = self.generate_tone_pattern(
                pattern_config["frequency"],
                pattern_config["duration"],
                pattern_config["pattern"],
                pattern_config["volume"]
            )
            
            # Write WAV file
            self.write_wav(temp_file.name, samples)
            
            if self.verbose:
                self.get_logger().info(f"Generated {severity} alert tone: {alert_type}")
            return temp_file.name
            
        except Exception as e:
            self.get_logger().error(f"Error generating tone: {e}")
            return None
    
    def generate_tone_pattern(self, frequency, duration, pattern, volume):
        """Generate audio samples for tone pattern"""
        total_samples = int(self.sample_rate * duration * len(pattern))
        samples = np.zeros(total_samples)
        
        for i, pattern_bit in enumerate(pattern):
            if pattern_bit:  # 1 = tone on
                start_sample = int(i * duration * self.sample_rate)
                end_sample = int((i + 1) * duration * self.sample_rate)
                
                # Generate sine wave for this segment
                t = np.linspace(0, duration, end_sample - start_sample)
                tone = np.sin(2 * np.pi * frequency * t)
                
                # Apply volume and fade in/out
                fade_samples = int(0.05 * self.sample_rate)  # 50ms fade
                if fade_samples > 0:
                    fade_in = np.linspace(0, 1, fade_samples)
                    fade_out = np.linspace(1, 0, fade_samples)
                    
                    if len(tone) > 2 * fade_samples:
                        tone[:fade_samples] *= fade_in
                        tone[-fade_samples:] *= fade_out
                
                samples[start_sample:end_sample] = tone * volume
        
        # Convert to 16-bit PCM
        samples = np.int16(samples * 32767)
        
        return samples
    
    def write_wav(self, filename, samples):
        """Write samples to WAV file"""
        with wave.open(filename, w) as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)   # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(samples.tobytes())
    
    def play_audio(self, audio_file):
        """Play audio file using available audio system"""
        try:
            output_device = os.environ.get("AUDIO_OUTPUT_DEVICE", "")
            device_arg = f"-D {output_device}" if output_device else ""
            
            # Try different audio playback methods
            if os.path.exists("/usr/bin/aplay"):
                os.system(f"aplay {device_arg} {audio_file} &")
            elif os.path.exists("/usr/bin/paplay"):
                os.system(f"paplay {audio_file} &")
            else:
                # Fallback: use Python sounddevice if available
                try:
                    import sounddevice as sd
                    import soundfile as sf
                    
                    data, fs = sf.read(audio_file)
                    sd.play(data, fs)
                    sd.wait()
                except ImportError:
                    self.get_logger().warning("No audio playback method available")
            
            # Clean up temp file after playback
            threading.Timer(5.0, lambda: os.unlink(audio_file)).start()
            
        except Exception as e:
            self.get_logger().error(f"Error playing audio: {e}")
    
    def log_alert(self, alert, audio_file):
        """Log alert to file for audit trail"""
        log_dir = os.environ.get("SECURITY_LOG_DIR", "/root/eva/security_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "alert": alert,
            "audio_generated": audio_file,
            "system": "AlarmSynthesis"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"alarm_{timestamp}.json")
        
        try:
            with open(log_file, "w") as f:
                json.dump(log_entry, f, indent=2)
        except Exception as e:
            self.get_logger().error(f"Error logging alert: {e}")


def main():
    parser = argparse.ArgumentParser(description="Alarm synthesis for IDS alerts")
    parser.add_argument("--volume-scale", type=float, default=1.0, help="Global volume multiplier")
    parser.add_argument("--test-tone", action="store_true", help="Generate test tone on startup")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    
    args = parser.parse_args()
    
    rclpy.init()
    synthesizer = AlarmSynthesizer(
        volume_scale=args.volume_scale,
        test_tone=args.test_tone,
        verbose=args.verbose
    )
    
    print("=" * 60)
    print("ALARM SYNTHESIS SYSTEM")
    print("=" * 60)
    print(f"Volume scale: {args.volume_scale}")
    print(f"Test tone: {Yes if args.test_tone else No}")
    print("\nListening for security alerts on /eva/security/alerts...")
    
    try:
        rclpy.spin(synthesizer)
    except KeyboardInterrupt:
        print("\nAlarm synthesis stopped")
    finally:
        synthesizer.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()