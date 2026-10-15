#!/usr/bin/env python3
"""
Capture training images from the TurtleBot3 camera in Gazebo.

Saves one frame every SAVE_INTERVAL seconds to OUTPUT_DIR while you drive
the robot around (teleop) or while it runs your room scan.

Run:
    python3 capture_images.py
Stop with Ctrl+C.
"""
import os
import time

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

IMAGE_TOPIC = "/camera/image_raw"
OUTPUT_DIR = os.path.expanduser("~/yolo_dataset/raw_images")
SAVE_INTERVAL = 1.0  # seconds between saved frames


class ImageCapture(Node):
    def __init__(self):
        super().__init__("image_capture")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.bridge = CvBridge()
        self.last_save = 0.0
        self.count = len(os.listdir(OUTPUT_DIR))  # continue numbering across runs
        self.create_subscription(Image, IMAGE_TOPIC, self.callback, 10)
        self.get_logger().info(f"Saving images to {OUTPUT_DIR}")

    def callback(self, msg):
        now = time.time()
        if now - self.last_save < SAVE_INTERVAL:
            return
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        path = os.path.join(OUTPUT_DIR, f"img_{self.count:04d}.jpg")
        cv2.imwrite(path, frame)
        self.count += 1
        self.last_save = now
        self.get_logger().info(f"Saved {path}")


def main():
    rclpy.init()
    node = ImageCapture()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
