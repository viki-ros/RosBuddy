# rosbuddy/data_models/package_config.py
from typing import List, Dict, Any, Optional
# This import assumes launch_config.py is in the same directory (data_models)
# and that data_models/__init__.py correctly exports LaunchConfiguration or
# you import directly from .launch_config
from .launch_config import LaunchConfiguration 

class Dependency:
    """Represents a single dependency in package.xml."""
    VALID_TYPES = [
        "depend",  # Generic dependency, implies build, export, and run
        "build_depend",
        "build_export_depend",
        "exec_depend",
        "test_depend",
        "doc_depend",
        "buildtool_depend"
    ]

    def __init__(self, name: str, dep_type: str = "depend", version_lt: Optional[str] = None,
                 version_lte: Optional[str] = None, version_eq: Optional[str] = None,
                 version_gte: Optional[str] = None, version_gt: Optional[str] = None):
        if dep_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid dependency type: {dep_type}. Valid types are: {self.VALID_TYPES}")
        self.name = name
        self.dep_type = dep_type
        self.version_lt = version_lt
        self.version_lte = version_lte
        self.version_eq = version_eq
        self.version_gte = version_gte
        self.version_gt = version_gt

    def __repr__(self):
        return (f"Dependency(name='{self.name}', type='{self.dep_type}', "
                f"version_eq='{self.version_eq or ''}')")

class Export:
    """Represents a generic export tag in package.xml."""
    def __init__(self, tag_name: str, content: Optional[str] = None, attributes: Optional[Dict[str, str]] = None):
        self.tag_name = tag_name
        self.content = content
        self.attributes = attributes if attributes is not None else {}

    def __repr__(self):
        return f"Export(tag='{self.tag_name}', attributes={self.attributes}, content='{self.content or ''}')"

class ExecutableTarget:
    """Represents a C++ executable target."""
    def __init__(self, name: str, sources: List[str], linked_libraries: Optional[List[str]] = None):
        self.name = name # e.g., "my_node"
        self.sources = sources # e.g., ["src/my_node.cpp", "src/utils.cpp"]
        self.linked_libraries = linked_libraries if linked_libraries is not None else [] # e.g., ["${PROJECT_NAME}_lib", "rclcpp::rclcpp"]

    def __repr__(self):
        return f"ExecutableTarget(name='{self.name}', sources={self.sources})"

class LibraryTarget:
    """Represents a C++ library target."""
    def __init__(self, name: str, sources: List[str], linked_libraries: Optional[List[str]] = None):
        self.name = name # e.g., "my_lib" (becomes ${PROJECT_NAME}_my_lib or similar)
        self.sources = sources # e.g., ["src/my_lib_code.cpp"]
        self.linked_libraries = linked_libraries if linked_libraries is not None else []

    def __repr__(self):
        return f"LibraryTarget(name='{self.name}', sources={self.sources})"
class PackageConfig:
    def __init__(self, name: str, version: str = "0.0.0", description: str = "TODO: Package description",
                 maintainer_email: str = "user@todo.todo", maintainer_name: str = "TODO: Maintainer name",
                 license_name: str = "TODO: License declaration", build_type: str = "ament_python"):
        
        self.name: str = name
        self.version: str = version
        self.description: str = description
        
        self.maintainers: List[Dict[str, str]] = [{'name': maintainer_name, 'email': maintainer_email}]
        self.licenses: List[str] = [license_name]
        self.authors: List[Dict[str, str]] = []
        self.urls: List[Dict[str, str]] = []
        self.dependencies: List[Dependency] = []
        self.exports: List[Export] = []
        
        # Automatically add the build_type export
        if build_type: # Ensure build_type is not None or empty
            self.add_export(Export(tag_name="build_type", content=build_type))

        self.build_type: str = build_type
        
        # --- Structures for package elements ---
        self.launch_configurations: List[LaunchConfiguration] = [] # Stores defined launch files with their content structure
        self.config_files_paths: List[str] = []    # Relative paths, e.g., ["config/params.yaml"]
        self.interface_files: List[str] = []       # Relative paths, e.g., ["msg/MyData.msg"]
        # --- Updated for C++ Targets ---
        self.executable_targets: List[ExecutableTarget] = [] 
        self.library_targets: List[LibraryTarget] = []   
        
        self.python_nodes: List[Any] = [] # For ament_python entry points
        
        # Placeholders for more detailed structures (can be used later)
        self.executables: List[Any] = [] 
        self.libraries: List[Any] = []   
        self.python_nodes: List[Any] = [] # For entry points (already used by setup.py generator logic)

    def add_maintainer(self, name: str, email: str):
        self.maintainers.append({'name': name, 'email': email})

    def add_license(self, license_name: str):
        if license_name not in self.licenses:
            self.licenses.append(license_name)

    def add_author(self, name: str, email: Optional[str] = None):
        author_info = {'name': name}
        if email:
            author_info['email'] = email
        self.authors.append(author_info)

    def add_url(self, url_value: str, url_type: Optional[str] = "website"):
        self.urls.append({'url': url_value, 'type': url_type})
        
    def add_dependency(self, dep: Dependency):
        self.dependencies.append(dep)

    def add_export(self, export: Export):
        self.exports.append(export)

    def add_launch_configuration(self, launch_config: LaunchConfiguration):
        """Adds a defined launch configuration to the package."""
        self.launch_configurations.append(launch_config)

    def add_config_file(self, relative_path: str):
        """Adds a config file (e.g., 'config/params.yaml')."""
        if relative_path not in self.config_files_paths:
            self.config_files_paths.append(relative_path)

    def add_interface_file(self, relative_path: str):
        """Adds an interface file (e.g., 'msg/MyData.msg')."""
        if relative_path not in self.interface_files:
            self.interface_files.append(relative_path)
    def add_executable_target(self, target: ExecutableTarget):
        self.executable_targets.append(target)

    def add_library_target(self, target: LibraryTarget):
        self.library_targets.append(target)            
    def set_build_type(self, build_type: str):
        self.build_type = build_type
        # Update or add the build_type export
        existing_build_type_export = next((exp for exp in self.exports if exp.tag_name == "build_type"), None)
        if existing_build_type_export:
            if build_type: # Only update if new build_type is valid
                existing_build_type_export.content = build_type
            else: # If new build_type is empty/None, remove the export
                self.exports = [exp for exp in self.exports if exp.tag_name != "build_type"]
        elif build_type: # Only add if new build_type is valid
            self.add_export(Export(tag_name="build_type", content=build_type))
    def __str__(self): # Updated __str__
        return (f"PackageConfig(name='{self.name}', version='{self.version}', "
                f"build_type='{self.build_type}', "
                f"executables={len(self.executable_targets)}, libraries={len(self.library_targets)}, "
                f"launch_configs={len(self.launch_configurations)})")
