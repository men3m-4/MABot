import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    description_share = get_package_share_directory('mabot_description')
    warehouse_launch = os.path.join(
        description_share, 'launch', 'warehouse.launch.py'
    )

    forwarded_arguments = (
        'use_gazebo_gui',
        'use_rviz',
        'enable_camera',
        'x',
        'y',
        'z',
        'yaw',
    )
    defaults = {
        'use_gazebo_gui': 'true',
        'use_rviz': 'true',
        'enable_camera': 'true',
        'x': '0.0',
        'y': '0.0',
        'z': '0.10',
        'yaw': '0.0',
    }

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(warehouse_launch),
        launch_arguments={
            name: LaunchConfiguration(name)
            for name in forwarded_arguments
        }.items(),
    )

    return LaunchDescription([
        *[
            DeclareLaunchArgument(name, default_value=defaults[name])
            for name in forwarded_arguments
        ],
        simulation,
    ])
