# rosbuddy/core_logic/package_creator.py
import pathlib
import textwrap
import traceback
import os

from rosbuddy.data_models import PackageConfig # ExecutableTarget, LibraryTarget used via config
from rosbuddy.file_generators import (
    generate_package_xml_content,
    generate_setup_py_content,
    generate_hello_world_python_node_content,
    generate_cmake_lists_content,
    generate_python_launch_file_content
)

def _create_dummy_cpp_file_content(target_name: str, is_node: bool = True) -> str:
    """Generates minimal C++ content for a dummy file."""
    if is_node: # For an executable/node
        return textwrap.dedent(f"""\
            #include "rclcpp/rclcpp.hpp"

            int main(int argc, char * argv[]) {{
              rclcpp::init(argc, argv);
              // Replace with your node class or logic
              auto node = std::make_shared<rclcpp::Node>("{target_name.lower()}_placeholder_node");
              RCLCPP_INFO(node->get_logger(), "Dummy C++ node '{target_name}' started.");
              rclcpp::spin(node);
              rclcpp::shutdown();
              return 0;
            }}
            """)
    else: # For a library
        return textwrap.dedent(f"""\
            #include <iostream> // Or a relevant header for the library

            void {target_name}_dummy_function() {{
              // std::cout << "Hello from {target_name} library!" << std::endl;
            }}

            // Add other library functions here
            """)

