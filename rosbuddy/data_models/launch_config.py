# rosbuddy/data_models/launch_config.py
from typing import List, Dict, Any, Optional, Union

class LaunchAction:
    """Base class for any action in a launch file."""
    pass

class Parameter:
    """Represents a ROS parameter for a Node."""
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value # Can be str, int, float, bool, list of these

    def __repr__(self):
        return f"Parameter(name='{self.name}', value={repr(self.value)})"

class Remapping:
    """Represents a remapping rule for a Node."""
    def __init__(self, from_topic: str, to_topic: str):
        self.from_topic = from_topic
        self.to_topic = to_topic

    def __repr__(self):
        return f"Remapping(from='{self.from_topic}', to='{self.to_topic}')"

class NodeAction(LaunchAction):
    """Represents a 'Node' action in a launch file."""
    def __init__(self,
                 package: str,
                 executable: str,
                 name: Optional[str] = None,
                 namespace: Optional[str] = None,
                 parameters: Optional[List[Parameter]] = None,
                 remappings: Optional[List[Remapping]] = None,
                 output: Optional[str] = 'screen', # Common default
                 # Future additions: arguments, condition, etc.
                 ):
        self.package = package
        self.executable = executable
        self.name = name
        self.namespace = namespace
        self.parameters = parameters if parameters is not None else []
        self.remappings = remappings if remappings is not None else []
        self.output = output

    def __repr__(self):
        return (f"NodeAction(package='{self.package}', executable='{self.executable}', "
                f"name='{self.name}', parameters={len(self.parameters)})")

class IncludeLaunchAction(LaunchAction):
    """Represents an 'IncludeLaunchDescription' action."""
    def __init__(self,
                 launch_file_path: str, # Path to the launch file (can be absolute or relative to package share)
                 package: Optional[str] = None, # Package containing the launch file
                 launch_arguments: Optional[Dict[str, Any]] = None
                 ):
        self.launch_file_path = launch_file_path
        self.package = package
        self.launch_arguments = launch_arguments if launch_arguments is not None else {}

    def __repr__(self):
        return f"IncludeLaunchAction(launch_file='{self.launch_file_path}', package='{self.package}')" # Adjusted repr for clarity  

class LaunchConfiguration:
    """Represents the overall configuration of a single launch file."""
    def __init__(self, file_name: str, # e.g., "my_robot.launch.py"
                       actions: Optional[List[LaunchAction]] = None):
        self.file_name = file_name # The name of the .launch.py file to be generated
        self.actions: List[LaunchAction] = actions if actions is not None else []
        # We could add launch arguments declarations here later if needed

    def add_action(self, action: LaunchAction):
        self.actions.append(action)

    def __repr__(self):
        return f"LaunchConfiguration(file_name='{self.file_name}', actions={len(self.actions)})"