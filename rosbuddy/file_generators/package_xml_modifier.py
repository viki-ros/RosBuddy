from pathlib import Path
from typing import Optional, Dict, List
import xml.etree.ElementTree as ET
from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
import logging

logger = logging.getLogger(__name__)

def add_dependency_to_package_xml(package_xml_path: Path, dep_name: str, dep_type: str = "depend") -> bool:
    """
    Adds a new dependency to package.xml. This is a higher-level function that handles file operations.
    """
    try:
        tree = ET.parse(str(package_xml_path))
        root = tree.getroot()
        add_unique_dependency_to_package_xml(root, dep_name, dep_type)
        tree.write(str(package_xml_path), encoding="utf-8", xml_declaration=True)
        return True
    except Exception as e:
        logger.error(f"Error adding dependency to package.xml: {e}", exc_info=True)
        return False

def ensure_element_with_text(
    parent_element: ET.Element,
    tag_name: str,
    text: Optional[str], # Text can be None for self-closing tags if needed, but here it's usually present
    attributes: Optional[Dict[str, str]] = None,
    ensure_unique_within_parent: bool = True # If True, only adds if no exact match found
) -> ET.Element:
    """
    Finds or creates/appends a child element with specific tag name, text, and attributes.
    Returns the found or created element.
    If ensure_unique_within_parent is True, it won't create a new element if an exact match already exists.
    """
    if attributes is None:
        attributes = {}
    # Construct XPath query for attributes
    attr_predicates = []
    if attributes:
        for k, v in attributes.items():
            # Escape attribute values for XPath, especially quotes
            escaped_v = v.replace("'", "&apos;").replace('"', "&quot;")
            attr_predicates.append(f"@{k}='{escaped_v}'")

    if ensure_unique_within_parent:
        # More robust check for existing elements
        for child in parent_element.findall(tag_name):
            text_match = (child.text == text) if text is not None else (child.text is None)
            if not text_match:
                continue

            attrs_match = True
            # Check if all provided attributes match
            for attr_k, attr_v in attributes.items():
                if child.get(attr_k) != attr_v:
                    attrs_match = False
                    break
            # Stricter check: ensure the child doesn't have *more* attributes than specified
            if attrs_match and len(child.attrib) != len(attributes):
                attrs_match = False

            if attrs_match: # Found an existing element that matches
                logger.debug(f"Found existing element: <{tag_name}> with text '{text}' and attributes {attributes}")
                return child
    
    # No exact match found (or uniqueness not enforced), create a new element
    logger.debug(f"Creating new element: <{tag_name}> with text '{text}' and attributes {attributes}")
    new_element = ET.SubElement(parent_element, tag_name, attrib=attributes)
    if text is not None:
        new_element.text = text
    return new_element

def add_unique_dependency_to_package_xml(
    root: ET.Element,
    dep_name: str,
    dep_type: str = "depend"
):
    """
    Adds a dependency tag of a specific type if an identical one (name and type)
    doesn't already exist. Tries to insert it logically.
    """
    # Check for existing identical dependency
    for child in root.findall(dep_type):
        if child.text == dep_name:
            logger.debug(f"Dependency {dep_type}: {dep_name} already exists.")
            return  # Already exists

    # Create the new dependency element
    new_dep_element = ET.Element(dep_type)
    new_dep_element.text = dep_name

    # --- Logical Insertion ---
    # Order of preference for finding the "last tag of a certain kind" to insert after:
    insert_after_tags = [
        'buildtool_depend',  # First check if there are any buildtool_depends
        'depend',            # Then regular depends
        'build_depend',      # Then specific depends
        'build_export_depend',
        'exec_depend',
        'test_depend',
                'doc_depend',
        'description',       # Fall back to common required tags
        'version',
        'name'
    ]
    last_relevant_element = None
    insertion_point_found = False

    # Try to find a logical insertion point
    for tag_name_to_check in reversed(insert_after_tags):
        elements = root.findall(tag_name_to_check)
        if elements:  # Find the last one of this specific tag type
            last_relevant_element = elements[-1]
            try:
                index = list(root).index(last_relevant_element) + 1
                root.insert(index, new_dep_element)
                insertion_point_found = True
                logger.debug(f"Inserted dependency {dep_type}: {dep_name} after last <{tag_name_to_check}>")
                break
            except ValueError:
                logger.warning(f"Element <{tag_name_to_check}> found but not a direct child of root. This is unexpected.")
                pass  # Fall through

    if not insertion_point_found:
        # Fallback: append after <export> or before <test_depend> or just append
        test_depends = root.findall('test_depend')
        if test_depends:
            try:
                index = list(root).index(test_depends[0])
                root.insert(index, new_dep_element)
                logger.debug(f"Inserted dependency {dep_type}: {dep_name} before first <test_depend>")
            except ValueError:
                root.append(new_dep_element)
                logger.debug(f"Appended dependency {dep_type}: {dep_name} (fallback)")
        else:
            root.append(new_dep_element)
            logger.debug(f"Appended dependency {dep_type}: {dep_name} (fallback)")

