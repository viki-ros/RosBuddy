from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    ld.add_action(Node(
        package='my_adv_cmake_pkg', executable='main_node', name='adv_main_node_launched', output='screen'
    ))

    ld.add_action(Node(
        package='my_adv_cmake_pkg', executable='talker_node', name='adv_talker_node_launched', output='screen'
    ))

    return ld