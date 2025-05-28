# rosbuddy/file_generators/cmake_generator.py
import textwrap
import os # For os.path.join
from typing import List
from rosbuddy.data_models.package_config import PackageConfig, Dependency, ExecutableTarget, LibraryTarget
# LaunchConfiguration might be needed if installing launch files with specific content knowledge
from rosbuddy.data_models.launch_config import LaunchConfiguration


def _generate_targets_code(config: PackageConfig) -> List[str]:
    lines = []
    if not config.library_targets and not config.executable_targets:
        lines.append("# No C++ library or executable targets defined.")
        return lines

    # Libraries
    for lib_target in config.library_targets:
        lines.append(f"\n# Library: {lib_target.name}")
        sources_str = " ".join(lib_target.sources)
        lines.append(f"add_library({lib_target.name} {sources_str})")
        if lib_target.linked_libraries:
            link_libs_str = " ".join(lib_target.linked_libraries)
            lines.append(f"target_link_libraries({lib_target.name} PUBLIC {link_libs_str})") # Or PRIVATE/INTERFACE
        # Could add ament_target_dependencies here too if deps are specific ROS packages
        # For now, assuming linked_libraries contains direct CMake target names or find_package results

    # Executables
    for exec_target in config.executable_targets:
        lines.append(f"\n# Executable: {exec_target.name}")
        sources_str = " ".join(exec_target.sources)
        lines.append(f"add_executable({exec_target.name} {sources_str})")
        
        # Use ament_target_dependencies for ROS packages, target_link_libraries for others
        ros_deps_for_target = []
        other_libs_for_target = []

        # Add project's own libraries first if specified
        for lib_name in exec_target.linked_libraries:
            is_project_lib = any(proj_lib.name == lib_name for proj_lib in config.library_targets)
            if is_project_lib:
                other_libs_for_target.append(lib_name) 
            else: # Assume it's a ROS dependency or system lib
                # This logic could be smarter: check if lib_name matches a find_package'd name
                is_found_package = any(dep.name == lib_name for dep in config.dependencies)
                if is_found_package:
                     ros_deps_for_target.append(lib_name)
                else: # Assume it's a system library or pre-compiled lib
                    other_libs_for_target.append(lib_name)


        if ros_deps_for_target:
            lines.append(f"ament_target_dependencies({exec_target.name} {' '.join(ros_deps_for_target)})")
        if other_libs_for_target: # Link other libraries (e.g. project's own libs, system libs)
            lines.append(f"target_link_libraries({exec_target.name} PRIVATE {' '.join(other_libs_for_target)})")


    return lines

def _generate_install_rules_code(config: PackageConfig) -> List[str]:
    lines = [""]
    lines.append("# Install rules")

    # Install executables and libraries
    install_targets = []
    for lib_target in config.library_targets:
        install_targets.append(lib_target.name)
    for exec_target in config.executable_targets:
        install_targets.append(exec_target.name)

    if install_targets:
        lines.append("install(TARGETS")
        for target_name in install_targets:
            lines.append(f"  {target_name}")
        lines.append("  ARCHIVE DESTINATION lib") # For static libraries
        lines.append("  LIBRARY DESTINATION lib") # For shared libraries
        lines.append("  RUNTIME DESTINATION lib/${PROJECT_NAME} # For executables")
        lines.append(")")

    # Install launch files
    # Uses config.launch_configurations (list of LaunchConfiguration objects)
    if config.launch_configurations:
        lines.append("\n# Install launch files")
        # Assuming launch files are in a 'launch' directory at the package root
        # And lc.file_name is just the basename like "my.launch.py"
        launch_files_to_install = [os.path.join("launch", lc.file_name) for lc in config.launch_configurations]
        if launch_files_to_install:
            lines.append("install(DIRECTORY")
            lines.append("  launch") # Source directory relative to CMakeLists.txt
            lines.append("  DESTINATION share/${PROJECT_NAME}")
            lines.append(")")
            # Alternative for specific files if not all in launch/ dir:
            # lines.append("install(FILES")
            # for lf_path in launch_files_to_install:
            #    lines.append(f"  {lf_path}") # Path relative to CMakeLists.txt
            # lines.append("  DESTINATION share/${PROJECT_NAME}/launch")
            # lines.append(")")


    # Install config files
    # Uses config.config_files_paths (list of strings like "config/my_params.yaml")
    if config.config_files_paths:
        lines.append("\n# Install config files")
        config_files_to_install = [os.path.join("config", os.path.basename(p)) for p in config.config_files_paths]
        if config_files_to_install: # Ensure there are files to install
            lines.append("install(DIRECTORY")
            lines.append("  config") # Source directory relative to CMakeLists.txt
            lines.append("  DESTINATION share/${PROJECT_NAME}")
            lines.append(")")
            # Alternative for specific files:
            # lines.append("install(FILES")
            # for cf_path in config_files_to_install: # These should be relative to CMakeLists.txt
            #    lines.append(f"  {cf_path}")
            # lines.append("  DESTINATION share/${PROJECT_NAME}/config")
            # lines.append(")")


    # Install package.xml (already handled by ament_package(), but explicit can be added if needed)
    # install(FILES package.xml DESTINATION share/${PROJECT_NAME})

    return lines


