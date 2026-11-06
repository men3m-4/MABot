# MABot

MABot is a ROS 2 Jazzy mobile robot project for Gazebo Harmonic. It includes a robot description and simulation, SLAM and saved maps, AMCL localization, Nav2 configuration, warehouse worlds, and a waypoint delivery mission.

## Project Structure

```text
Mabot/
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
├── src/
│   ├── mabot_description/
│   ├── mabot_slam/
│   ├── mabot_localization/
│   ├── mabot_navigation/
│   ├── mabot_warehouse_waypoints/
│   └── warehouse_world/
├── .dockerignore
├── compose.yaml
└── README.md
```
Docker builds an image containing ROS, Gazebo, dependencies, and a compiled copy of `src/`. Compose starts that image as a shell, simulation, or GUI process. The regular ROS 2 workflow remains available without Docker.

### What the Docker Files Do

- `docker/Dockerfile` describes the ROS base image, tools, dependency installation, and colcon build that produce the MABot image.
- `docker/entrypoint.sh` sources ROS Jazzy and the built workspace, applies ROS networking defaults, then replaces itself with the command you requested.
- `compose.yaml` defines the interactive shell, headless simulation, GUI services, optional NVIDIA service, DDS settings, and persistent `/data` volume.
- `.dockerignore` keeps generated build outputs, Git metadata, and local-only files out of the image build context.

Dependencies are selected from the package manifests through rosdep and apt. The base tag and apt package versions are not pinned to image digests or exact Debian versions, so rebuilding later can resolve newer compatible package releases.

## Requirements

- Ubuntu 24.04 on a native Linux host for the Compose host-network setup below.
- Docker Engine and Docker Compose v2 plugin, installed from Docker's official Ubuntu instructions: <https://docs.docker.com/engine/install/ubuntu/>.
- Internet access when building, for the base image and apt/rosdep dependencies.
- The prepared image uses the official `ros:jazzy-ros-base` image. The project targets ROS 2 Jazzy and Gazebo Harmonic / Gazebo Sim 8.
- GUI use additionally requires a working host X11 session and an accessible Xauthority file. NVIDIA acceleration additionally requires a supported NVIDIA GPU/driver and NVIDIA Container Toolkit.

Check a local Docker installation before continuing:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Docker installation instructions are deliberately delegated to Docker's official documentation rather than using an install script. Its Ubuntu repository packages include `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, and `docker-compose-plugin`. Docker group membership grants effective root-level control of the host; do not add users to that group unless you accept that security consequence.

## Docker Status

**PREPARED / NOT YET TESTED:** The Dockerfile, Compose configuration, and commands in this section have not been built or run. They were prepared in the restricted ETGAH workspace, which has no Docker daemon access. Validate them on a local Ubuntu 24.04 host before relying on them. GUI and NVIDIA support are also untested.

## Build and Start

Run these commands from the MABot project root (the directory containing `compose.yaml`).

Build the image:

```bash
docker compose build
```

Open a temporary interactive shell:

```bash
docker compose run --rm shell
```

Start the warehouse simulation headlessly in the foreground:

```bash
docker compose --profile sim up gazebo
```

Or run it in the background and inspect its output:

```bash
docker compose --profile sim up -d gazebo
docker compose --profile sim logs -f gazebo
```

Stop the simulation container without deleting the persistent data volume:

```bash
docker compose --profile sim stop gazebo
```

Stop and remove Compose containers:

```bash
docker compose down
```

The named `mabot_data` volume is mounted at `/data` for maps and other generated files that should survive container replacement. `docker compose down -v` also deletes that volume; do not use `-v` if you need its contents. Source files are copied into the image at build time, so source edits require `docker compose build` before starting a new container.

## ROS 2 and DDS Networking

Compose uses Linux host networking so ROS 2 DDS discovery and traffic can work between the Gazebo container and separate ROS containers without publishing individual DDS ports. The default domain is `42`; set the same `ROS_DOMAIN_ID` in host ROS terminals if they need to communicate with these containers. Host networking shares the host network namespace and is intended for native Ubuntu, not Docker Desktop. `ROS_LOCALHOST_ONLY=0` permits DDS traffic beyond loopback.

Run additional commands in a temporary container with the same network settings:

```bash
docker compose run --rm shell ros2 pkg list
```

If the simulation is running in the `gazebo` service, a shell in that container is also available with:

```bash
docker compose --profile sim exec gazebo bash
```

## Gazebo, RViz, and Navigation

Commands below assume the container image has been built and that each component is run in its own terminal. Start the selected simulation first and leave it running.

### Headless warehouse Gazebo

```bash
docker compose --profile sim up gazebo
```

This uses the actual `mabot_description/warehouse.launch.py` launch, which starts the warehouse world, MABot, and ROS-Gazebo bridges without the local Gazebo GUI.

### Gazebo GUI

The host must have X11 available. Ensure `DISPLAY` is set and `XAUTHORITY` points to a readable Xauthority file before starting the GUI profile:

```bash
docker compose --profile gui up gazebo-gui
```

The Compose service binds only `/tmp/.X11-unix` and the selected Xauthority file. If X11 authorization or rendering is unavailable on the host, use the headless service instead. This setup does not weaken X server access control automatically.

### RViz

Start RViz in another terminal after simulation is running:

```bash
docker compose --profile gui run --rm rviz
```

The command loads the existing `mabot_navigation/rviz/navigation.rviz` configuration. Set or confirm the initial pose in RViz before sending Nav2 goals.

### SLAM mapping

With a matching simulation already running:

```bash
docker compose run --rm shell ros2 launch mabot_slam mapping.launch.py
```

Drive the robot in a separate terminal while mapping:

