# mabot_bringup

`mabot_bringup` provides a single entry point for starting the MABot
warehouse simulation, Nav2, and the warehouse waypoint mission. It composes
the launch files and mission executable already provided by the other
workspace packages; it does not duplicate their robot, navigation, or route
logic.

## Package structure

- `launch/simulation.launch.py` forwards simulation options to
  `mabot_description/warehouse.launch.py`.
- `launch/navigation.launch.py` forwards the selected map to
  `mabot_navigation/nav2_bringup.launch.py`.
- `launch/warehouse_mission.launch.py` starts simulation, then navigation,
  then the warehouse mission.
- `config/warehouse_mission.yaml` provides the mission node's simulation-time
  default. The launch file supplies the installed waypoint file path.

## Build and source

From the workspace root with ROS 2 Jazzy available:

```bash
cd ~/MABot
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

The existing Docker image also builds all packages in `src/`. To rebuild it:

```bash
cd ~/MABot
docker compose build shell
```

## Launch

Start simulation only:

```bash
ros2 launch mabot_bringup simulation.launch.py
```

Start navigation only (simulation and robot TF must already be running):

```bash
ros2 launch mabot_bringup navigation.launch.py
```

Start the full warehouse mission:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py
```

The orchestration starts simulation first, allows Gazebo's robot-spawn process
a brief startup window, then starts navigation and the mission node. The
mission controller continues to wait for `/navigate_to_pose` and
`map -> base_footprint` before navigating.

## Options

Override the map and waypoint configuration with installed or custom YAML
files:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py \
  map:=/path/to/custom_map.yaml \
  waypoints_file:=/path/to/custom_waypoints.yaml
```

The defaults are `mabot_slam/map/mabot_warehouse_map.yaml` and
`mabot_warehouse_waypoints/config/warehouse_waypoints.yaml`, resolved from
their installed package shares.

Change the robot's initial pose in the warehouse:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py \
  x:=1.0 y:=2.0 yaw:=1.57
```

Disable Gazebo's GUI, RViz, or the simulated camera:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py \
  use_gazebo_gui:=false \
  use_rviz:=false \
  enable_camera:=false
```

The full launch defaults to Gazebo GUI, RViz, and camera enabled, matching
`mabot_description/warehouse.launch.py`. The mission uses simulation time by
default; `use_sim_time:=false` can be passed if needed.