def generate_cmake_lists_content(config: PackageConfig) -> str:
    if config.build_type != "ament_cmake":
        return "# This package is not configured as ament_cmake."

    project_name = config.name
    has_interfaces = bool(config.interface_files)

    lines = [
        f"cmake_minimum_required(VERSION 3.8)",
        f"project({project_name})",
        "",
        "if(NOT CMAKE_CXX_STANDARD)",
        "  set(CMAKE_CXX_STANDARD 17)",
        "endif()",
        "",
        "if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES \"Clang\")",
        "  add_compile_options(-Wall -Wextra -Wpedantic)",
        "endif()",
        "",
        "find_package(ament_cmake REQUIRED)",
    ]

    cmake_dependencies_to_find = set()
    # Add rosidl_default_generators if interfaces are present and not already a dep
    if has_interfaces:
        is_rosidl_dep_already = any(dep.name == "rosidl_default_generators" for dep in config.dependencies)
        if not is_rosidl_dep_already:
            cmake_dependencies_to_find.add("rosidl_default_generators")


    for dep in config.dependencies:
        if dep.dep_type in ["depend", "build_depend", "build_export_depend"]:
            if dep.name not in ["ament_cmake"]: 
                 cmake_dependencies_to_find.add(dep.name)
    
    if cmake_dependencies_to_find:
        lines.append("")
        lines.append("# Find direct dependencies")
        for dep_name in sorted(list(cmake_dependencies_to_find)):
            # If it's rosidl_default_generators, it's always REQUIRED for interface gen
            required_keyword = "REQUIRED" if dep_name == "rosidl_default_generators" else "REQUIRED" # Or "OPTIONAL" for some
            lines.append(f"find_package({dep_name} {required_keyword})")
    
    target_lines = _generate_targets_code(config)
    if target_lines and target_lines[0] != "# No C++ library or executable targets defined.":
        lines.extend(target_lines)

    # Interface generation section
    lines.append("\n# Interface Generation")
    if has_interfaces:
        lines.append("# Ensure rosidl_default_generators was found (added above)")
        interface_file_list_str = '"\n#    "'.join([f.replace("\\", "/") for f in config.interface_files]) # CMake paths use /
        lines.append(f"# TODO: Uncomment and verify/complete the rosidl_generate_interfaces call:")
        lines.append(f"# rosidl_generate_interfaces(${{PROJECT_NAME}}")
        lines.append(f'#   "{interface_file_list_str}"')
        lines.append(f"#   # DEPENDENCIES std_msgs # Add other msg/srv/action packages your interfaces depend on")
        lines.append(f"# )")
        lines.append("# TODO: Also ensure targets that USE these interfaces link against them, e.g.:")
        lines.append("# ament_target_dependencies(my_node ${PROJECT_NAME}__rosidl_typesupport_cpp)")
    else:
        lines.append("# No interface files defined in PackageConfig.")
    
    lines.extend(_generate_install_rules_code(config))

    lines.extend([
        "",
        "if(BUILD_TESTING)",
        "  find_package(ament_lint_auto REQUIRED)",
        "  ament_lint_auto_find_test_dependencies()",
        "endif()",
        "",
        "ament_package()"
    ])

    return "\n".join(lines)