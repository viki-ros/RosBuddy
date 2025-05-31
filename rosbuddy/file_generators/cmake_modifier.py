# rosbuddy/file_generators/cmake_modifier.py
import re
from pathlib import Path
from typing import List
from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class CMakeUpdateStatus(Enum):
    UPDATED = "updated"
    NO_CHANGES = "no_changes"
    ERROR = "error"

def _ensure_find_package(lines: List[str], package_name: str) -> bool:
    """
    Ensures a find_package call for the given package_name exists.
    Returns True if changes were made, False otherwise.
    """
    find_package_pattern = re.compile(rf'^\s*find_package\(\s*{re.escape(package_name)}(\s+|\s+REQUIRED\s*)\)', re.IGNORECASE)
    if any(find_package_pattern.search(line) for line in lines):
        return False # Already exists

    # Try to insert after ament_cmake or other find_package calls
    insert_index = -1
    ament_cmake_pattern = re.compile(r'^\s*find_package\(\s*ament_cmake\s+REQUIRED\s*\)', re.IGNORECASE)
    last_find_package_idx = -1

    for i, line in enumerate(lines):
        if ament_cmake_pattern.search(line):
            insert_index = i + 1
            break
        if re.search(r'^\s*find_package\(', line, re.IGNORECASE):
            last_find_package_idx = i

    if insert_index == -1 and last_find_package_idx != -1:
        insert_index = last_find_package_idx + 1
    elif insert_index == -1: # Fallback: insert before common target definitions or ament_package
        for i, line in enumerate(lines):
            if re.search(r'^\s*(add_library|add_executable|rosidl_generate_interfaces|ament_package)\(', line, re.IGNORECASE):
                insert_index = i
                break
        if insert_index == -1: # Absolute fallback: end of file before ament_package or just append
            for i, line in enumerate(lines):
                if re.search(r'^\s*ament_package\(\s*\)', line, re.IGNORECASE):
                    insert_index = i
                    break
            if insert_index == -1:
                lines.append(f"find_package({package_name} REQUIRED)")
                return True

    lines.insert(insert_index, f"find_package({package_name} REQUIRED)\n")
    return True

