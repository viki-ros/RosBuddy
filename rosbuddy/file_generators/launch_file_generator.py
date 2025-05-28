# rosbuddy/file_generators/launch_file_generator.py
import textwrap
from typing import Any, List, Dict, Optional # ADD THIS LINE
from rosbuddy.data_models.launch_config import (
    LaunchConfiguration, LaunchAction, NodeAction, IncludeLaunchAction, Parameter, Remapping
)
from rosbuddy.data_models.package_config import PackageConfig # May not be directly needed, but good for context
import os

def _format_python_value(value: Any) -> str:
    """Formats a Python value into its string representation for code generation."""
    if isinstance(value, str):
        # Escape backslashes and quotes appropriately for a string literal
        escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
        return f"'{escaped_value}'"
    elif isinstance(value, bool):
        return str(value) # True or False
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        return "[" + ", ".join([_format_python_value(v) for v in value]) + "]"
    elif isinstance(value, dict):
        # For launch arguments which are dicts of simple types
        # For parameters, they are usually a list of key-value pairs or a YAML file path
        return "{" + ", ".join([f"{_format_python_value(k)}: {_format_python_value(v)}" for k, v in value.items()]) + "}"
    elif value is None:
        return "None"
    else:
        # Fallback for unknown types, might need more sophisticated handling
        return repr(value)


def _generate_node_action_code(action: NodeAction) -> List[str]:
    """Generates Python code for a single Node action."""
    lines = []
    params_list_str = "[]"
    if action.parameters:
        param_strs = []
        for p in action.parameters:
            # Parameters can be a dict for complex types, or simple key-value
            # For simplicity, we'll assume value is directly usable or a path to YAML
            # A common way is [{'name': value}] or {'name': value}
            # The Parameter class stores name and value separately.
            param_strs.append(f"{{'{p.name}': {_format_python_value(p.value)}}}")
        
        # If parameters are defined, format them as a list of dictionaries
        if param_strs:
             # Parameters in launch are often a list of dicts, or a path to a YAML file.
             # Here we construct a list of dicts.
            params_list_str = "[\n" + ",\n".join([f"                {ps}" for ps in param_strs]) + "\n            ]"


    remappings_list_str = "[]"
    if action.remappings:
        remap_strs = [f"('{r.from_topic}', '{r.to_topic}')" for r in action.remappings]
        remappings_list_str = "[" + ", ".join(remap_strs) + "]"

    # Build the Node call
    node_args = [
        f"package='{action.package}'",
        f"executable='{action.executable}'",
    ]
    if action.name:
        node_args.append(f"name='{action.name}'")
    if action.namespace:
        node_args.append(f"namespace='{action.namespace}'")
    if action.parameters: # Only add if there are parameters
        node_args.append(f"parameters={params_list_str}")
    if action.remappings: # Only add if there are remappings
        node_args.append(f"remappings={remappings_list_str}")
    if action.output:
        node_args.append(f"output='{action.output}'")

    lines.append(f"    ld.add_action(Node(\n        {', '.join(node_args)}\n    ))")
    return lines

def _generate_include_launch_action_code(action: IncludeLaunchAction) -> List[str]:
    """Generates Python code for an IncludeLaunchDescription action."""
    lines = []
    include_args = []

    if action.package:
        # Use PythonLaunchDescriptionSource with FindPackageShare
        lines.append(f"    # Find the package share directory for the included launch file")
        lines.append(f"    {action.package}_share_dir = FindPackageShare(package='{action.package}').find('{action.package}')")
        lines.append(f"    included_launch_file = PythonLaunchDescriptionSource([")
        lines.append(f"        PathJoinSubstitution([{action.package}_share_dir, '{action.launch_file_path}'])")
        lines.append(f"    ])")
        include_args.append("source=included_launch_file")
    else:
        # Assume launch_file_path is directly usable (e.g., absolute or findable by other means)
        # This case is less common for portable launch files.
        include_args.append(f"source=PythonLaunchDescriptionSource('{action.launch_file_path}')")


    if action.launch_arguments:
        # launch_arguments are passed as a list of tuples: [('arg_name', 'value'), ...]
        # or as a dictionary that needs to be converted to items()
        arg_items_str = ", ".join([f"('{k}', {_format_python_value(v)})" for k, v in action.launch_arguments.items()])
        include_args.append(f"launch_arguments=[{arg_items_str}].items()")
        
    lines.append(f"    ld.add_action(IncludeLaunchDescription(\n        {', '.join(include_args)}\n    ))")
    return lines


def generate_python_launch_file_content(launch_config: LaunchConfiguration) -> str:
    """
    Generates the Python code for a .launch.py file based on the LaunchConfiguration.
    """
    
    import_lines = [
        "from launch import LaunchDescription",
        "from launch_ros.actions import Node",
        "from launch.actions import IncludeLaunchDescription",
        "from launch.launch_description_sources import PythonLaunchDescriptionSource",
        "from launch_ros.substitutions import FindPackageShare",
        "from launch.substitutions import PathJoinSubstitution",
        "import os" # Often useful
        # We might need more imports depending on the actions (e.g., SetEnvironmentVariable)
    ]
    
    # Check if specific imports are needed based on actions
    has_node_action = any(isinstance(action, NodeAction) for action in launch_config.actions)
    has_include_action = any(isinstance(action, IncludeLaunchAction) for action in launch_config.actions)

    # Minimal imports
    current_imports = set(["from launch import LaunchDescription"])
    if has_node_action:
        current_imports.add("from launch_ros.actions import Node")
    if has_include_action:
        current_imports.add("from launch.actions import IncludeLaunchDescription")
        current_imports.add("from launch.launch_description_sources import PythonLaunchDescriptionSource")
        current_imports.add("from launch_ros.substitutions import FindPackageShare") # For finding other packages
        current_imports.add("from launch.substitutions import PathJoinSubstitution") # For joining paths


    body_lines = [
        "",
        "def generate_launch_description():",
        "    ld = LaunchDescription()",
        ""
    ]

    for action in launch_config.actions:
        if isinstance(action, NodeAction):
            body_lines.extend(_generate_node_action_code(action))
        elif isinstance(action, IncludeLaunchAction):
            body_lines.extend(_generate_include_launch_action_code(action))
        # TODO: Add handlers for other action types (ExecuteProcess, SetEnvironmentVariable, etc.)
        else:
            body_lines.append(f"    # Skipping unsupported action type: {type(action)}")
        body_lines.append("") # Add a blank line between actions for readability

    body_lines.append("    return ld")
    
    # Combine imports and body
    # Sort imports for consistency, though order can matter for some specific cases (not usually these)
    final_code = "\n".join(sorted(list(current_imports))) + "\n" + "\n".join(body_lines)
    return final_code