def update_package_xml_for_new_interface(package_xml_path: Path, rosidl_deps: List[str]) -> bool:
    logger.info(f"Attempting to update {package_xml_path} for new interface")
    try:
        # Using a parser that might preserve comments/PIs is complex with standard ET.
        # For now, we accept that comments might be lost or formatting changed.
        # lxml is a good alternative for preserving more of the original XML structure.
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False, insert_pis=False))
        try:
            tree = ET.parse(str(package_xml_path), parser=parser)
        except ET.ParseError as pe: # Catch parsing error specifically
            logger.error(f"XML ParseError in {package_xml_path}: {pe}", exc_info=True)
            return False

        root = tree.getroot()

        # 1. Ensure <buildtool_depend>rosidl_default_generators</buildtool_depend>
        add_dependency_to_package_xml(root, "rosidl_default_generators", "buildtool_depend")
        
        # 2. Ensure <exec_depend>rosidl_default_runtime</exec_depend>
        add_dependency_to_package_xml(root, "rosidl_default_runtime", "exec_depend")

        # 3. Add interface dependencies from iface_def
        for dep_name in rosidl_deps:
            add_unique_dependency_to_package_xml(root, dep_name, "depend") # Using <depend>

        # 4. Ensure <export><member_of_group>rosidl_interface_packages</member_of_group></export>
        export_tag_list = root.findall("export") # findall returns a list
        if not export_tag_list: # No <export> tag exists
            logger.debug(f"No <export> tag found in {package_xml_path}. Creating one.")
            export_tag = ET.SubElement(root, "export")
            # Try to place it before test_depends if they exist
            test_depend_first = root.find("test_depend")
            if test_depend_first is not None:
                root.insert(list(root).index(test_depend_first), export_tag)
            else: # No test_depends, try to insert after last dependency-like tag
                dep_like_tags = ['depend', 'build_depend', 'build_export_depend', 'exec_depend', 'buildtool_depend']
                last_dep_like_element = None
                for tag_name_to_check in reversed(dep_like_tags): # Check in reverse order of typical appearance
                    elements = root.findall(tag_name_to_check)
                    if elements:
                        last_dep_like_element = elements[-1]
                        root.insert(list(root).index(last_dep_like_element) + 1, export_tag)
                        break
                if last_dep_like_element is None: # Fallback: append if no deps found (already appended by SubElement if root was empty)
                    pass # Already appended by SubElement if root had no children to insert before/after
        else:
            export_tag = export_tag_list[0] # Use the first <export> tag found
            logger.debug(f"Found existing <export> tag in {package_xml_path}.")

        ensure_element_with_text(export_tag, "member_of_group", "rosidl_interface_packages")

        # Make the XML output more human-readable.
        # ET.indent is available in Python 3.9+
        if hasattr(ET, 'indent'):
            ET.indent(tree, space="  ", level=0)
        else:
            logger.warning("ET.indent not available (requires Python 3.9+). XML output will not be pretty-printed by default.")
            
        tree.write(str(package_xml_path), encoding="utf-8", xml_declaration=True)
        logger.info(f"Successfully updated {package_xml_path} for new interface")
        return True
        
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error updating {package_xml_path} for new interface", exc_info=True)
        return False
