from pathlib import Path
from typing import Optional, Dict
import xml.etree.ElementTree as ET
from rosbuddy.data_models.interface_definition import InterfaceFileDefinition

def ensure_element_with_text(parent_element: ET.Element, tag_name: str, text: str, attributes: Optional[Dict[str, str]] = None) -> ET.Element:
    """Finds or creates an element with specific text and attributes. Avoids duplicates if text and attributes match."""
    if attributes is None:
        attributes = {}
    for child in parent_element.findall(tag_name):
        match = (child.text == text)
        if attributes:
            for attr_k, attr_v in attributes.items():
                if child.get(attr_k) != attr_v:
                    match = False
                    break
        if match:
            return child # Found existing matching element
    # Not found, create it
    new_element = ET.SubElement(parent_element, tag_name, attrib=attributes)
    new_element.text = text
    return new_element

def add_dependency_to_package_xml(root: ET.Element, dep_name: str, dep_type: str = "depend"):
    """Adds a dependency if a similar one doesn't already exist. Prioritizes <depend> if other types exist."""
    existing_dep_tags = root.findall(dep_type)
    for tag in existing_dep_tags:
        if tag.text == dep_name:
            return # Already exists with this exact type
    new_dep = ET.Element(dep_type)
    new_dep.text = dep_name
    # Insert after the last dependency tag or other common tags like <license>
    insert_after_tags = ['description', 'maintainer', 'license', 'url', 'author', 
                         'depend', 'build_depend', 'build_export_depend', 'exec_depend', 
                         'test_depend', 'doc_depend', 'buildtool_depend']
    last_relevant_element = None
    for tag_name_to_check in reversed(insert_after_tags):
        elements = root.findall(tag_name_to_check)
        if elements:
            last_relevant_element = elements[-1]
            break
    if last_relevant_element is not None:
        parent_map = {c:p for p in root.iter() for c in p}
        parent_of_last = parent_map.get(last_relevant_element)
        if parent_of_last is not None:
            index = list(parent_of_last).index(last_relevant_element) + 1
            parent_of_last.insert(index, new_dep)
        else:
            root.append(new_dep)
    else:
        root.append(new_dep)

def update_package_xml_for_new_interface(package_xml_path: Path, iface_def: InterfaceFileDefinition) -> bool:
    try:
        tree = ET.parse(str(package_xml_path))
        root = tree.getroot()
        # 1. Ensure <buildtool_depend>rosidl_default_generators</buildtool_depend>
        add_dependency_to_package_xml(root, "rosidl_default_generators", "buildtool_depend")
        # 2. Ensure <exec_depend>rosidl_default_runtime</exec_depend>
        add_dependency_to_package_xml(root, "rosidl_default_runtime", "exec_depend")
        # 3. Add interface dependencies from iface_def
        for dep_name in iface_def.interface_package_dependencies:
            add_dependency_to_package_xml(root, dep_name, "depend")
        # 4. Ensure <export><member_of_group>rosidl_interface_packages</member_of_group></export>
        export_tag = root.find("export")
        if export_tag is None:
            export_tag = ET.SubElement(root, "export")
        ensure_element_with_text(export_tag, "member_of_group", "rosidl_interface_packages")
        ET.indent(tree, space="  ", level=0)
        tree.write(str(package_xml_path), encoding="utf-8", xml_declaration=True)
        return True
    except ET.ParseError as e:
        print(f"Error parsing {package_xml_path}: {e}")
        return False
    except Exception as e:
        print(f"Error updating {package_xml_path}: {e}")
        return False
