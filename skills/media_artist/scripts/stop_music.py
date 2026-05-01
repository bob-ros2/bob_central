#!/usr/bin/env python3
"""Stop music by sending clear request to music daemon."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json, time

rclpy.init()
node = Node('stop_music_client')
from rclpy.qos import QoSProfile, DurabilityPolicy
qos = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)
pub = node.create_publisher(String, '/eva/media/play_request', qos)

start_wait = time.time()
while node.count_subscribers(pub.topic_name) == 0 and (time.time() - start_wait) < 3.0:
    rclpy.spin_once(node, timeout_sec=0.1)

request = {'files': [], 'loop': False, 'loop_all': False, 'enqueue': False}
pub.publish(String(data=json.dumps(request)))
print("Stop request sent to music daemon", flush=True)
