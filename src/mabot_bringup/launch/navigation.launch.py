import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    slam_share = get_package_share_directory('mabot_slam')
    navigation_share = get_package_share_directory('mabot_navigation')
    default_map = os.path.join(
        slam_share, 'map', 'mabot_warehouse_map.yaml'
    )
    navigation_launch = os.path.join(
        navigation_share, 'launch', 'nav2_bringup.launch.py'
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(navigation_launch),
        launch_arguments={
            'map': LaunchConfiguration('map'),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Full path to the occupancy map YAML file.',
        ),
        navigation,
    ])
