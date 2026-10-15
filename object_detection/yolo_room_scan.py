#!/usr/bin/env python3
"""
YOLO-based room scan: rotates the robot 360 degrees while running a
fine-tuned YOLO model on the camera stream, then reports which objects
were found. Drop-in alternative to the HSV-based room_scan.py.

Run (after Nav2 has brought the robot to a room):
    python3 yolo_room_scan.py
"""
import math
import time

import cv2
import rclpy
from cv_bridge import CvBridge
import os

from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import Image
from ultralytics import YOLO

# best.pt is looked for next to this script, so it works from any folder
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pt")
IMAGE_TOPIC = "/camera/image_raw"
CMD_VEL_TOPIC = "/cmd_vel"      # TurtleBot3 on Jazzy uses TwistStamped here
CONFIDENCE = 0.5
ANGULAR_SPEED = 0.4             # rad/s
SCAN_TIME = 2 * math.pi / ANGULAR_SPEED  # time for one full rotation


class YoloRoomScan(Node):
    def __init__(self):
        super().__init__("yolo_room_scan")
        self.model = YOLO(MODEL_PATH)
        self.bridge = CvBridge()
        self.found = {}  # class name -> best confidence
        self.cmd_pub = self.create_publisher(TwistStamped, CMD_VEL_TOPIC, 10)
        self.create_subscription(Image, IMAGE_TOPIC, self.image_callback, 10)
        self.start = time.time()
        self.create_timer(0.1, self.rotate)
        self.done = False
        self.get_logger().info("Starting 360-degree YOLO scan...")

    def make_cmd(self, angular_z=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"
        cmd.twist.angular.z = angular_z
        return cmd

    def rotate(self):
        if self.done:
            return
        if time.time() - self.start < SCAN_TIME:
            self.cmd_pub.publish(self.make_cmd(ANGULAR_SPEED))
        else:
            self.cmd_pub.publish(self.make_cmd(0.0))  # stop
            self.done = True
            self.report()

    def image_callback(self, msg):
        if self.done:
            return
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        results = self.model(frame, conf=CONFIDENCE, verbose=False)[0]

        for box in results.boxes:
            name = self.model.names[int(box.cls)]
            conf = float(box.conf)
            self.found[name] = max(conf, self.found.get(name, 0.0))
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("YOLO room scan", frame)
        cv2.waitKey(1)

    def report(self):
        if self.found:
            for name, conf in self.found.items():
                self.get_logger().info(f"Found: {name} (confidence {conf:.2f})")
        else:
            self.get_logger().info("No objects detected in this room.")


def main():
    rclpy.init()
    node = YoloRoomScan()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    node.cmd_pub.publish(node.make_cmd(0.0))  # make sure the robot stops
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
