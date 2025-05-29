from pathlib import Path
from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
from rosbuddy.file_generators.package_xml_modifier import update_package_xml_for_new_interface
import xml.etree.ElementTree as ET

def print_package_xml(path):
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read())

def main():
    # Create a dummy package.xml
    pkg_xml_path = Path("dummy_package.xml")
    pkg_xml_path.write_text('''<?xml version="1.0"?>
<package format="3">
  <name>dummy_pkg</name>
  <version>0.0.0</version>
  <description>Dummy package for test</description>
  <maintainer email="user@example.com">ROS User</maintainer>
  <license>Apache License 2.0</license>
</package>
''', encoding='utf-8')

    # Create a dummy interface definition
    iface_def = InterfaceFileDefinition(
        file_name="MyStatus.msg",
        interface_type="msg",
        content="int32 status\nstring message",
        interface_package_dependencies=["std_msgs", "geometry_msgs"]
    )

    print("Before update:\n----------------")
    print_package_xml(pkg_xml_path)

    # Update package.xml
    update_package_xml_for_new_interface(pkg_xml_path, iface_def)

    print("\nAfter update:\n----------------")
    print_package_xml(pkg_xml_path)

if __name__ == "__main__":
    main()