def update_cmakelists_for_new_interface(cmakelists_path: Path, iface_def: InterfaceFileDefinition, project_name: str) -> CMakeUpdateStatus:
    try:
        with open(cmakelists_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        original_lines = list(lines) # Keep a copy for comparison

        # 1. Ensure find_package for rosidl_default_generators and interface dependencies
        _ensure_find_package(lines, "rosidl_default_generators")
        for dep_name in iface_def.interface_package_dependencies:
            _ensure_find_package(lines, dep_name)

        # 2. Modify or add rosidl_generate_interfaces
        # Regex to find rosidl_generate_interfaces call, allowing for ${PROJECT_NAME} or the actual project_name
        # Escaping project_name in case it contains special regex characters (unlikely but safe)
        rosidl_call_pattern = re.compile(
            rf'^\s*rosidl_generate_interfaces\s*\(\s*({re.escape(project_name)}|\${{PROJECT_NAME}})\s*',
            re.IGNORECASE
        )
        rosidl_call_start_idx = -1
        rosidl_call_end_idx = -1
        paren_balance = 0

        for i, line in enumerate(lines):
            if rosidl_call_start_idx == -1 and rosidl_call_pattern.search(line):
                rosidl_call_start_idx = i
            
            if rosidl_call_start_idx != -1:
                paren_balance += line.count('(')
                paren_balance -= line.count(')')
                if paren_balance == 0 and rosidl_call_start_idx <= i : # Found the block
                    rosidl_call_end_idx = i
                    break
        
        new_interface_line = f'  "{iface_def.relative_path}"'

        if rosidl_call_start_idx != -1 and rosidl_call_end_idx != -1:
            # Modify existing call
            block_lines = lines[rosidl_call_start_idx : rosidl_call_end_idx + 1]
            
            # Add the new interface file
            # Insert before DEPENDENCIES or before the closing parenthesis
            inserted_file = False
            for i in range(len(block_lines) -1, -1, -1): # Iterate backwards
                if re.search(r'^\s*DEPENDENCIES', block_lines[i], re.IGNORECASE) or \
                   (i == len(block_lines) - 1 and block_lines[i].strip().endswith(')')):
                    # Check if file already listed (unlikely for new add, but good practice)
                    if not any(iface_def.relative_path in line for line in block_lines):
                        block_lines.insert(i, new_interface_line + '\n')
                    inserted_file = True
                    break
            if not inserted_file and not any(iface_def.relative_path in line for line in block_lines): # Failsafe if no clear spot
                 block_lines.insert(len(block_lines)-1, new_interface_line + '\n')


            # Add dependencies
            if iface_def.interface_package_dependencies:
                deps_keyword_idx = -1
                for i, line in enumerate(block_lines):
                    if re.search(r'^\s*DEPENDENCIES', line, re.IGNORECASE):
                        deps_keyword_idx = i
                        break
                
                if deps_keyword_idx != -1:
                    existing_deps_match = re.search(r'DEPENDENCIES\s+(.*?)(\)|\s*$)', block_lines[deps_keyword_idx], re.IGNORECASE)
                    current_deps_str = existing_deps_match.group(1).strip() if existing_deps_match else ""
                    current_deps_list = [d.strip() for d in current_deps_str.split() if d.strip()]
                    
                    for new_dep in iface_def.interface_package_dependencies:
                        if new_dep not in current_deps_list:
                            current_deps_list.append(new_dep)
                    
                    block_lines[deps_keyword_idx] = f"  DEPENDENCIES {' '.join(sorted(current_deps_list))}\n" # Ensure sorted, ends with newline
                    if not block_lines[deps_keyword_idx].strip().endswith(")"): # if it was the last line
                        if not block_lines[deps_keyword_idx].endswith("\n"): block_lines[deps_keyword_idx] += "\n"
                else: # No DEPENDENCIES keyword, add it
                    deps_str = " ".join(sorted(iface_def.interface_package_dependencies))
                    # Insert before the closing parenthesis of the rosidl_generate_interfaces call
                    block_lines.insert(len(block_lines)-1, f"  DEPENDENCIES {deps_str}\n")

            lines = lines[:rosidl_call_start_idx] + block_lines + lines[rosidl_call_end_idx+1:]
        else:
            # Add new rosidl_generate_interfaces call
            new_call_list = []
            new_call_list.append(f"rosidl_generate_interfaces(${{PROJECT_NAME}}\n")
            new_call_list.append(f'  "{iface_def.relative_path}"\n')
            if iface_def.interface_package_dependencies:
                deps_str = " ".join(sorted(iface_def.interface_package_dependencies))
                new_call_list.append(f"  DEPENDENCIES {deps_str}\n")
            new_call_list.append(")\n")
            
            # Insert before ament_package() or common install rules
            insert_before_ament_pkg_idx = len(lines)
            for i, line in enumerate(lines):
                if re.search(r'^\s*ament_package\(\s*\)', line, re.IGNORECASE):
                    insert_before_ament_pkg_idx = i
                    break
            lines = lines[:insert_before_ament_pkg_idx] + new_call_list + lines[insert_before_ament_pkg_idx:]

        if lines != original_lines:
            with open(cmakelists_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return CMakeUpdateStatus.UPDATED
        return CMakeUpdateStatus.NO_CHANGES
    except Exception as e:
        logger.error(f"Error updating {cmakelists_path}: {e}", exc_info=True)
        return CMakeUpdateStatus.ERROR

def add_cpp_node_to_cmakelists(cmakelists_path: Path, node_name: str, sources: List[str]) -> bool:
    """
    Adds a new C++ node executable to CMakeLists.txt.
    Returns True if successful, False otherwise.

    Args:
        cmakelists_path: Path to CMakeLists.txt
        node_name: Name of the node executable
        sources: List of source files (relative to package root)
    """
    try:
        with open(cmakelists_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        original_lines = list(lines)  # Keep a copy for comparison

        # 1. Ensure required find_package calls
        _ensure_find_package(lines, "rclcpp")

        # 2. Find the right spot to add the new executable
        # Try to group with other add_executable calls, or before install rules/ament_package
        insert_index = -1
        last_executable_idx = -1
        last_library_idx = -1

        for i, line in enumerate(lines):
            if re.search(r'^\s*add_executable\(', line, re.IGNORECASE):
                last_executable_idx = i
            elif re.search(r'^\s*add_library\(', line, re.IGNORECASE):
                last_library_idx = i
            elif re.search(r'^\s*(install\(|ament_package\()', line, re.IGNORECASE):
                if insert_index == -1:  # Haven't found a spot yet
                    insert_index = i

        # Prefer grouping with other executables
        if last_executable_idx != -1:
            # Find the end of the executable block
            i = last_executable_idx + 1
            while i < len(lines) and not re.search(r'^\s*(add_library|install|ament_package)\(', lines[i], re.IGNORECASE):
                if re.search(r'^\s*add_executable\(', lines[i], re.IGNORECASE):
                    last_executable_idx = i
                i += 1
            insert_index = last_executable_idx + 1
        elif last_library_idx != -1:
            # Place after libraries if no executables exist
            i = last_library_idx + 1
            while i < len(lines) and not re.search(r'^\s*(install|ament_package)\(', lines[i], re.IGNORECASE):
                if re.search(r'^\s*add_library\(', lines[i], re.IGNORECASE):
                    last_library_idx = i
                i += 1
            insert_index = last_library_idx + 1

        if insert_index == -1:
            # Fallback: insert before ament_package()
            for i, line in enumerate(lines):
                if re.search(r'^\s*ament_package\(\s*\)', line, re.IGNORECASE):
                    insert_index = i
                    break
            if insert_index == -1:
                insert_index = len(lines)  # Append to end if no ament_package found

        # 3. Generate and insert the new executable block
        new_lines = [
            "\n# Node executable\n",
            f"add_executable({node_name} {' '.join(sources)})\n",
            f"ament_target_dependencies({node_name} rclcpp)\n"
        ]

        lines[insert_index:insert_index] = new_lines

        # 4. Update install rules if they exist
        install_start = -1
        for i, line in enumerate(lines):
            if re.search(r'^\s*install\(\s*TARGETS', line, re.IGNORECASE):
                install_start = i
                break

        if install_start != -1:
            # Find the end of the install block
            install_end = install_start
            for i in range(install_start, len(lines)):
                if lines[i].strip() == ')':
                    install_end = i
                    break

            # Check if the target is already listed
            target_lines = lines[install_start + 1:install_end]
            if not any(re.search(rf'^\s*{re.escape(node_name)}\s*$', line) for line in target_lines):
                # Add the new target to the install block
                lines.insert(install_end, f"  {node_name}\n")
        else:
            # Create a new install block for the executable
            install_lines = [
                "\n# Install targets\n",
                "install(TARGETS\n",
                f"  {node_name}\n",
                "  DESTINATION lib/${PROJECT_NAME}\n",
                ")\n"
            ]
            lines.insert(insert_index + len(new_lines), '\n'.join(install_lines))

        if lines != original_lines:
            with open(cmakelists_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False  # No changes made

    except Exception as e:
        logger.error(f"Error updating CMakeLists.txt for node {node_name}: {e}", exc_info=True)
        return False

def update_cmakelists_for_new_cpp_node(
    cmake_path: Path,
    pkg_name: str,
    node_name: str,
    class_name: str,
    additional_message_dependencies: list
) -> bool:
    """
    Updates CMakeLists.txt to add a new standalone C++ node executable, link dependencies, and install headers.
    """
    try:
        with open(cmake_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        original_lines = list(lines)

        # Ensure find_package(ament_cmake REQUIRED)
        _ensure_find_package(lines, "ament_cmake")
        # Ensure find_package(rclcpp REQUIRED)
        _ensure_find_package(lines, "rclcpp")
        # Ensure find_package for each message dependency
        for dep in additional_message_dependencies:
            _ensure_find_package(lines, dep)

        # Add include_directories(include) if not present
        if not any(re.match(r'^\s*include_directories\(\s*include\s*\)', l) for l in lines):
            # Insert after find_package or at the top
            insert_idx = 0
            for i, l in enumerate(lines):
                if l.strip().startswith('find_package'):
                    insert_idx = i + 1
            lines.insert(insert_idx, 'include_directories(include)\n')

        # Add add_executable
        exe_line = f"add_executable({node_name}_exe src/{node_name}.cpp)\n"
        if not any(exe_line.strip() in l for l in lines):
            # Insert before ament_package or at end
            insert_idx = len(lines)
            for i, l in enumerate(lines):
                if re.match(r'^\s*ament_package\(\s*\)', l):
                    insert_idx = i
                    break
            lines.insert(insert_idx, '\n# Node executable\n' + exe_line)

        # Add ament_target_dependencies
        dep_line = f"ament_target_dependencies({node_name}_exe rclcpp {' '.join(additional_message_dependencies)})\n"
        if not any(dep_line.strip() in l for l in lines):
            # Insert after add_executable
            for i, l in enumerate(lines):
                if exe_line.strip() in l:
                    lines.insert(i + 1, dep_line)
                    break

        # Add install(TARGETS ...)
        install_targets_pattern = re.compile(r'^\s*install\(\s*TARGETS', re.IGNORECASE)
        found_install_targets = False
        for i, l in enumerate(lines):
            if install_targets_pattern.match(l):
                found_install_targets = True
                # Insert node_name_exe if not present
                block_end = i
                for j in range(i + 1, len(lines)):
                    if ')' in lines[j]:
                        block_end = j
                        break
                if not any(f"{node_name}_exe" in lines[j] for j in range(i, block_end)):
                    lines.insert(block_end, f"  {node_name}_exe\n")
                break
        if not found_install_targets:
            # Add a new install block
            install_block = [
                '\n# Install targets\n',
                'install(TARGETS\n',
                f'  {node_name}_exe\n',
                '  DESTINATION lib/${PROJECT_NAME}\n',
                ')\n'
            ]
            # Insert before ament_package
            insert_idx = len(lines)
            for i, l in enumerate(lines):
                if re.match(r'^\s*ament_package\(\s*\)', l):
                    insert_idx = i
                    break
            lines[insert_idx:insert_idx] = install_block

        # Add install headers
        install_headers_line = 'install(DIRECTORY include/ DESTINATION include FILES_MATCHING PATTERN "*.hpp")\n'
        if not any('install(DIRECTORY include/' in l and 'PATTERN "*.hpp"' in l for l in lines):
            # Insert before ament_package
            insert_idx = len(lines)
            for i, l in enumerate(lines):
                if re.match(r'^\s*ament_package\(\s*\)', l):
                    insert_idx = i
                    break
            lines.insert(insert_idx, install_headers_line)

        if lines != original_lines:
            with open(cmake_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating {cmake_path}: {e}", exc_info=True)
        return False