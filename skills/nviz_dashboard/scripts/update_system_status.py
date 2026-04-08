#!/usr/bin/env python3
import json
import os
import subprocess
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def get_system_stats():
    """Gather technical data from the mesh."""
    try:
        # Load
        with open('/proc/loadavg', 'r') as f:
            load = f.read().strip().split()[:3]
        
        # Memory
        mem = subprocess.run(['free', '-m'], capture_output=True, text=True)
        mem_used = mem.stdout.split('\n')[1].split()[2]
        
        # ROS Nodes
        nodes_raw = subprocess.run(['ros2', 'node', 'list'], capture_output=True, text=True)
        node_count = len([n for n in nodes_raw.stdout.strip().split('\n') if n.strip()])
        
        return {
            "load": " / ".join(load),
            "mem": f"{mem_used} MB used",
            "nodes": f"{node_count} active",
            "time": datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        return {"error": str(e)}

def draw_status_board(stats, is_busy=False):
    """Render a professional system board graphic."""
    width, height = 400, 150
    img = Image.new('RGB', (width, height), color=(5, 5, 20)) # Dark Space Blue
    draw = ImageDraw.Draw(img)
    
    # Try fonts
    try:
        font_main = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 14)
        font_bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 16)
    except:
        font_main = ImageFont.load_default()
        font_bold = font_main

    # Draw Status LED (Top Rightish)
    led_color = (255, 50, 50) if is_busy else (50, 255, 50) # Red if busy, Green if ready
    draw.ellipse([350, 15, 375, 40], fill=led_color, outline=(255, 255, 255))
    status_text = "BUSY / REASONING" if is_busy else "READY / IDLE"
    draw.text((220, 20), status_text, fill=led_color, font=font_bold)

    # Draw Stats
    y = 15
    draw.text((15, y), "EVA BRAIN-MESH STATUS", fill=(0, 200, 255), font=font_bold)
    
    y += 35
    draw.text((15, y), f"LOAD:  {stats.get('load', 'N/A')}", fill=(200, 200, 200), font=font_main)
    y += 20
    draw.text((15, y), f"MEM:   {stats.get('mem', 'N/A')}", fill=(200, 200, 200), font=font_main)
    y += 20
    draw.text((15, y), f"NODES: {stats.get('nodes', 'N/A')}", fill=(200, 200, 200), font=font_main)
    
    y += 25
    draw.text((15, y), f"Last Sync: {stats.get('time', 'N/A')}", fill=(100, 100, 150), font=font_main)
    
    # Border
    draw.rectangle([0, 0, width-1, height-1], outline=(0, 100, 200))
    
    return img

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--busy', action='store_true', help='Set status to BUSY')
    parser.add_argument('--output', default='/tmp/eva_system_board.png', help='Output path')
    args = parser.parse_args()

    stats = get_system_stats()
    img = draw_status_board(stats, is_busy=args.busy)
    img.save(args.output)
    
    # Display it on ID 'system_monitor'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    display_script = os.path.join(script_dir, "display_image.py")
    
    subprocess.run([
        "python3", display_script, 
        "--path", args.output, 
        "--id", "system_monitor", 
        "--area", "426", "20", "400", "150",
        "--pipe", "/tmp/monitor_pipe"
    ])

if __name__ == "__main__":
    main()
