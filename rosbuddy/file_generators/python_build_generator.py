# rosbuddy/file_generators/python_build_generator.py
import textwrap
import os 
from glob import glob 
from rosbuddy.data_models.package_config import PackageConfig

def generate_setup_py_content(config: PackageConfig, entry_points: dict) -> str:
    # --- Entry Points ---
    entry_points_str_lines = []
    for name, module_filename_stem in entry_points.items():
        # Indent each entry point line correctly
        entry_points_str_lines.append(f"            '{name} = {config.name}.{module_filename_stem}:main',")
    # Join them, ensuring the last one doesn't have an extra comma if it's the only one,
    # though a trailing comma in a list is fine.
    entry_points_final_str = "\n".join(entry_points_str_lines)


    # --- Maintainer and License (first one) ---
    first_maintainer_name = "TODO: Maintainer name"
    first_maintainer_email = "user@todo.todo"
    if config.maintainers:
        first_maintainer_name = config.maintainers[0].get('name', first_maintainer_name)
        first_maintainer_email = config.maintainers[0].get('email', first_maintainer_email)
    
    first_license = "TODO: License declaration"
    if config.licenses:
        first_license = config.licenses[0]

    # --- Data Files ---
    data_files_entries_for_format = [
        (os.path.join('share', 'ament_index', 'resource_index', 'packages'), ['resource/' + config.name]),
        (os.path.join('share', config.name), ['package.xml']),
    ]

    if config.launch_configurations:
        launch_file_source_paths = [os.path.join('launch', lc.file_name) for lc in config.launch_configurations]
        if launch_file_source_paths:
            data_files_entries_for_format.append(
                (os.path.join('share', config.name, 'launch'), launch_file_source_paths)
            )

    if config.config_files_paths:
        config_file_source_paths = [os.path.join('config', os.path.basename(p)) for p in config.config_files_paths]
        if config_file_source_paths:
            data_files_entries_for_format.append(
                (os.path.join('share', config.name, 'config'), config_file_source_paths) 
            )
    
    data_files_str_lines = []
    for dest, sources in data_files_entries_for_format:
        # Correct indentation for each (dest, sources) tuple line
        source_list_str = "[" + ", ".join([repr(s) for s in sources]) + "]"
        data_files_str_lines.append(f"        ({repr(dest)}, {source_list_str}),")
    
    data_files_final_str = "\n".join(data_files_str_lines)
    # Remove trailing comma from the last line if it exists and lines were added
    if data_files_final_str.endswith(','):
        data_files_final_str = data_files_final_str[:-1]


    # --- Main Template ---
    # Note: The f-string variables {data_files_final_str} and {entry_points_final_str}
    # are now expected to bring their own correct multi-line indentation.
    # textwrap.dedent will handle the main structure.
    setup_py_template = f"""\
from setuptools import find_packages, setup
import os
from glob import glob

package_name = '{config.name}'

setup(
    name=package_name,
    version='{config.version}',
    packages=find_packages(exclude=['test']),
    data_files=[
{data_files_final_str}
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='{first_maintainer_name}',
    maintainer_email='{first_maintainer_email}',
    description='{config.description}',
    license='{first_license}',
    tests_require=['pytest'],
    entry_points={{
        'console_scripts': [
{entry_points_final_str}
        ],
    }},
)
"""
    return textwrap.dedent(setup_py_template)

# generate_hello_world_python_node_content remains unchanged
# ... (paste the existing generate_hello_world_python_node_content here) ...
# rosbuddy/file_generators/python_build_generator.py
# ... (generate_setup_py_content remains the same) ...

def generate_hello_world_python_node_content(package_name: str) -> str:
    """Generates a simple 'hello world' Python node with flushed output."""
    return textwrap.dedent(f"""\
        import rclpy
        from rclpy.node import Node
        # from std_msgs.msg import String 

        class HelloWorldNode(Node):
            def __init__(self):
                super().__init__('{package_name}_hello_world_node')
                timer_period = 0.5 
                self.timer = self.create_timer(timer_period, self.timer_callback)
                self.i = 0
                # Use flush=True for print statements
                print('Hello world Python node started! (Prototype version)', flush=True)
                self.get_logger().info('Hello world Python node started via logger!') # Logger usually flushes

            def timer_callback(self):
                log_msg = f'Hello World Python: {{self.i}} (Prototype: not publishing to ROS topic)'
                # Use flush=True for print statements
                print(log_msg, flush=True) 
                self.get_logger().info(f'Timer tick: {{self.i}}') # Logger usually flushes
                self.i += 1

        def main(args=None):
            rclpy.init(args=args)
            node = HelloWorldNode()
            try:
                rclpy.spin(node)
            except KeyboardInterrupt:
                if node: node.get_logger().info('Keyboard interrupt, shutting down.') 
            finally:
                if node: node.destroy_node()
                rclpy.shutdown()

        if __name__ == '__main__':
            main()
    """)