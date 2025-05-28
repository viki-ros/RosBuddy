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

# Assuming MainWindow is in rosbuddy.ui.main_window
from rosbuddy.ui.main_window import MainWindow
from rosbuddy.core_logic import WorkspaceManager, ToolInvoker # Import core logic classes

# --- Global Logger for this file (main_app.py) ---
# This logger will use the handlers (console, GUI) set up on the root logger.
module_logger = logging.getLogger(__name__) # e.g., "rosbuddy.main_app"

DARK_THEME_QSS = """
/* Dark Theme with Blue Accent & More Design Elements */
/* Stylesheet content remains the same */

/* --- General Window & Text --- */
QWidget {
    background-color: #2D2D30; /* Slightly lighter dark base */
    color: #CCCCCC; /* Light gray for general text */
    font-family: Segoe UI, Cantarell, DejaVu Sans, Ubuntu, sans-serif; /* Common clean fonts */
    border: none; /* Remove default borders that can look clunky */
}

QMainWindow {
    background-color: #252526; /* Even darker for the main window itself */
}

/* --- MenuBar & Menu --- */
QMenuBar {
    background-color: #333333;
    color: #DDDDDD;
    padding: 2px; /* Add a little padding */
    border-bottom: 1px solid #1E1E1E; /* Sharper bottom border */
}
QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
    border-radius: 3px; /* Slightly rounded hover */
}
QMenuBar::item:selected { /* Hover */
    background-color: #007ACC; /* Blue accent */
    color: #FFFFFF;
}
QMenuBar::item:pressed {
    background-color: #005C99; /* Darker blue when pressed */
    color: #FFFFFF;
}
QMenu {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #444444; /* Defined border */
    padding: 5px;
}
QMenu::item {
    padding: 5px 20px 5px 15px; /* More padding */
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #007ACC;
    color: #FFFFFF;
}
QMenu::icon { /* Space for icons in menu items */
    padding-left: 5px;
}
QMenu::separator {
    height: 1px;
    background-color: #444444;
    margin: 4px 0px;
}

/* --- StatusBar --- */
QStatusBar {
    background-color: #007ACC; /* Blue accent for status bar */
    color: #FFFFFF; /* White text on blue */
    font-weight: bold;
    padding: 2px;
}
QStatusBar QLabel { /* Ensure labels within status bar get white text */
    color: #FFFFFF;
    background-color: transparent; /* No background for labels in status bar */
    padding: 0 5px;
}

/* --- Buttons --- */
QPushButton {
    background-color: #3E3E42;
    color: #F0F0F0;
    border: 1px solid #555555;
    padding: 6px 12px;
    min-width: 70px;
    border-radius: 4px; /* More pronounced rounding */
}
QPushButton:hover {
    background-color: #4F4F53;
    border: 1px solid #6A6A6A;
}
QPushButton:pressed {
    background-color: #007ACC; /* Blue accent when pressed */
    color: #FFFFFF;
    border: 1px solid #005C99;
}
QPushButton:disabled {
    background-color: #333333;
    color: #777777;
    border-color: #444444;
}
/* Special button styling (e.g., "OK" button in dialogs) */
QPushButton#okButton, QDialogButtonBox QPushButton[text="OK"] { /* Targeting OK buttons */
    background-color: #007ACC;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton#okButton:hover, QDialogButtonBox QPushButton[text="OK"]:hover {
    background-color: #008AE6;
}
QPushButton#okButton:pressed, QDialogButtonBox QPushButton[text="OK"]:pressed {
    background-color: #005C99;
}


/* --- Input Fields (QLineEdit, QComboBox, QTextEdit) --- */
QLineEdit, QComboBox, QTextEdit {
    background-color: #333333;
    color: #DDDDDD;
    border: 1px solid #555555;
    padding: 5px;
    selection-background-color: #007ACC; /* Blue selection */
    selection-color: white;
    border-radius: 3px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #007ACC; /* Blue border when focused */
    outline: none; /* Remove default outline if any */
}

/* --- QComboBox Specific --- */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    background-color: #3E3E42;
}
QComboBox::down-arrow {
    /* Using a standard char for simplicity, can be replaced by SVG/image */
    /* For a proper icon, you'd use 'image: url(...);' */
    /* This is a unicode down arrow char, may need font support */
    /* No easy way to color this char directly with QSS, image is better */
}
QComboBox QAbstractItemView { /* The dropdown list part */
    background-color: #2D2D30;
    border: 1px solid #444444;
    selection-background-color: #007ACC;
    color: #CCCCCC;
}

/* --- QCheckBox --- */
QCheckBox {
    spacing: 8px;
    color: #CCCCCC;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    background-color: #333333;
    border-radius: 3px;
}
QCheckBox::indicator:hover {
    border: 1px solid #007ACC;
}
QCheckBox::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #005C99;
    /* Add a checkmark image here if desired */
    /* image: url(path/to/white_checkmark.svg); */
}
QCheckBox::indicator:disabled {
    background-color: #444444;
    border: 1px solid #555555;
}


/* --- OutputDisplay (your existing QTextEdit) --- */
/* This is a suggestion if you want to integrate its style more */
/* You'll need to set objectName = "outputDisplay" on your OutputDisplay instance */
QTextEdit#outputDisplay {
    background-color: #1E1E1E; /* Very dark, typical for consoles */
    color: #DCDCDC; /* Off-white text */
    font-family: Consolas, "DejaVu Sans Mono", "Ubuntu Mono", "Courier New", monospace; /* Added more fallbacks */
    border: 1px solid #383838; /* Slightly more visible border than #333333 */
    padding: 5px;
    selection-background-color: #007ACC; /* Keep consistent selection color */
    selection-color: white;
}

/* --- Dialogs --- */
QDialog {
    background-color: #2D2D30; /* Consistent dialog background */
}
QDialog QLabel { /* Labels within dialogs */
    color: #CCCCCC;
    background-color: transparent;
}

/* --- Main content placeholder styling --- */
QLabel#mainContentArea { /* If you keep the placeholder label */
    font-size: 18pt;
    font-weight: bold;
    color: #007ACC; /* Use accent color for prominent text */
    background-color: transparent;
}

/* --- Tool Buttons (QToolButton) --- */
QToolButton {
    background-color: #3E3E42;
    color: #F0F0F0;
    border: 1px solid #555555;
    padding: 4px;
    border-radius: 3px;
    min-width: 0;
}
QToolButton:hover {
    background-color: #4F4F53;
    border: 1px solid #6A6A6A;
}
QToolButton:pressed {
    background-color: #007ACC;
    color: #FFFFFF;
    border: 1px solid #005C99;
}

/* --- ToolBar --- */
QToolBar {
    background-color: #383838; /* Slightly different from menubar */
    border-bottom: 1px solid #1E1E1E;
    padding: 2px;
    spacing: 3px; /* Spacing between buttons */
}

QToolBar QToolButton {
    background-color: transparent; /* Make them flat */
    color: #DDDDDD;
    border: 1px solid transparent; /* No border initially */
    padding: 5px;
    border-radius: 3px;
    min-width: 24px; /* Adjust based on icon size */
    min-height: 24px;
}
QToolBar QToolButton:hover {
    background-color: #555555; /* Hover effect */
    border: 1px solid #666666;
}
QToolBar QToolButton:pressed {
    background-color: #007ACC; /* Pressed effect */
    color: #FFFFFF;
    border: 1px solid #005C99;
}
QToolBar QToolButton:disabled {
    color: #777777;
    background-color: transparent;
}
QToolBar::separator {
    background-color: #555555;
    width: 1px;
    margin-left: 4px;
    margin-right: 4px;
}

/* --- QTreeView (Workspace Explorer) --- */
QTreeView {
    background-color: #252526; /* Darker background for tree */
    color: #CCCCCC;
    border: 1px solid #383838;
    /* font-size: 9pt; */ /* Optional: adjust font size */
}
QTreeView::item {
    padding: 4px; /* Increased padding slightly */
    border-radius: 3px; /* Match other rounded elements */
}
QTreeView::item:hover {
    background-color: #3E3E42; /* Consistent hover */
}
QTreeView::item:selected {
    background-color: #007ACC; /* Accent color for selection */
    color: #FFFFFF;
}
/* For branch indicators (arrows) - Qt usually handles these well with system theme or default dark style */
/* If you need custom arrows, you'd uncomment and provide paths to images */
/* QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url(path/to/arrow-right.png);
}
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url(path/to/arrow-down.png);
} */
"""

class RosBuddyApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        # Instantiate core logic components
        self.workspace_manager = WorkspaceManager()
        self.tool_invoker = ToolInvoker(self.workspace_manager) # ToolInvoker needs WorkspaceManager

        # Create and show the main window, passing logic components
        self.main_window = MainWindow(
            workspace_manager=self.workspace_manager,
            tool_invoker=self.tool_invoker
        )
        self.main_window.show()


def main():
    # Set application details (optional but good practice)
    QApplication.setApplicationName("ROSBuddy")
    QApplication.setOrganizationName("RosBuddyOrg") # Or your name/org
    QApplication.setApplicationVersion("0.1.2") # Match MainWindow's About dialog

    # --- Basic Logging Configuration (for console, before GUI handler is up) ---
    # This configures the root logger. MainWindow will add its GUI handler to this same root logger.
    logging.basicConfig(
        level=logging.DEBUG, # Set root logger level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)] # Basic console output
    )
    # Any logger created from now on (e.g. module_logger above, or loggers in other modules)
    # will inherit this level and send to console. MainWindow will add its GUI handler to the root.

    module_logger.info("ROSBuddy application bootstrap...") # Log using the module_logger

    app = RosBuddyApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    module_logger.info("ROSBuddy Application GUI initialized and starting event loop...")
    exit_code = app.exec()
    module_logger.info(f"ROSBuddy Application exited with code {exit_code}.")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()