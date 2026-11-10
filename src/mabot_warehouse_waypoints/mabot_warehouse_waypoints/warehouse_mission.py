
"""Run the warehouse delivery mission and display named waypoints."""

import math
import signal
import time

from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import Marker, MarkerArray

from mabot_warehouse_waypoints.waypoint_runner import WaypointRunner


class WarehouseMission(WaypointRunner):
    """Navigate to Home, visit warehouse locations, then return Home."""

    def __init__(self):
        super().__init__()

        self.locations = {point['name']: point for point in self.points}
        required = {'Home', 'Loading', 'Storage', 'Shipping'}

        if set(self.locations) != required:
            raise ValueError(
                'The file must contain Home, Loading, Storage and Shipping.'
            )

        self.active = None
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.marker_pub = self.create_publisher(
            MarkerArray, '/warehouse_waypoints/markers', qos
        )

        self.marker_timer = self.create_timer(
            0.5, self.publish_markers
        )

        self.publish_markers()

    def publish_markers(self):
        """Publish all warehouse waypoint markers."""
        message = MarkerArray()

        for index, (name, point) in enumerate(self.locations.items()):
            active = name == self.active

            for kind in ('arrow', 'label'):
                marker = Marker()
                marker.header.frame_id = 'map'
                marker.ns = f'warehouse_{kind}'
                marker.id = index
                marker.action = Marker.ADD

                marker.pose.position.x = point['x']
                marker.pose.position.y = point['y']

                marker.color.r = 0.0
                marker.color.g = 1.0 if active else 0.25
                marker.color.b = 0.0 if active else 1.0
                marker.color.a = 1.0

                if kind == 'arrow':
                    marker.type = Marker.ARROW
                    marker.pose.position.z = 0.12
                    marker.pose.orientation.z = math.sin(
                        point['yaw'] / 2.0
                    )
                    marker.pose.orientation.w = math.cos(
                        point['yaw'] / 2.0
                    )
                    marker.scale.x = 0.55
                    marker.scale.y = 0.10
                    marker.scale.z = 0.10

                else:
                    marker.type = Marker.TEXT_VIEW_FACING
                    marker.pose.position.z = 0.65
                    marker.pose.orientation.w = 1.0
                    marker.scale.z = 0.24
                    marker.text = name

                message.markers.append(marker)

        self.marker_pub.publish(message)

    def wait_for_localization(self, timeout=60.0):
        """
        Wait until a valid map -> base_footprint transform is available.

        This requires AMCL or another localization source to publish TF.
        It does not estimate the robot's initial pose by itself.
        """
        self.get_logger().info(
            'Waiting for localization: map -> base_footprint...'
        )

        deadline = time.monotonic() + timeout
        last_error = None

        while not self.stop_requested and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)

            try:
                transform = self.tf_buffer.lookup_transform(
                    'map',
                    'base_footprint',
                    Time()
                )

                position = transform.transform.translation
                rotation = transform.transform.rotation

                yaw = math.atan2(
                    2.0 * (rotation.w * rotation.z
                           + rotation.x * rotation.y),
                    1.0 - 2.0 * (
                        rotation.y * rotation.y
                        + rotation.z * rotation.z
                    ),
                )

                self.get_logger().info(
                    'Localization available. Current robot pose: '
                    f'x={position.x:.2f}, '
                    f'y={position.y:.2f}, '
                    f'yaw={math.degrees(yaw):.1f} deg'
                )

                return True

            except TransformException as error:
                last_error = str(error)

        if self.stop_requested:
            self.get_logger().warning(
                'Localization wait interrupted by user.'
            )
        else:
            self.get_logger().error(
                'Localization unavailable after waiting. '
                f'Last TF error: {last_error}. '
                'Check AMCL, initial pose and TF.'
            )

        return False

    def navigate_to_point(self, point, index, total):
        """Send a waypoint to Nav2 and wait for the navigation result."""
        goal = NavigateToPose.Goal()

        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        goal.pose.pose.position.x = point['x']
        goal.pose.pose.position.y = point['y']

        goal.pose.pose.orientation.z = math.sin(
            point['yaw'] / 2.0
        )
        goal.pose.pose.orientation.w = math.cos(
            point['yaw'] / 2.0
        )

        name = point['name']

        self.get_logger().info(
            f'[{index}/{total}] Navigating to {name}...'
        )

        self.pending_goal = self.client.send_goal_async(goal)

        if not self.wait_future(self.pending_goal):
            self.get_logger().error(
                f'No goal response received for {name}.'
            )
            return False

        self.goal_handle = self.pending_goal.result()
        self.pending_goal = None

        if not self.goal_handle.accepted:
            self.get_logger().error(
                f'Nav2 rejected the goal: {name}.'
            )
            self.goal_handle = None
            return False

        self.active = name
        self.publish_markers()

        self.result_future = self.goal_handle.get_result_async()

        if not self.wait_future(self.result_future):
            self.get_logger().warning(
                f'Waiting for navigation to {name} was interrupted.'
            )
            return False

        result = self.result_future.result()

        self.goal_handle = None
        self.result_future = None

        self.active = None
        self.publish_markers()

        if result.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(
                f'Navigation failed at {name}: '
                f'status={result.status}, '
                f'error_code={getattr(result.result, "error_code", "unknown")}. '
                'Mission stopped.'
            )
            return False

        self.get_logger().info(
            f'Reached {name} successfully.'
        )

        return True

    def wait_at_loading(self):
        """Wait for 30 simulation seconds at the Loading waypoint."""
        self.get_logger().info(
            'Loading: waiting 30 simulation seconds.'
        )

        start = self.get_clock().now().nanoseconds

        while not self.stop_requested:
            now = self.get_clock().now().nanoseconds

            if now < start:
                self.get_logger().error(
                    'Simulation time moved backwards. Mission stopped.'
                )
                return False

            if now - start >= 30_000_000_000:
                break

            rclpy.spin_once(self, timeout_sec=0.05)

        if self.stop_requested:
            return False

        self.get_logger().info('Loading wait complete.')
        return True

    def run_mission(self):
        """Navigate to Home first, execute the route, and return Home."""

        # Wait for Nav2 action server.
        self.get_logger().info(
            'Waiting for Nav2 /navigate_to_pose...'
        )

        deadline = time.monotonic() + 30.0

        while not self.client.wait_for_server(timeout_sec=0.2):
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.stop_requested:
                return False

            if time.monotonic() >= deadline:
                self.get_logger().error(
                    'Mission stopped: Nav2 action server unavailable.'
                )
                return False

        # Step 1: Wait for a valid robot pose.
        if not self.wait_for_localization(timeout=60.0):
            return False

        # Step 2: Navigate to Home automatically.
        self.get_logger().info(
            'Localization complete. Navigating to Home first.'
        )

        if not self.navigate_to_point(
            self.locations['Home'], 1, 5
        ):
            self.get_logger().error(
                'Could not reach Home. Mission aborted.'
            )
            return False

        self.get_logger().info(
            'Robot reached Home. Starting warehouse mission.'
        )

        # Step 3: Execute the warehouse route.
        route = [
            'Loading',
            'Storage',
            'Shipping',
            'Home',
        ]

        for index, name in enumerate(route, start=2):
            if self.stop_requested:
                return False

            point = self.locations[name]

            if not self.navigate_to_point(
                point, index, 5
            ):
                self.get_logger().error(
                    f'Mission stopped at {name}. '
                    'No further goals will be sent.'
                )
                return False

            # Preserve the 30-second Loading operation.
            if name == 'Loading':
                if not self.wait_at_loading():
                    return False

        self.get_logger().info(
            'Mission completed successfully: '
            'Home -> Loading -> Storage -> Shipping -> Home.'
        )

        return True


def main(args=None):
    rclpy.init(
        args=args,
        signal_handler_options=SignalHandlerOptions.NO
    )

    node = None
    handlers = {}
    code = 1

    try:
        node = WarehouseMission()

        def stop(signum, frame):
            node.stop_requested = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.signal(sig, stop)

        code = 0 if node.run_mission() else 1

        if code == 0:
            node.get_logger().info(
                'Markers remain visible. Press Ctrl+C to close.'
            )

            while not node.stop_requested:
                rclpy.spin_once(node, timeout_sec=0.1)

    except Exception as error:
        if node is not None:
            node.get_logger().error(
                f'Warehouse mission error: {error}'
            )
        else:
            print(f'Warehouse mission error: {error}')

    finally:
        if node is not None:
            try:
                node.cancel_current_goal()
                node.active = None
                node.publish_markers()
                rclpy.spin_once(node, timeout_sec=0.1)
            finally:
                node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

        for sig, handler in handlers.items():
            signal.signal(sig, handler)

    return code


if __name__ == '__main__':
    raise SystemExit(main())
