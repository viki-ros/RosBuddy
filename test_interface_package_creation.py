# test_interface_package_creation.py
import pathlib
import shutil
import sys

# --- START: Ensure 'rosbuddy' package is discoverable ---
# This adds the project root to sys.path
project_root_for_test = pathlib.Path(__file__).resolve().parent
if str(project_root_for_test) not in sys.path:
    sys.path.insert(0, str(project_root_for_test))
# --- END: Path adjustment ---

from rosbuddy.data_models import PackageConfig, InterfaceFileDefinition
from rosbuddy.core_logic.package_creator import create_package_scaffolding

def main_test():
    # --- Configuration for the test ---
    # 1. Define where the test workspace and package will be created
    #    It's good to use a temporary or clearly named test workspace.
    test_workspace_root = pathlib.Path.home() / "rosbuddy_interface_test_ws" # e.g., /home/viki/rosbuddy_interface_test_ws
    test_src_path = test_workspace_root / "src"
    new_package_name = "iface_provider_pkg" # Name of the package we are creating

    # 2. Clean up any old test package/workspace (optional, but good for clean runs)
    if (test_src_path / new_package_name).exists():
        print(f"Removing old package: {test_src_path / new_package_name}")
        shutil.rmtree(test_src_path / new_package_name)
    # If you want to clean the whole workspace:
    # if test_workspace_root.exists():
    #     print(f"Removing old workspace: {test_workspace_root}")
    #     shutil.rmtree(test_workspace_root)
    
    test_src_path.mkdir(parents=True, exist_ok=True)
    print(f"Test workspace 'src' directory ensured at: {test_src_path.resolve()}")

    # 3. Create the PackageConfig object
    pkg_config = PackageConfig(
        name=new_package_name,
        version="0.0.1",
        description="A test package that provides custom interfaces.",
        maintainer_email="test@example.com",
        maintainer_name="Test User",
        license_name="Apache License 2.0",
        build_type="ament_cmake"  # Interfaces are typically used with ament_cmake
    )

    # 4. Define the interfaces THIS PACKAGE WILL PROVIDE
    # Example 1: A simple message
    status_msg = InterfaceFileDefinition(
        file_name="MyStatus.msg",      # Base name + extension
        interface_type="msg",          # "msg", "srv", or "action"
        content="int32 error_code\nstring message", # The actual content of the .msg file
        interface_package_dependencies=[] # No external message dependencies for this simple one
    )
    pkg_config.add_interface_definition(status_msg)

    # Example 2: A service that uses a message from std_msgs
    command_srv = InterfaceFileDefinition(
        file_name="SetCommand.srv",
        interface_type="srv",
        content="std_msgs/String command_request\n---\nbool success\nstring response_message",
        interface_package_dependencies=["std_msgs"] # This service uses std_msgs/String
    )
    pkg_config.add_interface_definition(command_srv)
    
    # Example 3: An action (can be more complex)
    # For simplicity, let's make a basic action without external deps for now
    navigate_action = InterfaceFileDefinition(
        file_name="NavigateGoal.action",
        interface_type="action",
        content="# Define the goal\nfloat32 target_x\nfloat32 target_y\n---\n# Define the result\nbool reached_goal\n---\n# Define the feedback\nfloat32 distance_to_target",
        interface_package_dependencies=[] # Could be ["geometry_msgs"] if using Pose, for example
    )
    pkg_config.add_interface_definition(navigate_action)


    print(f"\n--- PackageConfig for '{pkg_config.name}' ---")
    print(f"  Name: {pkg_config.name}")
    print(f"  Build Type: {pkg_config.build_type}")
    print(f"  Interface Definitions ({len(pkg_config.interface_definitions)}):")
    for iface_def in pkg_config.interface_definitions:
        print(f"    - File: {iface_def.file_name}, Type: {iface_def.interface_type}, Deps: {iface_def.interface_package_dependencies}")
        # print(f"      Content: \n{iface_def.content}\n") # Uncomment to see content

    # 5. Call create_package_scaffolding
    #    The first argument to create_package_scaffolding is the base_path for the package,
    #    which is the 'src' directory of your workspace.
    print(f"\nAttempting to create package '{pkg_config.name}' in '{test_src_path.resolve()}'...")
    success = create_package_scaffolding(
        base_path=str(test_src_path),  # This should be the 'src' directory
        config=pkg_config,
        include_hello_world=False      # Set to True if you also want dummy C++ node
    )

    if success:
        package_on_disk_path = test_src_path / pkg_config.name
        print(f"\nSUCCESS: Package '{pkg_config.name}' created at {package_on_disk_path.resolve()}")
        print("Please verify the following files manually:")
        print(f"  - {package_on_disk_path / 'package.xml'}")
        print(f"  - {package_on_disk_path / 'CMakeLists.txt'}")
        print(f"  - {package_on_disk_path / status_msg.relative_path} (and its content)")
        print(f"  - {package_on_disk_path / command_srv.relative_path} (and its content)")
        print(f"  - {package_on_disk_path / navigate_action.relative_path} (and its content)")
        print(f"\nNext, open ROSBuddy, set '{test_workspace_root.resolve()}' as the active workspace, and try to build '{pkg_config.name}'.")
    else:
        print(f"\nFAILURE: Package creation for '{pkg_config.name}' failed.")


    main_test()