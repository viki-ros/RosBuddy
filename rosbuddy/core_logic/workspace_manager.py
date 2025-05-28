# rosbuddy/core_logic/workspace_manager.py
import pathlib
import os
from typing import Optional, Tuple

class WorkspaceManager:
    """
    Manages ROS 2 workspace creation and keeps track of the active workspace.
    """
    def __init__(self):
        self._active_workspace_path: Optional[pathlib.Path] = None
        self._active_workspace_src_path: Optional[pathlib.Path] = None

    def get_active_workspace_path(self) -> Optional[pathlib.Path]:
        """Returns the path to the root of the active workspace."""
        return self._active_workspace_path

    def get_active_workspace_src_path(self) -> Optional[pathlib.Path]:
        """Returns the path to the 'src' directory of the active workspace."""
        return self._active_workspace_src_path

    def create_new_workspace(self, parent_directory: str, workspace_name: str) -> Tuple[bool, str, Optional[pathlib.Path]]:
        """
        Creates a new ROS 2 workspace directory structure.
        A workspace consists of a root folder and a 'src' subfolder.

        Args:
            parent_directory: The directory where the workspace root folder will be created.
            workspace_name: The name for the workspace root folder.

        Returns:
            A tuple: (success: bool, message: str, workspace_path: Optional[pathlib.Path])
        """
        parent_path = pathlib.Path(parent_directory)
        if not parent_path.is_dir():
            return False, f"Error: Parent directory '{parent_directory}' does not exist or is not a directory.", None

        workspace_root = parent_path / workspace_name
        workspace_src = workspace_root / "src"

        if workspace_root.exists():
            # Check if it already looks like a valid workspace (has a src folder)
            if workspace_src.exists() and workspace_src.is_dir():
                message = f"Workspace '{workspace_name}' already exists at '{workspace_root}' and appears valid. Setting as active."
                self.set_active_workspace(str(workspace_root)) # Set it as active
                return True, message, workspace_root # Consider this a success for creation if it's already there and valid
            else:
                return False, f"Error: Directory '{workspace_name}' already exists at '{workspace_root}' but is not a valid workspace (missing 'src' folder or 'src' is not a directory).", None
        
        try:
            workspace_root.mkdir(parents=False, exist_ok=False) # Don't create parent_path, don't overwrite
            workspace_src.mkdir(parents=False, exist_ok=False) # Should be created inside workspace_root
            
            message = f"Successfully created new workspace '{workspace_name}' at '{workspace_root}'."
            print(message)
            self.set_active_workspace(str(workspace_root)) # Set the new workspace as active
            return True, message, workspace_root
        except FileExistsError:
            # This case should ideally be caught by the initial check, but as a safeguard
            return False, f"Error: Workspace directory '{workspace_root}' or its 'src' folder already exists.", None
        except OSError as e:
            return False, f"Error creating workspace directories: {e}", None

    def is_valid_workspace(self, workspace_path_str: str) -> bool:
        """
        Checks if the given path points to a directory that looks like a ROS 2 workspace
        (i.e., it's a directory and contains a 'src' subdirectory).
        """
        workspace_path = pathlib.Path(workspace_path_str)
        if not workspace_path.is_dir():
            return False
        
        src_path = workspace_path / "src"
        if not src_path.exists() or not src_path.is_dir():
            return False
            
        return True

    def set_active_workspace(self, workspace_path_str: str) -> Tuple[bool, str]:
        """
        Sets the active workspace path after validating it.

        Args:
            workspace_path_str: The path to the workspace root.

        Returns:
            A tuple: (success: bool, message: str)
        """
        if self.is_valid_workspace(workspace_path_str):
            self._active_workspace_path = pathlib.Path(workspace_path_str).resolve()
            self._active_workspace_src_path = self._active_workspace_path / "src"
            message = f"Active workspace set to: {self._active_workspace_path}"
            print(message)
            return True, message
        else:
            self._active_workspace_path = None
            self._active_workspace_src_path = None
            message = f"Error: '{workspace_path_str}' is not a valid ROS 2 workspace directory (must exist and contain a 'src' subdirectory)."
            print(message)
            return False, message

    def clear_active_workspace(self):
        """Clears the active workspace path."""
        self._active_workspace_path = None
        self._active_workspace_src_path = None
        print("Active workspace cleared.")