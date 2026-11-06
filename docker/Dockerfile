FROM ros:jazzy-ros-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

WORKDIR /opt/mabot_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      python3-colcon-common-extensions \
      python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

RUN if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then rosdep init; fi \
    && rosdep update

COPY src/ src/

RUN source /opt/ros/jazzy/setup.bash \
    && apt-get update \
    && rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y \
    && colcon build --symlink-install \
    && rm -rf /var/lib/apt/lists/*

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

ENV ROS_DOMAIN_ID=42
ENV ROS_LOCALHOST_ONLY=0
WORKDIR /opt/mabot_ws

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]