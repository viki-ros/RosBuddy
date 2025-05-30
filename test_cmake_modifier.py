import sys
import pathlib
import tempfile
from pathlib import Path
import os

# Ensure rosbuddy package is discoverable
project_root_for_test = pathlib.Path(__file__).resolve().parent
if str(project_root_for_test) not in sys.path:
    sys.path.insert(0, str(project_root_for_test))

from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
from rosbuddy.file_generators.cmake_modifier import update_cmakelists_for_new_interface

def write_file_and_modify(content: str, iface_def: InterfaceFileDefinition, project_name: str = "test_pkg") -> tuple[bool, str]:
    """Helper to write content to a temp file, modify it, and return results."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tf:
        tf.write(content)
        tf.seek(0)
        path = Path(tf.name)
    
    success = update_cmakelists_for_new_interface(path, iface_def, project_name)
    with open(path, 'r') as f:
        result = f.read()
    os.unlink(path)  # Clean up
    return success, result

def assert_contains(content: str, *expected_lines):
    """Helper to assert content contains expected lines in order."""
    content_lines = content.splitlines()
    curr_idx = 0
    for expected in expected_lines:
        found = False
        for i in range(curr_idx, len(content_lines)):
            if expected in content_lines[i]:
                curr_idx = i + 1
                found = True
                break
        if not found:
            raise AssertionError(f"Expected to find '{expected}' after line {curr_idx} in:\n{content}")

def test_empty_file():
    """Test adding interface to empty CMakeLists.txt"""
    iface_def = InterfaceFileDefinition(
        file_name="Empty.msg",
        interface_type="msg",
        content="string data",
        relative_path="msg/Empty.msg",
        interface_package_dependencies=[]
    )
    
    success, result = write_file_and_modify("", iface_def)
    assert success, "Should succeed on empty file"
    assert_contains(
        result,
        "find_package(rosidl_default_generators REQUIRED)",
        'rosidl_generate_interfaces(${PROJECT_NAME}',
        '"msg/Empty.msg"'
    )
    print("✓ Empty file test passed")

def test_existing_rosidl_block():
    """Test modifying existing rosidl_generate_interfaces block"""
    iface_def = InterfaceFileDefinition(
        file_name="NewMsg.msg",
        interface_type="msg",
        content="int32 data\nstring name",
        relative_path="msg/NewMsg.msg",
        interface_package_dependencies=["std_msgs"]
    )
    
    initial_content = '''
cmake_minimum_required(VERSION 3.8)
project(test_pkg)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ExistingMsg.msg"
  DEPENDENCIES geometry_msgs
)

ament_package()
'''
    
    success, result = write_file_and_modify(initial_content, iface_def)
    assert success, "Should succeed with existing block"
    assert_contains(
        result,
        'find_package(std_msgs REQUIRED)',
        'rosidl_generate_interfaces(${PROJECT_NAME}',
        '"msg/ExistingMsg.msg"',
        '"msg/NewMsg.msg"',
        'DEPENDENCIES geometry_msgs std_msgs'
    )
    print("✓ Existing rosidl block test passed")

def test_complex_dependencies():
    """Test handling complex dependency situations"""
    iface_def = InterfaceFileDefinition(
        file_name="Complex.msg",
        interface_type="msg",
        content="geometry_msgs/Pose pose\nstd_msgs/Header header\nsensor_msgs/Image image",
        relative_path="msg/Complex.msg",
        interface_package_dependencies=["geometry_msgs", "std_msgs", "sensor_msgs"]
    )
    
    initial_content = '''
cmake_minimum_required(VERSION 3.8)
project(test_pkg)

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)  # Already has one dependency
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Simple.msg"
  DEPENDENCIES geometry_msgs
)

ament_package()
'''
    
    success, result = write_file_and_modify(initial_content, iface_def)
    assert success, "Should succeed with complex dependencies"
    assert_contains(
        result,
        'find_package(std_msgs REQUIRED)',
        'find_package(sensor_msgs REQUIRED)',
        'rosidl_generate_interfaces(',
        '"msg/Simple.msg"',
        '"msg/Complex.msg"',
        'DEPENDENCIES geometry_msgs sensor_msgs std_msgs'  # Should be sorted
    )
    print("✓ Complex dependencies test passed")

def test_multiple_rosidl_blocks():
    """Test behavior with multiple rosidl_generate_interfaces blocks (should add TODO)"""
    iface_def = InterfaceFileDefinition(
        file_name="Another.msg",
        interface_type="msg",
        content="float64 value",
        relative_path="msg/Another.msg",
        interface_package_dependencies=[]
    )
    
    initial_content = '''
cmake_minimum_required(VERSION 3.8)
project(test_pkg)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/First.msg"
)

# Some other content
add_library(mylib src/lib.cpp)

rosidl_generate_interfaces(other_target
  "msg/Second.msg"
)

ament_package()
'''
    
    success, result = write_file_and_modify(initial_content, iface_def)
    assert success, "Should succeed but add TODO comment"
    assert "TODO: ROSBuddy added new interface 'msg/Another.msg'" in result
    print("✓ Multiple rosidl blocks test passed")

def test_formatting_preservation():
    """Test that existing formatting is preserved"""
    iface_def = InterfaceFileDefinition(
        file_name="New.msg",
        interface_type="msg",
        content="int32 data",
        relative_path="msg/New.msg",
        interface_package_dependencies=[]
    )
    
    initial_content = '''cmake_minimum_required(VERSION 3.8)
project(test_pkg)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
    "msg/Existing.msg"   # With comment
    
    # Empty line above
)

ament_package()
'''
    
    success, result = write_file_and_modify(initial_content, iface_def)
    assert success, "Should succeed while preserving format"
    assert '#' in result, "Comments should be preserved"
    assert '\n\n' in result, "Empty lines should be preserved"
    print("✓ Formatting preservation test passed")

def main():
    print("Running CMakeLists.txt modifier tests...")
    test_empty_file()
    test_existing_rosidl_block()
    test_complex_dependencies()
    test_multiple_rosidl_blocks()
    test_formatting_preservation()
    print("\nAll tests passed! ✓")

if __name__ == "__main__":
    main()
