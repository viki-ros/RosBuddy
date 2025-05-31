# rosbuddy/main_app.py
import sys
import logging
import pathlib # Added
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

# --- START: Ensure 'rosbuddy' package is discoverable if run directly ---
# This adds the project root (one level up from 'rosbuddy' directory) to sys.path
project_root_for_main_app = pathlib.Path(__file__).resolve().parent.parent
if str(project_root_for_main_app) not in sys.path:
    sys.path.insert(0, str(project_root_for_main_app))
# --- END: Path adjustment ---

# Import the new modern UI
from rosbuddy.ui.modern_main_window import ModernMainWindow
from rosbuddy.core_logic import WorkspaceManager, ToolInvoker # Import core logic classes

# --- Global Logger for this file (main_app.py) ---
# This logger will use the handlers (console, GUI) set up on the root logger.
module_logger = logging.getLogger(__name__)

STYLESHEET_PATH = pathlib.Path(__file__).resolve().parent / "ui" / "resources" / "themes" / "default_dark.qss"

def load_stylesheet() -> str:
    if STYLESHEET_PATH.exists():
        try:
            with open(STYLESHEET_PATH, "r") as f:
                return f.read()
        except Exception as e:
            module_logger.error(f"Failed to load stylesheet from {STYLESHEET_PATH}: {e}")
    else:
        module_logger.warning(f"Stylesheet not found at {STYLESHEET_PATH}. Using fallback or no custom style.")
    return ""

class RosBuddyApplication(QApplication):
    def __init__(self, argv, window_geometry=None, splitter_state=None):
        super().__init__(argv)
        # Instantiate core logic components
        self.workspace_manager = WorkspaceManager()
        self.tool_invoker = ToolInvoker(self.workspace_manager)
        # Create and show the main window, passing logic components and UI state
        self.main_window = ModernMainWindow(
            workspace_manager=self.workspace_manager,
            tool_invoker=self.tool_invoker,
            window_geometry=window_geometry,
            splitter_state=splitter_state
        )
        self.main_window.show()

    def get_ui_state(self):
        return self.main_window.get_ui_state()


def main(workspace_path=None, window_geometry=None, splitter_state=None):
    # Set application details (optional but good practice)
    QApplication.setApplicationName("ROSBuddy")
    QApplication.setOrganizationName("RosBuddyOrg") # Or your name/org
    QApplication.setApplicationVersion("0.1.2") # Match MainWindow's About dialog

    # --- Basic Logging Configuration (for console, before GUI handler is up) ---
    logging.basicConfig(
        level=logging.DEBUG, # Set root logger level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)] # Basic console output
    )
    module_logger.info("ROSBuddy application bootstrap...")

    app = RosBuddyApplication(sys.argv, window_geometry=window_geometry, splitter_state=splitter_state)
    if workspace_path:
        # Try to set the workspace before showing the main window
        success, msg = app.workspace_manager.set_active_workspace(workspace_path)
        if not success:
            module_logger.warning(f"Failed to set workspace from startup argument: {msg}")
    stylesheet_content = load_stylesheet()
    if stylesheet_content:
        app.setStyleSheet(stylesheet_content)
    else:
        module_logger.info("No custom stylesheet loaded. Using default Qt styling.")

    module_logger.info("ROSBuddy Application GUI initialized and starting event loop...")
    exit_code = app.exec()
    # Return UI state for persistence (from MainWindow via QApplication)
    ui_state = getattr(app, '_rosbuddy_ui_state', None)
    module_logger.info(f"ROSBuddy Application exited with code {exit_code}.")
    return ui_state
    # sys.exit(exit_code)  # Do not call sys.exit here, let the caller handle it

if __name__ == '__main__':
    main()