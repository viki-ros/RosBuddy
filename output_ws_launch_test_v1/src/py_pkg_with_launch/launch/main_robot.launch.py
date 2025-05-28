from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    ld = LaunchDescription()

    ld.add_action(Node(
        package='some_ros_package', executable='some_node_executable', name='my_first_node', namespace='robot1', parameters=[
                {'my_int_param': 42},
                {'my_str_param': 'hello_ros'},
                {'my_bool_param': True},
                {'my_float_param': 3.14},
                {'my_list_param': [1, 2, 'item3']}
            ], remappings=[('/input_topic', '/remapped_input'), ('relative_topic', 'new_relative_name')], output='screen'
    ))

    ld.add_action(Node(
        package='another_package', executable='talker', name='simple_talker', output='screen'
    ))

    ld.add_action(IncludeLaunchDescription(
        source=PythonLaunchDescriptionSource('included_utility.launch.py'), launch_arguments=[('some_arg_for_included', 'true')].items()
    ))

    return ld