def create_package_scaffolding(base_path: str, config: PackageConfig, include_hello_world: bool = True):
    pkg_path = pathlib.Path(base_path) / config.name
    print(f"Creating package in: {pkg_path.resolve()}")

    try:
        pkg_path.mkdir(parents=True, exist_ok=True)

        package_xml_path = pkg_path / "package.xml"
        package_xml_content = generate_package_xml_content(config)
        with open(package_xml_path, "w") as f:
            f.write(package_xml_content)
        print(f"  Created: {package_xml_path.name}")

        if config.build_type == "ament_python":
            # ... (ament_python scaffolding logic remains the same) ...
            src_pkg_module_path = pkg_path / config.name
            src_pkg_module_path.mkdir(exist_ok=True)
            (src_pkg_module_path / "__init__.py").touch(exist_ok=True)
            print(f"  Created: {config.name}/__init__.py")

            resource_path = pkg_path / "resource"
            resource_path.mkdir(exist_ok=True)
            (resource_path / config.name).touch(exist_ok=True)
            print(f"  Created: resource/{config.name}")

            entry_points = {}
            if include_hello_world and config.build_type == "ament_python":
                node_script_filename = "hello_world_node.py"
                node_script_stem = node_script_filename.replace('.py', '')
                hello_node_path = src_pkg_module_path / node_script_filename
                hello_node_content = generate_hello_world_python_node_content(config.name)
                with open(hello_node_path, "w") as f:
                    f.write(hello_node_content)
                entry_points["hello_world"] = node_script_stem
                print(f"  Created: {config.name}/{node_script_filename}")

            setup_py_path = pkg_path / "setup.py"
            setup_py_content = generate_setup_py_content(config, entry_points)
            with open(setup_py_path, "w") as f:
                f.write(setup_py_content)
            print(f"  Created: {setup_py_path.name}")

            setup_cfg_path = pkg_path / "setup.cfg"
            with open(setup_cfg_path, "w") as f:
                f.write(textwrap.dedent(f"""\
                    [develop]
                    script_dir=$base/lib/{config.name}
                    [install]
                    install_scripts=$base/lib/{config.name}
                """))
            print(f"  Created: {setup_cfg_path.name}")


        elif config.build_type == "ament_cmake":
            cmakelists_path = pkg_path / "CMakeLists.txt"
            cmakelists_content = generate_cmake_lists_content(config)
            with open(cmakelists_path, "w") as f:
                f.write(cmakelists_content)
            print(f"  Created: {cmakelists_path.name}")

            src_dir_path = pkg_path / "src" # Ensure src directory exists
            src_dir_path.mkdir(exist_ok=True)
            print(f"  Created/Ensured: src/ directory")

            # Create dummy C++ source files for defined targets
            for lib_target in config.library_targets:
                for source_file_rel_path in lib_target.sources: # e.g., "src/my_lib.cpp"
                    full_source_path = pkg_path / source_file_rel_path
                    full_source_path.parent.mkdir(parents=True, exist_ok=True) # Ensure dir like 'src/' exists
                    if not full_source_path.exists(): # Only create if it doesn't exist
                        with open(full_source_path, "w") as f:
                            f.write(_create_dummy_cpp_file_content(lib_target.name, is_node=False))
                        print(f"    Created dummy C++ library source: {source_file_rel_path}")
            
            for exec_target in config.executable_targets:
                for source_file_rel_path in exec_target.sources: # e.g., "src/my_node.cpp"
                    full_source_path = pkg_path / source_file_rel_path
                    full_source_path.parent.mkdir(parents=True, exist_ok=True)
                    if not full_source_path.exists():
                        with open(full_source_path, "w") as f:
                            f.write(_create_dummy_cpp_file_content(exec_target.name, is_node=True))
                        print(f"    Created dummy C++ executable source: {source_file_rel_path}")
            
            # Note: include_hello_world for CMake could be used to automatically
            # add an ExecutableTarget to config.executable_targets if desired.
            # For now, it just prints a message if no explicit targets are defined.
            if include_hello_world and not config.executable_targets and not config.library_targets:
                 print(f"  Info: 'include_hello_world' for CMake implies creating a C++ node. Define an ExecutableTarget in PackageConfig.")


        # --- Create standard directories and specified files (launch, config, interfaces) ---
        # Launch files
        launch_dir = pkg_path / "launch"
        if config.launch_configurations:
            launch_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created/Ensured: launch/ directory")
            for launch_config_obj in config.launch_configurations:
                launch_file_name = launch_config_obj.file_name
                if not launch_file_name.endswith(('.launch.py', '.launch.xml', '.launch.yaml')):
                    launch_file_name += ".launch.py"
                full_launch_file_path = launch_dir / launch_file_name
                if launch_file_name.endswith(".launch.py"):
                    launch_content = generate_python_launch_file_content(launch_config_obj)
                    with open(full_launch_file_path, "w") as f:
                        f.write(launch_content)
                    print(f"    Generated launch file: launch/{launch_file_name}")
                else:
                    full_launch_file_path.touch(exist_ok=True)
                    print(f"    Created dummy (non-python) launch file: launch/{launch_file_name}")
        else:
            launch_dir.mkdir(exist_ok=True)
            print(f"  Created/Ensured: launch/ directory (no specific launch configurations provided)")

        # Config files
        config_dir = pkg_path / "config"
        if config.config_files_paths:
            config_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created/Ensured: config/ directory")
            for config_file_rel_path in config.config_files_paths:
                full_config_file_path = config_dir / os.path.basename(config_file_rel_path)
                full_config_file_path.touch(exist_ok=True)
                print(f"    Created dummy config file: config/{os.path.basename(config_file_rel_path)}")
        else:
            config_dir.mkdir(exist_ok=True)
            print(f"  Created/Ensured: config/ directory (no specific config files requested)")

        # Interface files
        if hasattr(config, 'interface_definitions') and config.interface_definitions:
            print(f"  Processing interface definitions:")
            for iface_def in config.interface_definitions:
                try:
                    full_interface_file_path = pkg_path / iface_def.relative_path
                    interface_type_dir = full_interface_file_path.parent
                    interface_type_dir.mkdir(parents=True, exist_ok=True)
                    with open(full_interface_file_path, "w", encoding="utf-8") as f:
                        f.write(iface_def.content)
                    print(f"    Created interface file: {iface_def.relative_path} with content.")
                except AttributeError:
                    print(f"    Skipping invalid interface definition object: {iface_def}")
                    traceback.print_exc()
                except OSError as e:
                    print(f"    Error creating interface file {iface_def.relative_path}: {e}")
                    traceback.print_exc()
                except Exception as e:
                    print(f"    Unexpected error processing interface definition {getattr(iface_def, 'file_name', iface_def)}: {e}")
                    traceback.print_exc()
        else:
            (pkg_path / "msg").mkdir(exist_ok=True)
            (pkg_path / "srv").mkdir(exist_ok=True)
            (pkg_path / "action").mkdir(exist_ok=True)
            print(f"  Created/Ensured: msg/, srv/, action/ directories (no specific interface definitions provided).")

        print(f"Package '{config.name}' created successfully at {pkg_path.resolve()}")
        return True

    except Exception as e:
        print(f"Error creating package '{config.name}': {e}")
        traceback.print_exc()
        return False