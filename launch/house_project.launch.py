#!/usr/bin/env python3
"""
Launch Gazebo with the custom house world (house_project.world) and spawn
a TurtleBot3. Based on turtlebot3_house.launch.py from turtlebot3_gazebo (Jazzy),
with the world path pointed at your own file.

Run:
    export TURTLEBOT3_MODEL=waffle
    ros2 launch ~/smart-room-assistant-ros2/launch/house_project.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

# Your custom world with the added objects
WORLD = os.path.expanduser("~/my_worlds/house_project.world")


def generate_launch_description():
    tb3_launch_dir = os.path.join(get_package_share_directory("turtlebot3_gazebo"), "launch")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    x_pose = LaunchConfiguration("x_pose", default="-2.0")
    y_pose = LaunchConfiguration("y_pose", default="-0.5")

    # Lets Gazebo find model://turtlebot3_house and other TurtleBot3 models
    set_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(get_package_share_directory("turtlebot3_gazebo"), "models"),
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

    spawn_turtlebot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3_launch_dir, "spawn_turtlebot3.launch.py")),
        launch_arguments={"x_pose": x_pose, "y_pose": y_pose}.items(),
    )

    return LaunchDescription([
        set_resource_path,
        gz_server,
        gz_client,
        spawn_turtlebot,
        robot_state_publisher,
    ])
