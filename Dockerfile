FROM osrf/ros:jazzy-desktop
WORKDIR /opt/mabot_ws
COPY src/ src/
RUN apt-get update && rosdep update && rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
RUN . /opt/ros/jazzy/setup.sh && colcon build --symlink-install
RUN echo "source /opt/ros/jazzy/setup.bash && source /opt/mabot_ws/install/setup.bash" >> /root/.bashrc