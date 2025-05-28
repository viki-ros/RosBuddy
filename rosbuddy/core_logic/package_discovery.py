# rosbuddy/core_logic/package_discovery.py
import pathlib
import xml.etree.ElementTree as ET
import os
from typing import List, Dict, Any, Optional, Tuple
import logging # Add this

# Add a module-level logger
logger_pd = logging.getLogger(__name__)
class PackageInfo:
    """Basic information about a discovered ROS 2 package."""
    def __init__(self, name: str, path: pathlib.Path, build_type: str):
        self.name = name
        self.path = path # Absolute path to the package root
        self.build_type = build_type
        self.executables: List[str] = [] # List of executable names (e.g., 'my_node')
        self.launch_files: List[str] = [] # List of launch file names (e.g., 'start_robot.launch.py')

    def __repr__(self):
        return f"PackageInfo(name='{self.name}', path='{self.path.name}', build_type='{self.build_type}')"

class PackageDiscovery:
    """
    Discovers ROS 2 packages within a given workspace and extracts basic information
    about their executables and launch files.
    """
    def __init__(self, workspace_manager: 'WorkspaceManager'): # Expects WorkspaceManager instance
        self.workspace_manager = workspace_manager

    def find_packages_in_active_workspace(self) -> List[PackageInfo]:
        """
        Scans the active workspace's 'src' directory for ROS 2 packages.
        Returns a list of PackageInfo objects.
        """
        active_ws_src_path = self.workspace_manager.get_active_workspace_src_path()
        if not active_ws_src_path or not active_ws_src_path.is_dir():
            logger_pd.info(f"No active workspace 'src' directory found at {active_ws_src_path}, or it's not a directory.")
            return []

        discovered_packages: List[PackageInfo] = []

        # colcon works with symlinked src directories too. For simplicity, we just list direct subdirs.
        for item in active_ws_src_path.iterdir():
            if item.is_dir():
                package_xml_path = item / "package.xml"
                if package_xml_path.is_file():
                    try:
                        tree = ET.parse(package_xml_path)
                        root = tree.getroot()
                        package_name = root.find('name').text
                        build_type_element = root.find(".//build_type") # Find build_type within <export>
                        build_type = build_type_element.text if build_type_element is not None else "Unknown"
                        
                        pkg_info = PackageInfo(package_name, item, build_type)
                        
                        # Populate executables and launch files
                        self._populate_executables(pkg_info)
                        self._populate_launch_files(pkg_info)

                        discovered_packages.append(pkg_info)
                    except Exception as e:
                        logger_pd.warning(f"Could not parse package.xml for '{item.name}': {e}", exc_info=True)
        
        # Sort packages by name for consistent display
        return sorted(discovered_packages, key=lambda p: p.name.lower())

    def _populate_executables(self, pkg_info: PackageInfo):
        """
        Populates the executables list for a PackageInfo object.
        Initial approach: Scan Python packages' setup.py for console_scripts.
        Future: Parse CMakeLists.txt for add_executable.
        """
        if pkg_info.build_type == "ament_python":
            setup_py_path = pkg_info.path / "setup.py"
            if setup_py_path.is_file():
                # This is tricky: parsing setup.py without executing it is hard.
                # The safest way is to use AST or regex, but fragile.
                # For a functional prototype, we might simplify or assume structure.
                # A common hack: grep for 'console_scripts' entry_points
                # For now, let's just assume a 'hello_world' executable if it's there
                # and provide a placeholder for proper parsing.
                
                # A simple heuristic: check for a common hello_world node name
                # This is unreliable in general, but demonstrates intent for prototype
                python_pkg_module_path = pkg_info.path / pkg_info.name # e.g., my_pkg/my_pkg/
                if python_pkg_module_path.is_dir():
                    for py_file in python_pkg_module_path.iterdir():
                        if py_file.is_file() and py_file.suffix == '.py' and py_file.stem != '__init__':
                            # Check if 'main()' function is in the file (very basic check)
                            try:
                                with open(py_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                if "def main(args=None):" in content: # Simple heuristic
                                    # Executable name is usually the stem of the file or entry point name
                                    # For hello_world_node.py, the entry point is 'hello_world'
                                    if "hello_world_node" in py_file.stem:
                                        pkg_info.executables.append("hello_world")
                                    else:
                                        pkg_info.executables.append(py_file.stem) # Fallback to filename
                            except Exception as e:
                                logger_pd.warning(f"Could not read Python file {py_file} for executables in package {pkg_info.name}: {e}")
            else:
                logger_pd.debug(f"Python package '{pkg_info.name}' is missing setup.py (this is normal for some packages).")
        
        # TODO: For ament_cmake, parse CMakeLists.txt for add_executable
        elif pkg_info.build_type == "ament_cmake":
            # For now, just add a placeholder if we know one exists from our scaffold
            if "hello_world_node" in pkg_info.name: # e.g. if we created 'my_cpp_hello_world_node'
                pkg_info.executables.append("my_cpp_node") # Placeholder executable name
            # Real implementation would parse CMakeLists.txt
            # e.g., use regex on CMakeLists.txt content: re.findall(r'add_executable\((.*?)\s', cmake_content)
        
        # Ensure unique executables
        pkg_info.executables = sorted(list(set(pkg_info.executables)))


    def _populate_launch_files(self, pkg_info: PackageInfo):
        """
        Populates the launch_files list for a PackageInfo object.
        Scans the 'launch' subdirectory.
        """
        launch_dir = pkg_info.path / "launch"
        if launch_dir.is_dir():
            for item in launch_dir.iterdir():
                if item.is_file() and item.suffix in ['.py', '.xml', '.yaml']:
                    if item.name.endswith(('.launch.py', '.launch.xml', '.launch.yaml')):
                        pkg_info.launch_files.append(item.name)
            pkg_info.launch_files.sort() # Sort for consistent order