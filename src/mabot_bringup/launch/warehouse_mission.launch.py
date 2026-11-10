import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnExecutionComplete
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    bringup_share = get_package_share_directory('mabot_bringup')
    slam_share = get_package_share_directory('mabot_slam')
    waypoints_share = get_package_share_directory(
        'mabot_warehouse_waypoints'
    )

    default_map = os.path.join(
        slam_share, 'map', 'mabot_warehouse_map.yaml'
    )
    default_waypoints = os.path.join(
        waypoints_share, 'config', 'warehouse_waypoints.yaml'
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'simulation.launch.py')
        ),
        launch_arguments={
            name: LaunchConfiguration(name)
            for name in (
                'use_gazebo_gui',
                'use_rviz',
                'enable_camera',
                'x',
                'y',
                'z',
                'yaw',
            )
        }.items(),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'map': LaunchConfiguration('map'),
        }.items(),
    )

    mission = Node(
        package='mabot_warehouse_waypoints',
        executable='warehouse_mission',
        name='warehouse_mission',
        output='screen',
        parameters=[
            os.path.join(
                bringup_share, 'config', 'warehouse_mission.yaml'
            ),
            {
                'use_sim_time': ParameterValue(
                    LaunchConfiguration('use_sim_time'),
                    value_type=bool,
                ),
                'waypoints_file': ParameterValue(
                    LaunchConfiguration('waypoints_file'),
                    value_type=str,
                ),
            },
        ],
    )

    # Give Gazebo's spawn process a startup window before Nav2 begins.
    # The mission still waits for the Nav2 action server and localization TF.
    start_navigation = RegisterEventHandler(
        OnExecutionComplete(
            target_action=simulation,
            on_completion=[
                TimerAction(period=5.0, actions=[navigation]),
            ],
        )
    )
    start_mission = RegisterEventHandler(
        OnExecutionComplete(
            target_action=navigation,
            on_completion=[mission],
        )
    )

    arguments = [
        DeclareLaunchArgument('map', default_value=default_map),
        DeclareLaunchArgument(
            'waypoints_file',
            default_value=default_waypoints,
            description='Full path to the warehouse waypoint YAML file.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use the Gazebo simulation clock in the mission node.',
        ),
        DeclareLaunchArgument(
            'use_gazebo_gui',
            default_value='true',
            description='Enable the local Gazebo GUI.',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz2 automatically.',
        ),
        DeclareLaunchArgument(
            'enable_camera',
            default_value='true',
            description='Enable the simulated RGB-D camera.',
        ),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.10'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
    ]

    return LaunchDescription([
        *arguments,
        start_navigation,
        start_mission,
        simulation,
    ])
