from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    ld.add_action(Node(
        package='py_pkg_with_launch', executable='utility_node', name='my_utility', output='screen'
    ))

    return ld