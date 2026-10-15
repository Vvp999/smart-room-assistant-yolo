#!/usr/bin/env python3
"""
Launch your house world with a TurtleBot3 BURGER that has a camera.

Needs the model made by make_burger_cam.py
(~/my_models/turtlebot3_burger_cam/model.sdf).

Run:
    export TURTLEBOT3_MODEL=burger
    ros2 launch ~/smart-room-assistant-ros2/launch/house_project_burger.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WORLD = os.path.expanduser("~/my_worlds/house_project.world")
BURGER_CAM_SDF = os.path.expanduser("~/my_models/turtlebot3_burger_cam/model.sdf")


def generate_launch_description():
    tb3_gazebo = get_package_share_directory("turtlebot3_gazebo")
    tb3_launch_dir = os.path.join(tb3_gazebo, "launch")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    x_pose = LaunchConfiguration("x_pose", default="-2.0")
    y_pose = LaunchConfiguration("y_pose", default="-0.5")

    # Lets Gazebo find the house and the burger meshes
    set_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(tb3_gazebo, "models")
    )

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": ["-r -s -v2 ", WORLD], "on_exit_shutdown": "true"}.items(),
    )

    gz_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": "-g -v2 ", "on_exit_shutdown": "true"}.items(),
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3_launch_dir, "robot_state_publisher.launch.py")),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # Spawn our burger-with-camera model
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "burger",
            "-file", BURGER_CAM_SDF,
            "-x", x_pose,
            "-y", y_pose,
            "-z", "0.01",
        ],
        output="screen",
    )

    # Normal burger bridge: cmd_vel, odom, scan, imu, tf, joint_states, clock
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{
            "config_file": os.path.join(tb3_gazebo, "params", "turtlebot3_burger_bridge.yaml"),
        }],
        output="screen",
    )

    # Camera bridge (the stock burger launch leaves this out)
    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )

    return LaunchDescription([
        set_resource_path,
        gz_server,
        gz_client,
        robot_state_publisher,
        spawn_robot,
        bridge,
        image_bridge,
    ])
