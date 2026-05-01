#!/usr/bin/env python3
import logging
import threading
import time

# Attempt to configure rclpy (ROS2) safely gracefully degrading to fallback
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False


class SentenceBufferNode(Node if ROS_AVAILABLE else object):
    """
    A smart buffer that collects Whisper fragments, holds them for a configurable timeout
    (to see if more speech is following), and evaluates them to try and form complete queries
    before flushing them to Eva's topic.
    """

    def __init__(self, publish_topic="/eva/user_query", buffer_timeout=3.0, **kwargs):
        if ROS_AVAILABLE:
            if not rclpy.ok():
                rclpy.init(args=None)
            super().__init__("vox_smart_buffer")
            self.publisher = self.create_publisher(String, publish_topic, 10)
        else:
            self.publisher = None
            logging.error("rclpy not found. OutputHandler running in debug mode.")

        self.buffer = []
        self.buffer_timeout = buffer_timeout
        self.last_update_time = time.time()
        self.lock = threading.Lock()
        
        # Start a background watchdog thread
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()

    def add_fragment(self, text):
        """Called by the main Handler when a new phrase arrives."""
        text = text.strip()
        if not text:
            return

        with self.lock:
            self.buffer.append(text)
            self.last_update_time = time.time()

    def _flush_buffer(self):
        """Combines snippets and publishes them, then clears the buffer."""
        with self.lock:
            if not self.buffer:
                return

            # Very simple combination strategy
            combined_text = " ".join(self.buffer).strip()
            self.buffer.clear()

        # Send it to ROS
        if combined_text:
            logging.info(f"BUFFER FLUSH: '{combined_text}'")
            if ROS_AVAILABLE and self.publisher:
                msg = String()
                msg.data = combined_text
                self.publisher.publish(msg)
                
                # We also need to keep spinning ROS 1 step so callbacks/publishings happen
                rclpy.spin_once(self, timeout_sec=0.01)

    def _watchdog_loop(self):
        """Continuously checks if the buffer needs flushing."""
        while True:
            time.sleep(0.5)
            with self.lock:
                needs_flush = False
                if self.buffer and (time.time() - self.last_update_time) >= self.buffer_timeout:
                    needs_flush = True
                
            if needs_flush:
                self._flush_buffer()

    def close(self):
        """Shut down cleanly."""
        self._flush_buffer()
        if ROS_AVAILABLE and getattr(self, "destroy_node", None):
            self.destroy_node()
        if ROS_AVAILABLE and rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


class OutputHandler:
    """
    Standard Vox custom plugin class.
    Vox reads this and uses `send(text)`.
    """

    def __init__(self, **kwargs):
        logging.info("Initializing Vox Smart Buffer Handler...")
        # Customize the buffer delay (how long to wait after silence to consider phrase complete).
        self.buffer_node = SentenceBufferNode(
            publish_topic="/eva/user_query",
            buffer_timeout=2.5  # 2.5 seconds timeout
        )

    def send(self, text):
        logging.debug(f">> Vox caught fragment: {text}")
        self.buffer_node.add_fragment(text)

    def close(self):
        logging.info("Closing Vox Smart Buffer Handler...")
        self.buffer_node.close()
