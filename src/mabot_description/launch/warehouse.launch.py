import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
)

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    mabot_share = get_package_share_directory('mabot_description')
    warehouse_share = get_package_share_directory('warehouse_world')
    ros_gz_share = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(
        warehouse_share, 'worlds', 'warehouse_storage.sdf'
    )
    xacro_file = os.path.join(
        mabot_share, 'urdf', 'mabot.urdf.xacro'
    )
    bridge_file = os.path.join(
        mabot_share, 'config', 'gz_bridge.yaml'
    )

    # مسار ملف إعدادات RViz لو متوفر في الباكدج
    rviz_config_file = os.path.join(
        mabot_share, 'rviz', 'mabot.rviz'
    )

    # Preserve existing resource paths.
    resource_paths = [
        os.path.join(warehouse_share, 'worlds'),
        os.path.join(warehouse_share, 'models'),
        str(Path(warehouse_share).parent.resolve()),
        str(Path(mabot_share).parent),
    ]

    existing_paths = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if existing_paths:
        resource_paths.append(existing_paths)

    resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.pathsep.join(resource_paths),
    )

    enable_camera = LaunchConfiguration('enable_camera')

    launch_arguments = [
        # تم تعديل القيمة الافتراضية هنا لتكون true لتشغيل واجهة جازيبو مباشرة
        DeclareLaunchArgument(
            'use_gazebo_gui',
            default_value='true',
            description='Enable the local Gazebo GUI.',
        ),
        # خيار تشغيل RViz مع جعله true افتراضياً
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

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            xacro_file,
            ' enable_camera:=',
            enable_camera,
        ]),
        value_type=str,
    )

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_share, 'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', world_file],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_share, 'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': '-g -v2',
            'on_exit_shutdown': 'true',
        }.items(),
        condition=IfCondition(
            LaunchConfiguration('use_gazebo_gui')
        ),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_mabot',
        output='screen',
        arguments=[
            '-world', 'warehouse_storage',
            '-name', 'mabot',
            '-topic', 'robot_description',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gazebo_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_file,
            'use_sim_time': True,
        }],
    )

    camera_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='camera_image_bridge',
        output='screen',
        arguments=['/camera/image'],
        remappings=[
            ('/camera/image', '/camera/image_raw'),
        ],
        parameters=[{
            'use_sim_time': True,
        }],
        condition=IfCondition(enable_camera),
    )

    # عقدة تشغيل RViz2 تلقائياً
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file] if os.path.exists(rviz_config_file) else [],
        parameters=[{
            'use_sim_time': True,
        }],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([
        *launch_arguments,
        resource_path,
        gazebo_server,
        gazebo_gui,
        robot_state_publisher,
        spawn_robot,
        bridge,
        camera_image_bridge,
        rviz_node,
    ])