```bash
docker compose run --rm shell ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.10 -p turn:=0.20
```

Map saving is not automated by the launch. Save generated maps under `/data` to keep them in the persistent volume; for example, use `map_saver_cli -f /data/mabot_warehouse_map` while the map topic is available.

Run the installed map saver while SLAM is publishing the map:

```bash
docker compose run --rm shell ros2 run nav2_map_server map_saver_cli -f /data/mabot_warehouse_map --ros-args -p use_sim_time:=true -p save_map_timeout:=20.0
```

### AMCL localization

The standalone AMCL launch defaults to the map for the original MABot world. Start `mabot_description/gazebo.launch.py` (not the warehouse world) before using it:

```bash
docker compose run --rm shell ros2 launch mabot_description gazebo.launch.py
```

In a second terminal, start AMCL:

```bash
docker compose run --rm shell ros2 launch mabot_localization amcl.launch.py
```

Set the initial pose in RViz. Do not run standalone AMCL at the same time as Nav2's AMCL or another localization process publishing `map -> odom`.

SLAM Toolbox's saved pose-graph localization is a separate mode, also requiring a matching world and its `.posegraph` plus `.data` files:

```bash
docker compose run --rm shell ros2 launch mabot_slam localization.launch.py
```

### Nav2 in the warehouse

With the warehouse simulation running, launch Nav2 with the included warehouse map:

```bash
docker compose run --rm shell ros2 launch mabot_navigation nav2_bringup.launch.py map:=/opt/mabot_ws/src/mabot_slam/map/mabot_warehouse_map.yaml
```

Nav2 starts its own map server and AMCL. Use RViz to set the initial pose before sending a goal.

### Warehouse delivery mission

Start this only after warehouse simulation and Nav2 are active, and after localization places the robot at the configured Home waypoint:

```bash
docker compose run --rm shell ros2 run mabot_warehouse_waypoints warehouse_mission --ros-args -p use_sim_time:=true -p waypoints_file:=/opt/mabot_ws/src/mabot_warehouse_waypoints/config/warehouse_waypoints.yaml
```

The mission waits for Nav2, checks the robot's pose against Home, visits Loading, Storage, and Shipping, then returns Home. After success it stays active to publish waypoint markers; press Ctrl+C to stop it.

## Optional NVIDIA GPU

GPU use is optional. On the local host, first verify that the NVIDIA driver works, then install and configure NVIDIA Container Toolkit using its official instructions: <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>. Verify Docker GPU access with the NVIDIA test command documented by that project before using the Compose profile.

The `nvidia` Compose profile requests all NVIDIA devices. For example, an interactive container can be started with:

```bash
docker compose --profile nvidia run --rm nvidia
```

To run the headless warehouse simulation in a GPU-enabled container instead:

```bash
docker compose --profile nvidia run --rm nvidia ros2 launch mabot_description warehouse.launch.py
```

This profile requires a compatible NVIDIA driver, toolkit, Docker Engine, and Compose v2 support. It is not required for headless operation and has not been tested here.

## Normal ROS 2 Without Docker

Docker is optional. On a host with ROS 2 Jazzy, Gazebo Harmonic, and the project dependencies installed:

```bash
cd ~/Mabot
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install
source install/setup.bash
```

Source ROS and `install/setup.bash` in each additional terminal. The following commands run directly in those sourced terminals.

For warehouse simulation, RViz, Nav2, and the mission, use separate terminals in this order:

```bash
ros2 launch mabot_description warehouse.launch.py
ros2 run rviz2 rviz2 -d "$PWD/src/mabot_navigation/rviz/navigation.rviz" --ros-args -p use_sim_time:=true
ros2 launch mabot_navigation nav2_bringup.launch.py map:="$PWD/src/mabot_slam/map/mabot_warehouse_map.yaml"
ros2 run mabot_warehouse_waypoints warehouse_mission --ros-args -p use_sim_time:=true -p waypoints_file:="$PWD/src/mabot_warehouse_waypoints/config/warehouse_waypoints.yaml"
```

Start the first three commands in separate terminals and leave them running. Set the robot's initial pose in RViz before starting the mission. For SLAM mapping, start the simulation first, then run `ros2 launch mabot_slam mapping.launch.py` and drive with `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.10 -p turn:=0.20` in another terminal. For standalone AMCL, use the matching original-world simulation (`ros2 launch mabot_description gazebo.launch.py`) followed by `ros2 launch mabot_localization amcl.launch.py`; set the initial pose in RViz. Do not run competing localization or velocity-command nodes at the same time.

## Troubleshooting

- **Build reports a missing rosdep rule:** rerun rosdep on the six package manifests and check the matching ROS Jazzy package name. `mock_components/GenericSystem` is exported by the ROS package `hardware_interface`; the manifest declares `hardware_interface`.
- **Gazebo cannot resolve warehouse models:** use `mabot_description/warehouse.launch.py`, which sets `GZ_SIM_RESOURCE_PATH`, and keep `warehouse_world/models` and `warehouse_world/worlds` in the built workspace.
- **ROS containers do not discover each other:** ensure they use the same `ROS_DOMAIN_ID`, use host networking on native Linux, and check host firewall/multicast restrictions.
- **GUI fails to connect:** check `DISPLAY`, `XAUTHORITY`, the X11 socket, and the host X server's authorization. Use headless Gazebo if forwarding is unsupported.
- **GPU is unavailable:** confirm host `nvidia-smi`, install the NVIDIA Container Toolkit, configure Docker as directed by NVIDIA, then verify with a small GPU test container before using MABot.
- **Source changes do not appear in the image:** rebuild with `docker compose build` and recreate the container.