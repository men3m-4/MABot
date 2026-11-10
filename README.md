# MABot — Autonomous Mobile Robot for Warehouse Automation

**ROS 2 Jazzy | Gazebo Harmonic | Nav2 | Docker**

MABot is an autonomous mobile robot simulation project designed for warehouse automation and navigation. Built on ROS 2 Jazzy, the project integrates robot description, Gazebo simulation, localization, navigation, and warehouse mission execution into a unified robotics stack.

The project focuses on developing and testing autonomous mobile robot capabilities in a simulated warehouse environment, with an extensible architecture for future integration of computer vision, perception, and intelligent task execution.

## Key Features

- **Robot Simulation:** Mobile robot simulation in Gazebo Harmonic (Gazebo Sim 8).
- **ROS 2 Architecture:** Modular ROS 2 packages for robot control and system integration.
- **Robot Description:** URDF-based robot model and simulation configuration.
- **Localization:** AMCL-based robot localization.
- **Autonomous Navigation:** Nav2 integration for path planning and motion control.
- **SLAM:** Mapping and localization capabilities using SLAM Toolbox.
- **Warehouse Environment:** Custom warehouse simulation world.
- **Waypoint Navigation:** Autonomous navigation through predefined warehouse destinations.
- **Visualization:** RViz2 integration for robot state, maps, and navigation.
- **Docker Support:** Containerized development and simulation environment.

## Technology Stack

| Component | Technology |
|---|---|
| Operating System | Ubuntu 24.04 |
| Robotics Middleware | ROS 2 Jazzy |
| Simulation | Gazebo Harmonic / Gazebo Sim 8 |
| Navigation | Nav2 |
| Localization | AMCL |
| Mapping | SLAM Toolbox |
| Visualization | RViz2 |
| Robot Description | URDF / Xacro |
| Containerization | Docker / Docker Compose |


## Project Structure

```text
MABot/
├── Dockerfile
├── compose.yaml
├── .gitignore
└── src/
    ├── mabot_bringup/
    ├── mabot_description/
    ├── mabot_localization/
    ├── mabot_navigation/
    ├── mabot_slam/
    ├── mabot_warehouse_waypoints/
    └── warehouse_world/
```

### ROS 2 Packages

| Package | Responsibility |
|---|---|
| `mabot_bringup` | System launch files and mission integration |
| `mabot_description` | Robot model and simulation description |
| `mabot_localization` | Robot localization configuration |
| `mabot_navigation` | Nav2 configuration and navigation |
| `mabot_slam` | Mapping and localization using SLAM Toolbox |
| `mabot_warehouse_waypoints` | Warehouse waypoint mission |
| `warehouse_world` | Warehouse simulation environment |

## Requirements

- Ubuntu 24.04 (native Linux host).
- Docker Engine.
- Docker Compose V2.
- Internet connection for downloading the base image and dependencies.
- A working graphical display for Gazebo GUI and RViz2.

Check your Docker installation:

```bash
docker --version
docker compose version
```

## Getting Started with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/men3m-4/MABot.git
cd MABot
```

### 2. Build the Docker Image

```bash
docker build -t mabot:jazzy .
```

The Dockerfile uses the official ROS 2 Jazzy desktop image, installs package dependencies through rosdep, and builds the workspace using colcon.

### 3. Start the Container

```bash
docker compose up -d
```

Check the container status:

```bash
docker compose ps
```

### 4. Enter the Container

```bash
docker compose exec mabot bash
```

The interactive shell automatically loads the ROS 2 and MABot workspace environments.

Verify ROS 2:

```bash
echo $ROS_DISTRO
```

Expected output:

```text
jazzy
```

Verify the installed packages:

```bash
ros2 pkg list | grep -E '^(mabot_|warehouse_world)'
```

### 5. Run ROS 2 Commands from the Host

For non-interactive commands, explicitly source the ROS 2 and workspace environments:

```bash
docker compose exec mabot bash -c \
"source /opt/ros/jazzy/setup.bash && \
 source /opt/mabot_ws/install/setup.bash && \
 ros2 node list"
```

## Running the Warehouse Simulation

Start the warehouse mission:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py
```

The launch file integrates the warehouse simulation and the robot's ROS 2 navigation stack.

The simulation configuration includes:

- Gazebo warehouse environment.
- Robot simulation.
- ROS-Gazebo integration.
- Robot state publishing.
- Camera image bridge.
- Localization and Nav2 components.
- RViz2 visualization.

The launch file supports configurable parameters, including simulation time, GUI options, camera integration, map configuration, and waypoint configuration.

To inspect available launch arguments:

```bash
ros2 launch mabot_bringup warehouse_mission.launch.py --show-args
```

## Navigation

MABot uses Nav2 for autonomous navigation.

The navigation stack includes:

- AMCL localization.
- Map Server.
- Planner Server.
- Controller Server.
- Behavior Server.
- Behavior Tree Navigator.
- Global and Local Costmaps.
- Lifecycle Management.

After launching the simulation:

1. Open RViz2.
2. Verify the robot's localization.
3. Set the initial pose if required.
4. Send a navigation goal.
5. Monitor the robot as it plans and follows its path.

## Docker GUI Configuration

The Docker Compose configuration forwards the host X11 display to the container.

On a Linux desktop using X11 or XWayland, grant temporary local display access:

```bash
xhost +si:localuser:root
```

Start the container:

```bash
docker compose up -d
```

Enter the container:

```bash
docker compose exec mabot bash
```

Run RViz2:

```bash
rviz2
```

Run Gazebo:

```bash
gz sim
```

Revoke the temporary display permission when finished:

```bash
xhost -si:localuser:root
```

**Security note:** Only grant display access to trusted containers. X11 forwarding provides access to the host display.

## Development Workflow

Rebuild the Docker image after modifying source files:

```bash
docker build -t mabot:jazzy .
```

Restart the container:

```bash
docker compose down
docker compose up -d
```

Access the container:

```bash
docker compose exec mabot bash
```

Stop the environment:

```bash
docker compose down
```

