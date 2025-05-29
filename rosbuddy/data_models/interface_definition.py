from typing import List
from dataclasses import dataclass, field

@dataclass
class InterfaceFileDefinition:
    """
    Represents the configuration for a single .msg, .srv, or .action file to be generated.
    """
    file_name: str  # e.g., "MotorStatus.msg", "SetTarget.srv", "NavigateToGoal.action"
    interface_type: str # "msg", "srv", or "action"
    content: str    # The actual definition text
    interface_package_dependencies: List[str] = field(default_factory=list)

    @property
    def relative_path(self) -> str:
        return f"{self.interface_type}/{self.file_name}"

    def __post_init__(self):
        if not self.file_name.endswith(f".{self.interface_type}"):
            pass
        if self.interface_type not in ["msg", "srv", "action"]:
            raise ValueError(f"Invalid interface_type: {self.interface_type}")
