"""Launch the VLN graph; use instruction_cli in a separate terminal."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os


def generate_launch_description():
    share = get_package_share_directory('vln_bringup')
    params = LaunchConfiguration('params_file')
    common = [params, {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}]
    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=os.path.join(share, 'config', 'vln.yaml')),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('enable_perception', default_value='true'),
        DeclareLaunchArgument('start_onestreamer_worker', default_value='true'),
        DeclareLaunchArgument('enable_goal_selector', default_value='true'),
        DeclareLaunchArgument('enable_planner', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='false'),
        Node(package='vln_perception', executable='streaming_semantics', output='screen',
             parameters=common + [{'start_worker': ParameterValue(
                 LaunchConfiguration('start_onestreamer_worker'), value_type=bool)}],
             condition=IfCondition(LaunchConfiguration('enable_perception'))),
        Node(package='vln_navigation', executable='vln_goal', output='screen',
             parameters=common, condition=IfCondition(LaunchConfiguration('enable_goal_selector'))),
        Node(package='vln_planner', executable='a_star_planner_node', output='screen',
             parameters=common, condition=IfCondition(LaunchConfiguration('enable_planner'))),
        Node(package='rviz2', executable='rviz2', output='screen',
             arguments=['-d', os.path.join(share, 'config', 'vln.rviz')],
             parameters=[{'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}],
             condition=IfCondition(LaunchConfiguration('use_rviz'))),
    ])
