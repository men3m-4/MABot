#!/usr/bin/env bash
set -e

source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"
source /opt/mabot_ws/install/setup.bash

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-0}"

exec "$@"