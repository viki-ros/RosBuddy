# rosbuddy/ui/main_window.py
import sys
import os
import pathlib
import traceback
import subprocess
import time # Keep for now if on_stop_task uses it for a brief pause
import logging
import ast
import astor
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QSplitter, QWidget, QLabel, QStatusBar, QMenuBar, QTextEdit,
    QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QApplication, QToolButton, QToolBar, QTabWidget,
    QStyle, # For standard icons
    QTreeView, # For Workspace Explorer
    QLineEdit,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QModelIndex, QByteArray, QFile, QSize
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence, QAction

# Project imports
from rosbuddy.utils.icon_manager import IconManager
from rosbuddy.ui.views.ros_tools_navigation_view import RosToolsNavigationView
from rosbuddy.ui.wizards import ParameterFileWizard
 
# Configure module-level logger
logger = logging.getLogger(__name__)

# Project specific imports
from rosbuddy.core_logic import WorkspaceManager, ToolInvoker, create_package_scaffolding, PackageDiscovery
from rosbuddy.core_logic.package_discovery import PackageInfo
from rosbuddy.data_models import PackageConfig
from rosbuddy.ui.dialogs import CreatePackageDialog, SelectRosItemDialog
from rosbuddy.ui.components import WorkspaceExplorer, OutputPanel, ContextualViewPlaceholder
from rosbuddy.ui.components.worker import Worker, WorkerSignals
from rosbuddy.ui.dialogs.node_creator_dialog import NodeCreatorDialog
from rosbuddy.ui.dialogs.launch_file_composer_dialog import LaunchFileComposerDialog
from rosbuddy.ui.dialogs.msg_srv_action_editor_dialog import MsgSrvActionEditorDialog
from rosbuddy.ui.dialogs.package_config_editor_dialog import PackageConfigEditorDialog # Import new views
from rosbuddy.file_generators.package_xml_modifier import update_package_xml_for_new_interface
from rosbuddy.file_generators.cmake_modifier import update_cmakelists_for_new_interface, CMakeUpdateStatus
from rosbuddy.code_generation.node_generator import NodeGenerator
from rosbuddy.ui.views import (SettingsView, AIAssistantView, CodeEditorView, WelcomeView,
                               NodeWizardView, LaunchRunnerView, DebugView, RosGraphInspectorView,
                               RosDoctorView, AIAgentActionView)
from rosbuddy.file_generators.package_xml_modifier import add_unique_dependency_to_package_xml
from rosbuddy.file_generators.cmake_generator import generate_cmake_lists_content
from rosbuddy.data_models.package_config import PackageConfig, Dependency

# --- Custom Logging Handler ---
class QtLogSignal(QObject):
    log_message_written = pyqtSignal(str)

class QtLogHandler(logging.Handler):
    def __init__(self, parent_signal_emitter: QtLogSignal):
        super().__init__()
        self.signal_emitter = parent_signal_emitter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s : %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.signal_emitter.log_message_written.emit(msg)
        except Exception:
            self.handleError(record)

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self, workspace_manager: WorkspaceManager, tool_invoker: ToolInvoker, parent=None, window_geometry=None, splitter_state=None):
        super().__init__(parent)
        self.active_ws_label = QLabel("Active Workspace: None")
        self.active_ws_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 6px 12px; color: #00aaff;")

        self.setWindowTitle("ROSBuddy - ROS 2 Package Development Assistant")
        self.setGeometry(100, 100, 1280, 800)
        # Restore window geometry if provided
        if window_geometry:
            self.restoreGeometry(window_geometry)

        self.workspace_manager = workspace_manager
        self.tool_invoker = tool_invoker
        self.package_discovery = PackageDiscovery(self.workspace_manager)
        self.current_worker: Optional[Worker] = None
        self.current_action_description: str = ""
        self.running_ros_process: Optional[subprocess.Popen] = None
        self.last_maint_name: str = "ROS User"
        self.last_maint_email: str = "user@example.com"

        # Initialize IconManager before creating actions
        self.icon_manager = IconManager(self.style())

        # --- Legacy action attributes for compatibility ---
        self.new_workspace_action = QAction("New Workspace", self)
        self.open_workspace_action = QAction("Open Workspace", self)
        self.create_package_action = QAction("Create Package", self)
        self.build_workspace_action = QAction("Build Workspace", self)
        self.clean_workspace_action = QAction("Clean Workspace", self)
        self.run_executable_action = QAction("Run Executable", self)
        self.launch_file_action = QAction("Launch File", self)
        self.stop_task_action = QAction("Stop Task", self)
        self.refresh_workspace_action = QAction("Refresh Workspace", self)

        # --- Modular UI Components ---
        self.workspace_explorer = WorkspaceExplorer(self.package_discovery, self.workspace_manager)
        self.workspace_explorer.doubleClicked.connect(self._on_explorer_item_double_clicked) # Reverted to standard QTreeView signal
        self.output_panel = OutputPanel()
        # self.contextual_view_placeholder = ContextualViewPlaceholder() # Will be replaced by QTabWidget
        self.active_view_tabs = QTabWidget()
        self.active_view_tabs.setTabsClosable(True)
        self.active_view_tabs.tabCloseRequested.connect(self.on_close_tab)
        self.active_view_tabs.currentChanged.connect(self.on_active_tab_changed)

        # Placeholder for when no tabs are open (as per report)
        self._empty_tab_placeholder = QLabel("Open a file from the Workspace Explorer or use an action from the sidebar.")
        self._empty_tab_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_tab_placeholder.setStyleSheet("font-style: italic; color: #888; font-size: 14px; padding: 20px;")
        self._empty_tab_placeholder.setWordWrap(True)

        # Map unique view IDs to their corresponding sidebar actions that open them
        self.sidebar_view_action_map: Dict[str, QAction] = {} # Initialize as empty, populated in _create_actions

        # Connect clear button
        self.output_panel.clear_output_button.clicked.connect(self.on_clear_output)

        # --- Sidebar ---
        self.sidebar_tool_bar = QToolBar("Sidebar")
        self.sidebar_tool_bar.setObjectName("sidebarToolBar")
        self.sidebar_tool_bar.setMovable(False)
        self.sidebar_tool_bar.setFloatable(False)
        self.sidebar_tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.sidebar_tool_bar.setFixedWidth(120)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.sidebar_tool_bar)

        # Sidebar actions
        self.sidebar_actions = []
        sidebar_sections = [
            ("Explorer", "Workspace Explorer"),
            ("Node Wizard", "Node Wizard"),
            ("Launch Runner", "Launch Runner"),
            ("AI Assistant", "AI Assistant"),
            ("Settings", "Settings")
        ]
        self.sidebar_content_stack = QStackedWidget()
        for idx, (action_name, label_text) in enumerate(sidebar_sections):
            action = QAction(action_name, self)
            action.setCheckable(True)
            self.sidebar_tool_bar.addAction(action)
            self.sidebar_actions.append(action)
            # Add placeholder content for each section
            page = QWidget()
            layout = QVBoxLayout(page)
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 40px;")
            layout.addWidget(label)
            self.sidebar_content_stack.addWidget(page)

        # Sidebar action switching
        def make_switcher(i):
            return lambda checked=False, i=i: self.sidebar_content_stack.setCurrentIndex(i)
        for i, action in enumerate(self.sidebar_actions):
            action.triggered.connect(make_switcher(i))
        self.sidebar_actions[0].setChecked(True)
        self.sidebar_content_stack.setCurrentIndex(0)

        # --- Toolbar ---
        self.tool_bar = QToolBar("Main Toolbar")
        self.tool_bar.setObjectName("mainToolBar")
        self.tool_bar.setMovable(True)
        self.tool_bar.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tool_bar)
        toolbar_actions = [
            ("New Workspace", self.on_new_workspace),
            ("Open Workspace", self.on_open_workspace),
            ("Build", self.on_build_workspace),
            ("Run", self.on_run_executable),
            ("Launch", self.on_launch_file),
            ("Stop", self.on_stop_task),
            ("Refresh", self.on_refresh_workspace_explorer)
        ]
        for name, slot in toolbar_actions:
            action = QAction(name, self)
            action.triggered.connect(slot)
            self.tool_bar.addAction(action)

        # --- Central Widget Layout ---
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.active_ws_label)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        h_layout.addWidget(self.sidebar_content_stack)
        main_layout.addLayout(h_layout)
        self.setCentralWidget(central)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")

        # --- Setup GUI Logging ---
        self.log_signal_emitter = QtLogSignal()
        self.log_signal_emitter.log_message_written.connect(self.output_display.append_text)
        gui_log_handler = QtLogHandler(self.log_signal_emitter)
        gui_log_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(gui_log_handler)
        
        self.update_active_workspace_display()
        logger.info("MainWindow initialized and GUI logging handler set up.")
        self._open_initial_view() # Open WelcomeView or show placeholder
        self._update_empty_tab_placeholder_visibility() # Initial check

        # Apply modern dark theme
        try:
            qss_file = QFile(":/rosbuddy/ui/resources/themes/modern_dark.qss")
            if not qss_file.exists():
                qss_file.setFileName(str(pathlib.Path(__file__).parent / "resources/themes/modern_dark.qss"))
            if qss_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                qss = str(qss_file.readAll(), encoding="utf-8")
                QApplication.instance().setStyleSheet(qss)
        except Exception as theme_exc:
            print(f"[ROSBuddy] Failed to apply theme: {theme_exc}")

    @property
    def active_tab_unique_id(self) -> Optional[str]:
        current_widget = self.active_view_tabs.currentWidget()
        if current_widget and hasattr(current_widget, 'rosbuddy_tab_id'):
            return current_widget.rosbuddy_tab_id
        return None


    @property
    def output_display(self) -> QTextEdit: # Convenience property
        return self.output_panel.output_display


    def _create_actions(self):
        """Creates all QActions used in menus and toolbars."""
        # Main toolbar and menu actions (no icons)
        self.new_workspace_action = QAction("&New Workspace...", self)
        self.new_workspace_action.triggered.connect(self.on_new_workspace)
        self.open_workspace_action = QAction("&Open Workspace...", self)
        self.open_workspace_action.triggered.connect(self.on_open_workspace)
        self.exit_action = QAction("&Exit", self)
        self.exit_action.triggered.connect(self.close)

        # Create Workspace Actions
        self.create_package_action = QAction("&Create New Package...", self)
        self.create_package_action.triggered.connect(self.on_create_package)
        self.build_workspace_action = QAction("&Build Workspace", self)
        self.build_workspace_action.triggered.connect(self.on_build_workspace)
        self.clean_workspace_action = QAction("&Clean Workspace", self)
        self.clean_workspace_action.triggered.connect(self.on_clean_workspace)
        self.run_executable_action = QAction("Run &Executable...", self)
        self.run_executable_action.triggered.connect(self.on_run_executable)
        self.launch_file_action = QAction("&Launch File...", self)
        self.launch_file_action.triggered.connect(self.on_launch_file)
        self.stop_task_action = QAction("&Stop Current Task", self)
        self.stop_task_action.triggered.connect(self.on_stop_task)
        self.refresh_workspace_action = QAction("&Refresh Workspace Explorer", self)
        self.refresh_workspace_action.triggered.connect(self.on_refresh_workspace_explorer)

        # Sidebar Actions (no icons)
        self.sidebar_explorer_action = QAction("Explorer", self)
        self.sidebar_explorer_action.triggered.connect(self.on_sidebar_explorer)
        self.sidebar_explorer_action.setCheckable(True)

        self.sidebar_settings_action = QAction("Settings", self)
        self.sidebar_settings_action.triggered.connect(self.on_sidebar_settings)
        self.sidebar_settings_action.setCheckable(True)

        self.sidebar_ai_assistant_action = QAction("AI Assistant", self)
        self.sidebar_ai_assistant_action.triggered.connect(self.on_sidebar_ai_assistant)
        self.sidebar_ai_assistant_action.setCheckable(True)

        self.sidebar_node_wizard_action = QAction("Node Wizard", self)
        self.sidebar_node_wizard_action.triggered.connect(self.on_sidebar_node_wizard)
        self.sidebar_node_wizard_action.setCheckable(True)

        self.sidebar_debug_view_action = QAction("Debug View", self)  # Add the missing action
        self.sidebar_debug_view_action.triggered.connect(self.on_sidebar_debug_view)
        self.sidebar_debug_view_action.setCheckable(True)

        self.sidebar_launch_runner_action = QAction("Launch Runner", self)
        self.sidebar_launch_runner_action.triggered.connect(self.on_sidebar_launch_runner)
        self.sidebar_launch_runner_action.setCheckable(True)

        self.sidebar_ros_graph_action = QAction("ROS Graph", self)
        self.sidebar_ros_graph_action.triggered.connect(self.on_sidebar_ros_graph)
        self.sidebar_ros_graph_action.setCheckable(True)

        self.sidebar_ai_agent_action = QAction("AI Agent Actions", self)
        self.sidebar_ai_agent_action.triggered.connect(self.on_sidebar_ai_agent_actions)
        self.sidebar_ai_agent_action.setCheckable(True)

        self.sidebar_ros_doctor_action = QAction("ROS Doctor", self)
        self.sidebar_ros_doctor_action.triggered.connect(self.on_sidebar_ros_doctor)
        self.sidebar_ros_doctor_action.setCheckable(True)

        # Omni-search action
        self.omni_search_action = QAction("Quick Search", self)
        self.omni_search_action.triggered.connect(self.on_omni_search_triggered)
        self.omni_search_action.setShortcut(QKeySequence(Qt.Key.Key_K | Qt.KeyboardModifier.ControlModifier))

        # Asset Creation Actions
        self.new_node_action = QAction("New Node...", self)
        self.new_node_action.triggered.connect(self.on_new_node)
        self.new_launch_action = QAction("New Launch File...", self)
        self.new_launch_action.triggered.connect(self.on_new_launch_file)
        self.new_msg_srv_action = QAction("New Msg/Srv/Action...", self)
        self.new_msg_srv_action.triggered.connect(self.on_new_msg_srv_action)
        self.edit_pkg_config_action = QAction("Edit package.xml/CMakeLists.txt...", self)
        self.edit_pkg_config_action.triggered.connect(self.on_edit_pkg_config)

        # New Python and C++ Node actions
        self.new_python_node_action = QAction("New Python Node...", self)
        self.new_python_node_action.triggered.connect(self.on_new_python_node)
        self.new_cpp_node_action = QAction("New C++ Node...", self)
        self.new_cpp_node_action.triggered.connect(self.on_new_cpp_node)

        # Map sidebar actions to their unique IDs for active state management
        self.sidebar_view_action_map = {
            "rosbuddy_settings_view": self.sidebar_settings_action,
            "rosbuddy_ai_assistant_view": self.sidebar_ai_assistant_action,
            "rosbuddy_node_wizard_view": self.sidebar_node_wizard_action,
            "rosbuddy_launch_runner_view": self.sidebar_launch_runner_action,
            "rosbuddy_ros_graph_view": self.sidebar_ros_graph_action,
            "rosbuddy_debug_view": self.sidebar_debug_view_action,
            "rosbuddy_ai_agent_actions_view": self.sidebar_ai_agent_action,
            "rosbuddy_ros_doctor_view": self.sidebar_ros_doctor_action,
        }

        # Set initial enabled states
        self.create_package_action.setEnabled(False)
        self.build_workspace_action.setEnabled(False)
        self.clean_workspace_action.setEnabled(False)
        self.run_executable_action.setEnabled(False)
        self.launch_file_action.setEnabled(False)
        self.stop_task_action.setEnabled(False)
        self.refresh_workspace_action.setEnabled(False)
        
        # Omni-Search Action (for toolbar)
        icon_omni_search = QIcon.fromTheme("edit-find", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.omni_search_action = QAction(icon_omni_search, "Omni-Search (Ctrl+K)...", self)
        self.omni_search_action.setShortcut(QKeySequence(Qt.Key.Key_K | Qt.KeyboardModifier.ControlModifier))
        self.omni_search_action.triggered.connect(self.on_omni_search_triggered)
        self.omni_search_action.setToolTip("Coming Soon: Search files, commands, etc.")


    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_workspace_action)
        file_menu.addAction(self.open_workspace_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        workspace_menu = menu_bar.addMenu("&Workspace")
        workspace_menu.addAction(self.create_package_action)
        workspace_menu.addSeparator()
        workspace_menu.addAction(self.refresh_workspace_action)
        build_menu = menu_bar.addMenu("&Build")
        build_menu.addAction(self.build_workspace_action)
        build_menu.addAction(self.clean_workspace_action)
        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(self.run_executable_action)
        run_menu.addAction(self.launch_file_action)
        run_menu.addSeparator()
        run_menu.addAction(self.stop_task_action)
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self) # No icon needed for About in menu usually
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        asset_menu = menu_bar.addMenu("&Assets")
        asset_menu.addAction(self.new_node_action)
        asset_menu.addAction(self.new_launch_action)
        asset_menu.addAction(self.new_msg_srv_action)
        asset_menu.addSeparator()
        asset_menu.addAction(self.edit_pkg_config_action)
        asset_menu.addAction(self.new_python_node_action)
        asset_menu.addAction(self.new_cpp_node_action)

    def _create_tool_bar(self):
        self.tool_bar = QToolBar("Main Toolbar")
        self.tool_bar.setObjectName("mainToolBar")
        self.tool_bar.setMovable(True)
        self.tool_bar.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tool_bar)

        self.tool_bar.addAction(self.new_workspace_action)
        self.tool_bar.addAction(self.open_workspace_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.refresh_workspace_action)
        self.tool_bar.addAction(self.create_package_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.build_workspace_action)
        self.tool_bar.addAction(self.clean_workspace_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.run_executable_action)
        self.tool_bar.addAction(self.launch_file_action)
        self.tool_bar.addAction(self.stop_task_action)
        self.tool_bar.addAction(self.omni_search_action)
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        # Optionally add the New Python Node and New C++ Node actions to the toolbar for quick access (if a toolbar is present in your UI setup).
        self.tool_bar.addAction(self.new_python_node_action)
        self.tool_bar.addAction(self.new_cpp_node_action)

    def _create_sidebar(self):
        from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QLabel
        from rosbuddy.ui.components.ai_assistant_widget import AIAssistantWidget

        # --- Activity Bar Items (icon-only, modern, with tooltips and shortcuts) ---
        # Robust fallback for all sidebar icons
        def get_sidebar_icon(key, fallback):
            icon = self.icon_manager.get_icon(key)
            if icon.isNull():
                icon = self.style().standardIcon(fallback)
            return icon

        self.sidebar_explorer_action.setIcon(get_sidebar_icon("explorer", QStyle.StandardPixmap.SP_DirIcon))
        self.sidebar_explorer_action.setToolTip("Workspace Explorer (Ctrl+1)")
        self.sidebar_explorer_action.setShortcut(QKeySequence("Ctrl+1"))
        self.sidebar_tool_bar.addAction(self.sidebar_explorer_action)

        self.sidebar_node_wizard_action.setIcon(get_sidebar_icon("node-wizard", QStyle.StandardPixmap.SP_FileIcon))
        self.sidebar_node_wizard_action.setToolTip("Node Wizard (Ctrl+2)")
        self.sidebar_node_wizard_action.setShortcut(QKeySequence("Ctrl+2"))
        self.sidebar_tool_bar.addAction(self.sidebar_node_wizard_action)

        self.sidebar_launch_runner_action.setIcon(get_sidebar_icon("launch-runner", QStyle.StandardPixmap.SP_MediaPlay))
        self.sidebar_launch_runner_action.setToolTip("Launch Runner (Ctrl+3)")
        self.sidebar_launch_runner_action.setShortcut(QKeySequence("Ctrl+3"))
        self.sidebar_tool_bar.addAction(self.sidebar_launch_runner_action)

        self.sidebar_ros_graph_action.setIcon(get_sidebar_icon("ros-graph", QStyle.StandardPixmap.SP_DriveNetIcon))
        self.sidebar_ros_graph_action.setToolTip("ROS Graph (Ctrl+4)")
        self.sidebar_ros_graph_action.setShortcut(QKeySequence("Ctrl+4"))
        self.sidebar_tool_bar.addAction(self.sidebar_ros_graph_action)

        self.sidebar_debug_view_action.setIcon(get_sidebar_icon("debug", QStyle.StandardPixmap.SP_MessageBoxQuestion))
        self.sidebar_debug_view_action.setToolTip("Debug (Ctrl+5)")
        self.sidebar_debug_view_action.setShortcut(QKeySequence("Ctrl+5"))
        self.sidebar_tool_bar.addAction(self.sidebar_debug_view_action)

        self.sidebar_tool_bar.addSeparator()

        self.sidebar_ai_assistant_action.setIcon(get_sidebar_icon("ai-assistant", QStyle.StandardPixmap.SP_MessageBoxQuestion))
        self.sidebar_ai_assistant_action.setToolTip("AI Assistant (Ctrl+6)")
        self.sidebar_ai_assistant_action.setShortcut(QKeySequence("Ctrl+6"))
        self.sidebar_tool_bar.addAction(self.sidebar_ai_assistant_action)

        self.sidebar_ai_agent_action.setIcon(get_sidebar_icon("ai-agent", QStyle.StandardPixmap.SP_CommandLink))
        self.sidebar_ai_agent_action.setToolTip("AI Agent Actions (Ctrl+7)")
        self.sidebar_ai_agent_action.setShortcut(QKeySequence("Ctrl+7"))
        self.sidebar_tool_bar.addAction(self.sidebar_ai_agent_action)

        self.sidebar_tool_bar.addSeparator()

        self.sidebar_ros_doctor_action.setIcon(get_sidebar_icon("ros-doctor", QStyle.StandardPixmap.SP_DialogHelpButton))
        self.sidebar_ros_doctor_action.setToolTip("ROS Doctor (Ctrl+8)")
        self.sidebar_ros_doctor_action.setShortcut(QKeySequence("Ctrl+8"))
        self.sidebar_tool_bar.addAction(self.sidebar_ros_doctor_action)

        self.sidebar_settings_action.setIcon(get_sidebar_icon("settings", QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.sidebar_settings_action.setToolTip("Settings (Ctrl+9)")
        self.sidebar_settings_action.setShortcut(QKeySequence("Ctrl+9"))
        self.sidebar_tool_bar.addAction(self.sidebar_settings_action)

        # --- Sidebar Content Area (contextual, modular) ---
        self.sidebar_content_widget = QWidget()
        self.sidebar_content_widget.setObjectName("sidebar_content_widget")
        self.sidebar_content_layout = QVBoxLayout(self.sidebar_content_widget)
        self.sidebar_content_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_content_layout.setSpacing(0)
        self.sidebar_search_bar = QLineEdit()
        self.sidebar_search_bar.setPlaceholderText("Search or filter...")
        self.sidebar_content_layout.addWidget(self.sidebar_search_bar)

        # Modular sidebar content stack
        self.sidebar_content_stack = QStackedWidget()
        from rosbuddy.ui.components.workspace_explorer import WorkspaceExplorer
        explorer_widget = WorkspaceExplorer(self.package_discovery, self.workspace_manager)
        self.sidebar_content_stack.addWidget(explorer_widget)  # index 0
        # Settings stub
        settings_stub = QWidget()
        settings_layout = QVBoxLayout(settings_stub)
        settings_layout.addWidget(QLabel("Settings sidebar stub"))
        settings_layout.addWidget(QPushButton("Settings Action"))
        self.sidebar_content_stack.addWidget(settings_stub)
        # AI Assistant: real widget
        ai_assistant_widget = AIAssistantWidget()
        self.sidebar_content_stack.addWidget(ai_assistant_widget)
        # All other sidebar views: use stubs (QWidget with label/button)
        for label in ["Node Wizard", "Debug", "Launch Runner", "ROS Graph", "AI Agent", "ROS Doctor"]:
            stub = QWidget()
            stub_layout = QVBoxLayout(stub)
            stub_layout.addWidget(QLabel(f"{label} sidebar stub"))
            stub_layout.addWidget(QPushButton(f"{label} Action"))
            self.sidebar_content_stack.addWidget(stub)
        self.sidebar_content_layout.addWidget(self.sidebar_content_stack)

        # Example contextual widgets (stubs for now)
        self.sidebar_explorer_view = self.workspace_explorer  # This is a WorkspaceExplorer instance
        # Do NOT call setAlignment on WorkspaceExplorer

        # Settings sidebar: minimal QWidget
        self.sidebar_settings_view = QWidget()
        settings_layout = QVBoxLayout(self.sidebar_settings_view)
        settings_label = QLabel("Settings Sidebar")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_button = QPushButton("Open Settings")
        settings_layout.addWidget(settings_label)
        settings_layout.addWidget(settings_button)
        settings_layout.addStretch(1)

        # AI Assistant sidebar: minimal QWidget
        self.sidebar_ai_assistant_view = QWidget()
        ai_assistant_layout = QVBoxLayout(self.sidebar_ai_assistant_view)
        ai_assistant_label = QLabel("AI Assistant Sidebar")
        ai_assistant_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ai_assistant_button = QPushButton("Ask AI")
        ai_assistant_layout.addWidget(ai_assistant_label)
        ai_assistant_layout.addWidget(ai_assistant_button)
        ai_assistant_layout.addStretch(1)

        # Node Wizard sidebar: minimal QWidget
        self.sidebar_node_wizard_view = QWidget()
        node_wizard_layout = QVBoxLayout(self.sidebar_node_wizard_view)
        node_wizard_label = QLabel("Node Wizard Sidebar")
        node_wizard_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        node_wizard_button = QPushButton("Start New Node Wizard")
        node_wizard_layout.addWidget(node_wizard_label)
        node_wizard_layout.addWidget(node_wizard_button)
        node_wizard_layout.addStretch(1)

        # Debug sidebar: minimal QWidget
        self.sidebar_debug_view = QWidget()
        debug_layout = QVBoxLayout(self.sidebar_debug_view)
        debug_label = QLabel("Debug Sidebar")
        debug_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        debug_button = QPushButton("Start Debug Session")
        debug_layout.addWidget(debug_label)
        debug_layout.addWidget(debug_button)
        debug_layout.addStretch(1)

        # Launch Runner sidebar: minimal QWidget
        self.sidebar_launch_runner_view = QWidget()
        launch_runner_layout = QVBoxLayout(self.sidebar_launch_runner_view)
        launch_runner_label = QLabel("Launch Runner Sidebar")
        launch_runner_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        launch_runner_button = QPushButton("Run Launch File")
        launch_runner_layout.addWidget(launch_runner_label)
        launch_runner_layout.addWidget(launch_runner_button)
        launch_runner_layout.addStretch(1)

        # ROS Graph sidebar: minimal QWidget
        self.sidebar_ros_graph_view = QWidget()
        ros_graph_layout = QVBoxLayout(self.sidebar_ros_graph_view)
        ros_graph_label = QLabel("ROS Graph Sidebar")
        ros_graph_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ros_graph_button = QPushButton("Show Graph")
        ros_graph_layout.addWidget(ros_graph_label)
        ros_graph_layout.addWidget(ros_graph_button)
        ros_graph_layout.addStretch(1)

        # AI Agent sidebar: minimal QWidget
        self.sidebar_ai_agent_view = QWidget()
        ai_agent_layout = QVBoxLayout(self.sidebar_ai_agent_view)
        ai_agent_label = QLabel("AI Agent Actions Sidebar")
        ai_agent_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ai_agent_button = QPushButton("Run Agent Action")
        ai_agent_layout.addWidget(ai_agent_label)
        ai_agent_layout.addWidget(ai_agent_button)
        ai_agent_layout.addStretch(1)

        # ROS Doctor sidebar: minimal QWidget
        self.sidebar_ros_doctor_view = QWidget()
        ros_doctor_layout = QVBoxLayout(self.sidebar_ros_doctor_view)
        ros_doctor_label = QLabel("ROS Doctor Sidebar")
        ros_doctor_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ros_doctor_button = QPushButton("Run Diagnostics")
        ros_doctor_layout.addWidget(ros_doctor_label)
        ros_doctor_layout.addWidget(ros_doctor_button)
        ros_doctor_layout.addStretch(1)

        # Add all sidebar widgets to the stack in the correct order
        self.sidebar_content_stack.addWidget(self.sidebar_explorer_view)   # index 0
        self.sidebar_content_stack.addWidget(self.sidebar_settings_view)   # index 1
        self.sidebar_content_stack.addWidget(self.sidebar_ai_assistant_view)   # index 2
        self.sidebar_content_stack.addWidget(self.sidebar_node_wizard_view)    # index 3
        self.sidebar_content_stack.addWidget(self.sidebar_debug_view)          # index 4
        self.sidebar_content_stack.addWidget(self.sidebar_launch_runner_view)  # index 5
        self.sidebar_content_stack.addWidget(self.sidebar_ros_graph_view)      # index 6
        self.sidebar_content_stack.addWidget(self.sidebar_ai_agent_view)       # index 7
        self.sidebar_content_stack.addWidget(self.sidebar_ros_doctor_view)     # index 8

        # Node Wizard sidebar: replace stub with a minimal QWidget for future expansion
        from PyQt6.QtWidgets import QVBoxLayout, QPushButton
        self.sidebar_node_wizard_view = QWidget()
        node_wizard_layout = QVBoxLayout(self.sidebar_node_wizard_view)
        node_wizard_label = QLabel("Node Wizard Sidebar")
        node_wizard_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        node_wizard_button = QPushButton("Start New Node Wizard")
        node_wizard_layout.addWidget(node_wizard_label)
        node_wizard_layout.addWidget(node_wizard_button)
        node_wizard_layout.addStretch(1)

        self.sidebar_content_stack.insertWidget(3, self.sidebar_node_wizard_view)  # index 3 for Node Wizard

        # AI Assistant sidebar: replace stub with a minimal QWidget for future expansion
        from PyQt6.QtWidgets import QVBoxLayout, QPushButton
        self.sidebar_ai_assistant_view = QWidget()
        ai_assistant_layout = QVBoxLayout(self.sidebar_ai_assistant_view)
        ai_assistant_label = QLabel("AI Assistant Sidebar")
        ai_assistant_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ai_assistant_button = QPushButton("Ask AI")
        ai_assistant_layout.addWidget(ai_assistant_label)
        ai_assistant_layout.addWidget(ai_assistant_button)
        ai_assistant_layout.addStretch(1)

        self.sidebar_content_stack.insertWidget(2, self.sidebar_ai_assistant_view)  # index 2 for AI Assistant

        # Debug sidebar: replace stub with a minimal QWidget for future expansion
        self.sidebar_debug_view = QWidget()
        debug_layout = QVBoxLayout(self.sidebar_debug_view)
        debug_label = QLabel("Debug Sidebar")
        debug_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        debug_button = QPushButton("Start Debug Session")
        debug_layout.addWidget(debug_label)
        debug_layout.addWidget(debug_button)
        debug_layout.addStretch(1)
        self.sidebar_content_stack.insertWidget(4, self.sidebar_debug_view)  # index 4 for Debug

        # Launch Runner sidebar: replace stub with a minimal QWidget for future expansion
        self.sidebar_launch_runner_view = QWidget()
        launch_runner_layout = QVBoxLayout(self.sidebar_launch_runner_view)
        launch_runner_label = QLabel("Launch Runner Sidebar")
        launch_runner_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        launch_runner_button = QPushButton("Run Launch File")
        launch_runner_layout.addWidget(launch_runner_label)
        launch_runner_layout.addWidget(launch_runner_button)
        launch_runner_layout.addStretch(1)
        self.sidebar_content_stack.insertWidget(5, self.sidebar_launch_runner_view)  # index 5 for Launch Runner

        # ROS Graph sidebar: minimal QWidget
        self.sidebar_ros_graph_view = QWidget()
        ros_graph_layout = QVBoxLayout(self.sidebar_ros_graph_view)
        ros_graph_label = QLabel("ROS Graph Sidebar")
        ros_graph_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ros_graph_button = QPushButton("Show Graph")
        ros_graph_layout.addWidget(ros_graph_label)
        ros_graph_layout.addWidget(ros_graph_button)
        ros_graph_layout.addStretch(1)
        self.sidebar_content_stack.insertWidget(6, self.sidebar_ros_graph_view)  # index 6

        # AI Agent sidebar: minimal QWidget
        self.sidebar_ai_agent_view = QWidget()
        ai_agent_layout = QVBoxLayout(self.sidebar_ai_agent_view)
        ai_agent_label = QLabel("AI Agent Actions Sidebar")
        ai_agent_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ai_agent_button = QPushButton("Run Agent Action")
        ai_agent_layout.addWidget(ai_agent_label)
        ai_agent_layout.addWidget(ai_agent_button)
        ai_agent_layout.addStretch(1)
        self.sidebar_content_stack.insertWidget(7, self.sidebar_ai_agent_view)  # index 7

        # ROS Doctor sidebar: minimal QWidget
        self.sidebar_ros_doctor_view = QWidget()
        ros_doctor_layout = QVBoxLayout(self.sidebar_ros_doctor_view)
        ros_doctor_label = QLabel("ROS Doctor Sidebar")
        ros_doctor_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        ros_doctor_button = QPushButton("Run Diagnostics")
        ros_doctor_layout.addWidget(ros_doctor_label)
        ros_doctor_layout.addWidget(ros_doctor_button)
        ros_doctor_layout.addStretch(1)
        self.sidebar_content_stack.insertWidget(8, self.sidebar_ros_doctor_view)  # index 8

        # Map sidebar actions to stack indexes for context switching
        self._sidebar_action_to_stack_index = {
            self.sidebar_explorer_action: 0,
            self.sidebar_settings_action: 1,
            self.sidebar_ai_assistant_action: 2,
            self.sidebar_node_wizard_action: 3,
            self.sidebar_debug_view_action: 4,
            self.sidebar_launch_runner_action: 5,
            self.sidebar_ros_graph_action: 6,
            self.sidebar_ai_agent_action: 7,
            self.sidebar_ros_doctor_action: 8,
        }

        # Add the sidebar content widget to the main splitter (left pane, after Activity Bar)
        # Remove Workspace Explorer from left pane, add sidebar_content_widget instead
        # (Assume main_splitter is set up in _create_central_widget)
        if hasattr(self, 'main_splitter'):
            self.main_splitter.insertWidget(0, self.sidebar_content_widget)
            self.main_splitter.setSizes([250, 950])

        # Connect sidebar actions to context switcher (fix lambda late binding)
        for action, idx in self._sidebar_action_to_stack_index.items():
            def make_switcher(i):
                return lambda checked=False, i=i: self.sidebar_content_stack.setCurrentIndex(i)
            action.triggered.connect(make_switcher(idx))

        # Set default sidebar content
        self.sidebar_content_stack.setCurrentIndex(0)

        # --- Highlight active icon ---
        # Add logic to visually highlight the active sidebar action (e.g., by changing background or using a colored bar)
        # This can be done in the slot that handles sidebar action triggers

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.active_ws_label = QLabel("Active Workspace: None")
        self.status_bar.addPermanentWidget(self.active_ws_label)

        # AI Assistant Status (as per report)
        self.ai_status_label = QLabel("◉ AI Assistant [Online]") # Default
        self.ai_status_label.setStyleSheet("color: lightgreen; margin-left: 10px; margin-right: 5px;")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        # Initial message will be set by update_active_workspace_display

    def _create_central_widget(self):
        logger.debug(f"_create_central_widget: Method START.")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout for the central widget (everything to the right of the sidebar)
        main_hbox_layout = QHBoxLayout(self.central_widget) 
        main_hbox_layout.setContentsMargins(0, 0, 0, 0) # No margins for the main layout

        # Main horizontal splitter: Workspace Explorer | (ActiveViewTabs / OutputPanel)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_hbox_layout.addWidget(self.main_splitter)

        # Left side of main_splitter: Workspace Explorer
        self.main_splitter.addWidget(self.workspace_explorer)

        # Right side of main_splitter: Container for Active View Tabs and Output Panel
        right_primary_pane_container = QWidget()
        right_primary_pane_layout = QVBoxLayout(right_primary_pane_container)
        right_primary_pane_layout.setContentsMargins(0, 0, 0, 0)
        right_primary_pane_layout.setSpacing(0) # No spacing between tabs and output

        # Container for tab widget and empty placeholder (to toggle visibility)
        self.tab_area_container = QWidget()
        self.tab_area_layout = QVBoxLayout(self.tab_area_container) # Or QStackedLayout
        self.tab_area_layout.setContentsMargins(0,0,0,0)
        self.tab_area_layout.addWidget(self.active_view_tabs)
        self.tab_area_layout.addWidget(self._empty_tab_placeholder)
        self._empty_tab_placeholder.hide() # Initially hidden
        right_primary_pane_layout.addWidget(self.tab_area_container, 1) # Stretch factor 1

        # Output Panel (below active view tabs)
        right_primary_pane_layout.addWidget(self.output_panel, 0) # Stretch factor 0 (or smaller)

        self.main_splitter.addWidget(right_primary_pane_container)
        self.main_splitter.setSizes([250, 950]) # Initial sizes for Workspace Explorer and Right Pane
        self.main_splitter.setOpaqueResize(False)

        logger.debug(f"_create_central_widget: Method END. Splitter children count: {self.main_splitter.count()}")
        main_hbox_layout.setSpacing(0)

    def _update_empty_tab_placeholder_visibility(self):
        if self.active_view_tabs.count() == 0:
            self.active_view_tabs.hide()
            self._empty_tab_placeholder.show()
        else:
            self._empty_tab_placeholder.hide()
            self.active_view_tabs.show()

    def update_active_workspace_display(self, action_description: Optional[str] = None):
        logger.debug(f"update_active_workspace_display called. Current action_desc: '{self.current_action_description}', New event_desc: '{action_description}'") # <-- ADD THIS LINE
        workspace_path = self.workspace_manager.get_active_workspace_path()
        is_ws_active = bool(workspace_path)
        worker_active = bool(self.current_worker and self.current_worker.isRunning())

        ros_process_active = False
        if self.running_ros_process:
            try:
                poll_status = self.running_ros_process.poll()
                logger.debug(f"update_active_workspace_display: running_ros_process PID {self.running_ros_process.pid if self.running_ros_process else 'N/A'} poll() is {poll_status}")
                if poll_status is None:
                    ros_process_active = True
                else:
                    logger.info(f"update_active_workspace_display: ROS process (PID: {self.running_ros_process.pid if self.running_ros_process else 'N/A'}) terminated (poll={poll_status}). Clearing reference.")
                    self.running_ros_process = None
            except Exception as e:
                logger.error(f"Error checking running_ros_process.poll(): {e}", exc_info=True)
                self.running_ros_process = None

        overall_busy = worker_active or ros_process_active
        logger.debug(f"update_active_workspace_display: is_ws_active={is_ws_active}, worker_active={worker_active}, ros_process_active={ros_process_active}, overall_busy={overall_busy}")

        self.new_workspace_action.setEnabled(not overall_busy)
        self.open_workspace_action.setEnabled(not overall_busy)
        actions_requiring_ws = [
            self.create_package_action, self.build_workspace_action, self.clean_workspace_action,
            self.run_executable_action, self.launch_file_action
        ]
        actions_requiring_ws.append(self.refresh_workspace_action) # Add refresh action here
        for act in actions_requiring_ws:
            act.setEnabled(is_ws_active and not overall_busy)
        self.stop_task_action.setEnabled(ros_process_active)
        logger.debug(f"update_active_workspace_display: stop_task_action.setEnabled({ros_process_active})")

        # Status bar message logic:
        # 'action_description' passed to this function usually indicates an event that just occurred or a state change.
        # 'self.current_action_description' holds the name of the task that *made* the UI busy.
        if overall_busy:
            # If action_description is from a *new* task starting (e.g., "Build Workspace", not "Build Workspace Finished")
            if action_description and not any(s in action_description.lower() for s in ["finished", "failed", "completed", "active", "ready"]):
                self.current_action_description = action_description # This is the new task name
                self.status_bar.showMessage(f"{self.current_action_description} in progress...", 0)
            elif self.current_action_description: # A task is already in progress
                self.status_bar.showMessage(f"{self.current_action_description} in progress...", 0)
            else: # Busy, but no specific task name known (e.g. only ros_process_active after app restart)
                self.status_bar.showMessage("Processing...", 0)
        else: # Not overall_busy
            if action_description: # A specific message for non-busy state (e.g., "Task X Finished", "Ready")
                self.status_bar.showMessage(action_description, 5000)
                # If this message indicates a task just finished, clear current_action_description
                if self.current_action_description and any(s in action_description.lower() for s in ["finished", "failed", "completed", "cancelled"]):
                    self.current_action_description = ""
            else: # Generic ready message
                ws_display_name = str(workspace_path.name) if workspace_path else "None"
                self.active_ws_label.setText(f"Active Workspace: {ws_display_name}")
                self.status_bar.showMessage(f"Ready. Active WS: {ws_display_name}", 5000)
                if self.current_action_description: # If we became not_busy but current_action_description wasn't cleared by a "finished" message
                    self.current_action_description = "" # Clear it now

        # Update permanent widget for active workspace path name
        ws_display_name_perm = str(workspace_path.name) if workspace_path else "None"
        self.active_ws_label.setText(f"Active Workspace: {ws_display_name_perm}")
        
        # --- Conditionally update workspace explorer ---
        if hasattr(self, 'workspace_explorer'):
            self._update_workspace_explorer() # Call MainWindow's own method for detailed view
        QApplication.processEvents() # Ensure UI updates are processed

    def _update_workspace_explorer(self):
        """Populates/Updates the workspace explorer QTreeView with the active workspace and its packages."""
        logger.debug("_update_workspace_explorer: Method START.") # <-- ADD THIS LINE
        # Clear previous items from the model
        self.workspace_explorer.model.clear()
        # self.workspace_explorer_model.setHorizontalHeaderLabels(['Workspace Structure']) # Optional

        active_ws_path = self.workspace_manager.get_active_workspace_path()

        if not active_ws_path:
            root_item = QStandardItem("No Active Workspace")
            root_item.setEditable(False)
            self.workspace_explorer.model.appendRow(root_item)
            logger.debug("Workspace explorer updated: No active workspace.")
            self.workspace_explorer.view.header().setVisible(False)
            return

        # Create a root item for the workspace name
        ws_name = active_ws_path.name
        ws_root_item = QStandardItem(f"Workspace: {ws_name}")
        ws_root_item.setEditable(False)
        # icon_folder = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        # ws_root_item.setIcon(icon_folder)
        self.workspace_explorer.model.appendRow(ws_root_item)

        # Discover packages
        try:
            discovered_packages = self.package_discovery.find_packages_in_active_workspace()
            if discovered_packages:
                # "Packages" parent item under the workspace root
                packages_parent_item = QStandardItem("Packages")
                packages_parent_item.setEditable(False)
                # icon_package_folder = self.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon) # Example
                # packages_parent_item.setIcon(icon_package_folder)
                ws_root_item.appendRow(packages_parent_item)

                for pkg_info in discovered_packages:
                    package_item = QStandardItem(pkg_info.name)
                    package_item.setEditable(False)
                    package_item.setData(pkg_info, Qt.ItemDataRole.UserRole + 1) # Store PackageInfo
                    # Populate package contents recursively
                    self._populate_directory_recursively(package_item, pkg_info.path)
                    packages_parent_item.appendRow(package_item)
                logger.debug(f"Workspace explorer updated with {len(discovered_packages)} packages.")
                self.workspace_explorer.view.expand(packages_parent_item.index()) # Use .view.expand()

            else:
                no_packages_item = QStandardItem("No packages found in src/")
                no_packages_item.setEditable(False)
                ws_root_item.appendRow(no_packages_item)
                logger.info("Workspace explorer: Added 'No packages found in src/' under workspace node.")
            self.workspace_explorer.view.expand(ws_root_item.index()) # Use .view.expand()
        except Exception as e:
            error_msg = f"Error during package discovery or populating tree: {e}"
            logger.error(error_msg, exc_info=True)
            if self.output_display: self.output_display.append_text(f"[ERROR] {error_msg}")
            error_item = QStandardItem("Error loading packages")
            error_item.setEditable(False)
            if ws_root_item: ws_root_item.appendRow(error_item) # Check if ws_root_item exists
            
        
        self.workspace_explorer.view.header().setVisible(False)

    def _populate_directory_recursively(self, parent_item: QStandardItem, directory_path: pathlib.Path):
        """
        Recursively populates a QStandardItem with the contents of a directory.
        """
        try:
            # Sort entries: directories first, then files, then alphabetically
            entries = sorted(
                list(directory_path.iterdir()),
                key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError:
            logger.warning(f"Permission denied when trying to list directory: {directory_path}")
            perm_denied_item = QStandardItem(self.icon_manager.get_icon("dialog-error", QStyle.StandardPixmap.SP_MessageBoxCritical),
                                             f"[Permission Denied] {directory_path.name}")
            perm_denied_item.setEditable(False)
            parent_item.appendRow(perm_denied_item)
            return
        except FileNotFoundError: # Should not happen if directory_path comes from a valid PackageInfo
            logger.warning(f"Directory not found during population: {directory_path}")
            return

        for entry_path in entries:
            # Skip common hidden/temporary/build files/folders for a cleaner view
            if entry_path.name.startswith('.') or \
               entry_path.name in ['__pycache__', 'build', 'install', 'log', 
                                    'target', 'node_modules', '.vscode', '.idea', 'bin', 'lib', 'obj', 'Debug', 'Release']: # Added more common ignores
                continue

            item_name = entry_path.name
            item: QStandardItem

            if entry_path.is_dir():
                icon = self.icon_manager.get_icon("folder", QStyle.StandardPixmap.SP_DirIcon)
                item = QStandardItem(icon, item_name)
                item.setEditable(False)
                item.setData(str(entry_path), Qt.ItemDataRole.UserRole + 3) # UserRole + 3 for folder path (for future use)
                parent_item.appendRow(item)
                self._populate_directory_recursively(item, entry_path) # Recurse
            elif entry_path.is_file():
                icon = self.icon_manager.get_icon("text-x-generic", QStyle.StandardPixmap.SP_FileIcon)
                item = QStandardItem(icon, item_name)
                item.setEditable(False)
                item.setData(str(entry_path), Qt.ItemDataRole.UserRole + 2) # UserRole + 2 for file path (for opening)
                parent_item.appendRow(item)

    # --- Custom Slot for New Python Node ---
    def on_new_python_node(self):
        """Handler to create a new Python node in a selected package."""
        try:
            dialog = NodeCreatorDialog(self.package_discovery, parent=self, build_type="ament_python")
            if dialog.exec() != QDialog.DialogCode.Accepted:
                self.output_display.append_text("[INFO] Node creation cancelled.")
                return
                
            # Get dialog data and validate
            data = dialog.get_data()
            pkg_name = data['package_name']
            node_name = data['node_name']
            node_type = data['node_type']
            topic_name = data['topic_name']
            msg_type = data['message_type']
            
            if not all([pkg_name, node_name, node_type, topic_name, msg_type]):
                QMessageBox.critical(self, "Node Creation Error", "All fields must be filled.")
                return

            # Find package info
            pkg_info = next((p for p in self.package_discovery.find_packages_in_active_workspace() if p.name == pkg_name), None)
            if not pkg_info:
                QMessageBox.critical(self, "Node Creation Error", f"Package '{pkg_name}' not found.")
                return

            pkg_path = pkg_info.path
            module_dir = pkg_path / pkg_name
            module_dir.mkdir(exist_ok=True)
            
            # Ensure __init__.py exists
            init_file = module_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                
            # Create node file
            node_file_path = module_dir / f"{node_name}.py"
            node_gen = NodeGenerator()
            node_code = node_gen.generate_node({
                "type": node_type,
                "name": node_name,
                "msg_type": msg_type,
                "topic": topic_name
            })
            with open(node_file_path, "w", encoding="utf-8") as f:
                f.write(node_code)
            self.output_display.append_text(f"[INFO] Created node file: {node_file_path}")
                
            # Update setup.py
            setup_py_path = pkg_path / "setup.py"
            if setup_py_path.exists():
                if self._update_setup_py_entry_point(setup_py_path, pkg_name, node_name):
                    self.output_display.append_text("[INFO] Updated setup.py with new entry point")
                else:
                    self.output_display.append_text("[WARNING] Could not update setup.py automatically")
                    
            # Update package.xml dependencies
            package_xml_path = pkg_path / "package.xml"
            if package_xml_path.exists():
                try:
                    tree = ET.parse(str(package_xml_path))
                    root = tree.getroot()
                    
                    # Add required Python ROS2 dependencies
                    msg_pkg = msg_type.split("/")[0]
                    for dep in ["rclpy", msg_pkg]:
                        add_unique_dependency_to_package_xml(root, dep, dep_type="depend")
                    
                    tree.write(str(package_xml_path), encoding="utf-8", xml_declaration=True)
                    self.output_display.append_text("[INFO] Updated package.xml dependencies")
                except Exception as e:
                    logger.error(f"Failed to update package.xml: {e}", exc_info=True)
                    self.output_display.append_text(f"[WARNING] Failed to update dependencies in package.xml: {e}")

            # Feedback and refresh
            self.output_display.append_text(f"[INFO] Successfully created node '{node_name}' in package '{pkg_name}'")
            QMessageBox.information(self, "Node Created", f"Node '{node_name}' created in package '{pkg_name}'")
            self.on_refresh_workspace_explorer()
            
        except Exception as e:
            logger.error(f"Error creating new Python node: {e}", exc_info=True)
            QMessageBox.critical(self, "Node Creation Error", f"Failed to create node: {e}")

    def _update_setup_py_entry_point(self, setup_py_path: Path, package_name: str, node_executable_name: str) -> bool:
        """
        Updates the setup.py file to include a new console script entry point.
        Uses ast to parse and modify the setup.py file.
        """
        try:
            with open(setup_py_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            new_entry_point_str = f"{node_executable_name} = {package_name}.{node_executable_name}:main"

            class EntryPointTransformer(ast.NodeTransformer):
                def __init__(self, new_entry_val):
                    super().__init__()
                    self.new_entry_str = new_entry_val
                    self.modified_in_setup = False

                def visit_Call(self, node):
                    # Check if this is the setup() call
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        entry_points_kw = None
                        for kw_idx, kw in enumerate(node.keywords):
                            if kw.arg == 'entry_points':
                                entry_points_kw = kw
                                break
                        
                        if entry_points_kw: # 'entry_points' argument exists
                            if isinstance(entry_points_kw.value, ast.Dict):
                                ep_dict = entry_points_kw.value
                                console_scripts_list_node = None
                                cs_key_exists_in_dict = False
                                # Find 'console_scripts' key in the entry_points Dict
                                for i, key_node_in_dict in enumerate(ep_dict.keys):
                                    if isinstance(key_node_in_dict, ast.Constant) and key_node_in_dict.value == 'console_scripts':
                                        cs_key_exists_in_dict = True
                                        if isinstance(ep_dict.values[i], ast.List):
                                            console_scripts_list_node = ep_dict.values[i]
                                        else:
                                            # 'console_scripts' value is not a List, log and skip modification
                                            logger.warning(f"setup.py: 'console_scripts' in 'entry_points' is not a List. Cannot modify.")
                                            return node # Return node unchanged
                                        break
                                
                                if console_scripts_list_node: # 'console_scripts' key and List found
                                    # Add new entry point if it doesn't exist
                                    if not any(isinstance(elt, ast.Constant) and elt.value == self.new_entry_str for elt in console_scripts_list_node.elts):
                                        console_scripts_list_node.elts.append(ast.Constant(value=self.new_entry_str))
                                        self.modified_in_setup = True
                                elif cs_key_exists_in_dict: # 'console_scripts' key exists but value wasn't a list (handled above)
                                    pass # Should have been caught by "not a List"
                                else: # 'console_scripts' key does not exist in entry_points Dict, add it
                                    ep_dict.keys.append(ast.Constant(value='console_scripts'))
                                    new_cs_list = ast.List(elts=[ast.Constant(value=self.new_entry_str)], ctx=ast.Load())
                                    ep_dict.values.append(new_cs_list)
                                    self.modified_in_setup = True
                            else: # 'entry_points' value is not a Dict
                                logger.warning(f"setup.py: 'entry_points' value is not a Dict. Cannot modify.")
                                return node # Return node unchanged
                        else: # 'entry_points' argument does not exist, add it
                            console_scripts_list_node = ast.List(elts=[ast.Constant(value=self.new_entry_str)], ctx=ast.Load())
                            ep_dict_node = ast.Dict(keys=[ast.Constant(value='console_scripts')], values=[console_scripts_list_node])
                            node.keywords.append(ast.keyword(arg='entry_points', value=ep_dict_node))
                            self.modified_in_setup = True
                        return node # Return the (potentially modified) setup call node
                    return self.generic_visit(node) # Visit other nodes

            transformer = EntryPointTransformer(new_entry_point_str)
            new_tree = transformer.visit(tree)
            
            if transformer.modified_in_setup:
                new_source_code = astor.to_source(new_tree)
                with open(setup_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_source_code)
                logger.info(f"Successfully updated setup.py with entry point: {new_entry_point_str}")
                return True
            else:
                # Check if the entry point string is already in the file literally
                # This covers cases where AST modification might not occur due to non-standard setup.py or if already present
                with open(setup_py_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                if new_entry_point_str in current_content:
                    logger.info(f"Entry point '{new_entry_point_str}' already exists in setup.py.")
                    return True # Consider it successful if already present
                logger.info(f"setup.py: No AST modifications made for entry point '{new_entry_point_str}'. Structure might be non-standard or entry point already exists in an unusual format.")
                return False # No modification made and not found literally

        except FileNotFoundError:
            logger.error(f"setup.py not found at {setup_py_path}")
            QMessageBox.warning(self, "File Error", f"setup.py not found at {setup_py_path}")
            return False
        except Exception as e:
            logger.error(f"Error updating setup.py at {setup_py_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Update Error", f"Could not update setup.py: {e}")
            return False

    def on_new_cpp_node(self):
        """Handler to create a new C++ node in a selected package."""
        logger.info("New C++ Node action triggered.")
        if self.current_worker and self.current_worker.isRunning():  # Standard busy check
            QMessageBox.warning(self, "Busy", "Another task is in progress.")
            return

        active_ws_src_path = self.workspace_manager.get_active_workspace_src_path()
        if not active_ws_src_path:  # Check for active workspace
            QMessageBox.warning(self, "Error", "No active CMake workspace. Please open or create one first.")
            logger.warning("New C++ Node attempted with no active workspace.")
            return

        dialog = NodeCreatorDialog(self.package_discovery, parent=self, build_type="ament_cmake")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.output_display.append_text("[INFO] C++ Node creation cancelled.")
            return

        try:
            data = dialog.get_data()
            pkg_name = data['package_name']
            node_name = data['node_name']
            node_type = data['node_type']
            topic_name = data['topic_name']
            msg_type = data['message_type']

            if not (pkg_name and node_name and node_type and topic_name and msg_type):
                QMessageBox.critical(self, "Node Creation Error", "All fields must be filled.")
                return

            # Find package info and validate it's an ament_cmake package
            pkg_info = next((p for p in self.package_discovery.find_packages_in_active_workspace() if p.name == pkg_name), None)
            if not pkg_info:
                QMessageBox.critical(self, "Node Creation Error", f"Package '{pkg_name}' not found.")
                return
            
            if pkg_info.build_type != "ament_cmake":
                QMessageBox.critical(self, "Node Creation Error", f"Package '{pkg_name}' is not a C++ package (build_type is not ament_cmake).")
                return

            pkg_path = pkg_info.path
            include_dir = pkg_path / "include" / pkg_name
            src_dir = pkg_path / "src"
            include_dir.mkdir(parents=True, exist_ok=True)
            src_dir.mkdir(parents=True, exist_ok=True)

            # Generate node files
            from rosbuddy.code_generation.cpp_node_generator import CppNodeGenerator
            node_gen = CppNodeGenerator()
            node_code = node_gen.generate_node_files_content({
                "package_name": pkg_name,
                "node_name": node_name,
                "role": node_type,
                "topic_name": topic_name,
                "message_type": msg_type
            })

            hpp_file_path = include_dir / f"{node_name}.hpp"
            cpp_file_path = src_dir / f"{node_name}.cpp"

            # Write the header and source files
            with open(hpp_file_path, "w", encoding="utf-8") as f:
                f.write(node_code["hpp_content"])
            with open(cpp_file_path, "w", encoding="utf-8") as f:
                f.write(node_code["cpp_content"])

            # Update CMakeLists.txt to include the new node (robust version)
            from rosbuddy.file_generators.cmake_modifier import update_cmakelists_for_new_cpp_node
            cmakelists_path = pkg_path / "CMakeLists.txt"
            msg_pkg = msg_type.split("/")[0]
            additional_deps = [msg_pkg] if msg_pkg != "std_msgs" else []  # std_msgs is usually present, but add if needed
            update_cmakelists_for_new_cpp_node(
                cmakelists_path,
                pkg_name=pkg_name,
                node_name=node_name,
                class_name=node_name.title().replace('_', ''),
                additional_message_dependencies=["rclcpp"] + additional_deps
            )

            # Update package.xml for rclcpp, ament_cmake, and message dependency
            package_xml_path = pkg_path / "package.xml"
            if package_xml_path.exists():
                import xml.etree.ElementTree as ET
                from rosbuddy.file_generators.package_xml_modifier import add_unique_dependency_to_package_xml
                tree = ET.parse(str(package_xml_path))
                root = tree.getroot()
                # Add ament_cmake as buildtool_depend
                from rosbuddy.file_generators.package_xml_modifier import add_dependency_to_package_xml
                add_dependency_to_package_xml(package_xml_path, "ament_cmake", dep_type="buildtool_depend")
                # Add rclcpp and message type dependency
                add_unique_dependency_to_package_xml(root, "rclcpp", dep_type="depend")
                add_unique_dependency_to_package_xml(root, msg_pkg, dep_type="depend")
                tree.write(str(package_xml_path), encoding="utf-8", xml_declaration=True)

            # Feedback and refresh
            self.output_display.append_text(f"[INFO] Created C++ node '{node_name}' in package '{pkg_name}'")
            QMessageBox.information(self, "Node Created", f"C++ node '{node_name}' created in package '{pkg_name}'")
            self.on_refresh_workspace_explorer()

        except Exception as e:
            logger.error(f"Error creating new C++ node: {e}", exc_info=True)
            QMessageBox.critical(self, "Node Creation Error", f"Failed to create node: {e}")

    def on_refresh_workspace_explorer(self):
        """Refresh the workspace explorer view (stub for UI/test stability)."""
        if hasattr(self, '_update_workspace_explorer'):
            self._update_workspace_explorer()
        self.update_active_workspace_display("Workspace Explorer Refreshed")

    # --- Placeholder Asset Creation/Editing Slots ---
    def on_new_node(self):
        """Placeholder for creating a new ROS node."""
        logger.info("New Node action triggered.")
        self.output_display.append_text("[INFO] Action: New Node... (Not yet implemented)")
        QMessageBox.information(self, "New Node", "Functionality to create a new node is not yet implemented.")
        # Example of how you might use NodeCreatorDialog:
        # dialog = NodeCreatorDialog(parent=self)
        # if dialog.exec() == QDialog.DialogCode.Accepted:
        #     node_data = dialog.get_node_data()
        #     if node_data:
        #         # Process node_data (e.g., generate files)
        #         self.output_display.append_text(f"[INFO] New node '{node_data['node_name']}' creation initiated (logic pending).")
        # else:
        #     self.output_display.append_text("[INFO] New node creation cancelled.")

    def on_new_launch_file(self):
        """Placeholder for creating a new ROS launch file."""
        logger.info("New Launch File action triggered.")
        self.output_display.append_text("[INFO] Action: New Launch File... (Not yet implemented)")
        QMessageBox.information(self, "New Launch File", "Functionality to create a new launch file is not yet implemented.")
        # Example: dialog = LaunchFileComposerDialog(parent=self) ...

    def on_new_msg_srv_action(self):
        """Allows creating a new ROS message, service, or action definition in the selected package."""
        logger.info("New Msg/Srv/Action action triggered.")
        self.output_display.append_text("[INFO] Action: New Msg/Srv/Action...")

        selected_pkg_info = self._get_selected_package_info_from_explorer()
        if not selected_pkg_info:
            QMessageBox.warning(self, "No Package Selected",
                                "Please select a package in the Workspace Explorer to add an interface to.")
            self.output_display.append_text("[WARN] No package selected for new interface.")
            return

        dialog = MsgSrvActionEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            iface_def = dialog.get_data()
            if iface_def:
                logger.info(f"Interface definition received: {iface_def.file_name} for package {selected_pkg_info.name}")
                self.output_display.append_text(f"[INFO] Creating interface '{iface_def.file_name}' in package '{selected_pkg_info.name}'...")

                # 1. Create the interface file
                interface_file_full_path = selected_pkg_info.path / iface_def.relative_path
                try:
                    interface_file_full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(interface_file_full_path, "w", encoding="utf-8") as f:
                        f.write(iface_def.content)
                    logger.info(f"Successfully created interface file: {interface_file_full_path}")
                    self.output_display.append_text(f"[INFO] Created file: {iface_def.relative_path}")

                    # 2. Modify existing package.xml
                    package_xml_path = selected_pkg_info.path / "package.xml"
                    if package_xml_path.exists():
                        # Pass only the dependencies list, not the InterfaceFileDefinition object
                        success_xml = update_package_xml_for_new_interface(package_xml_path, iface_def.interface_package_dependencies)
                        if success_xml:
                            logger.info(f"Successfully updated {package_xml_path} for new interface.")
                            self.output_display.append_text(f"[INFO] Updated {package_xml_path.name}.")
                        else:
                            logger.error(f"Failed to update {package_xml_path}.")
                            self.output_display.append_text(f"[ERROR] Failed to update {package_xml_path.name}.")
                            QMessageBox.warning(self, "Update Error", f"Failed to update {package_xml_path.name}. Check logs.")
                    else:
                        logger.warning(f"package.xml not found at {package_xml_path} for package {selected_pkg_info.name}. Skipping update.")
                        self.output_display.append_text(f"[WARN] {package_xml_path.name} not found. Skipping update.")

                    # 3. Advise for CMakeLists.txt if ament_cmake
                    cmakelists_path = selected_pkg_info.path / "CMakeLists.txt"
                    cmake_generated = False
                    cmake_updated = False
                    if selected_pkg_info.build_type == "ament_cmake":
                        if not cmakelists_path.exists():
                            # Try to build a minimal PackageConfig for this package
                            pkg_config = PackageConfig(
                                name=selected_pkg_info.name,
                                build_type=selected_pkg_info.build_type,
                                dependencies=[Dependency(dep) for dep in iface_def.interface_package_dependencies],
                                interface_definitions=[iface_def],
                                library_targets=[],
                                executable_targets=[],
                                launch_configurations=[],
                                config_files_paths=[]
                            )
                            cmake_content = generate_cmake_lists_content(pkg_config)
                            with open(cmakelists_path, "w", encoding="utf-8") as f:
                                f.write(cmake_content)
                            logger.info(f"Generated new CMakeLists.txt for {selected_pkg_info.name}.")
                            self.output_display.append_text(f"[INFO] Generated new CMakeLists.txt for {selected_pkg_info.name}.")
                            cmake_generated = True
                        if cmakelists_path.exists():
                            cmake_status = update_cmakelists_for_new_interface(cmakelists_path, iface_def, selected_pkg_info.name)
                            cmake_updated = cmake_status == CMakeUpdateStatus.UPDATED
                            if cmake_status == CMakeUpdateStatus.UPDATED:
                                self.output_display.append_text(f"[INFO] CMakeLists.txt for {selected_pkg_info.name} was updated.")
                            elif cmake_status == CMakeUpdateStatus.NO_CHANGES:
                                self.output_display.append_text(f"[INFO] CMakeLists.txt for {selected_pkg_info.name} was already up to date.")
                            else:
                                self.output_display.append_text(f"[ERROR] Failed to update CMakeLists.txt for {selected_pkg_info.name}.")
                        # Only show manual message if neither generated nor updated
                        if not (cmake_generated or cmake_updated):
                            msg = (f"Interface file '{iface_def.file_name}' created and package.xml updated.\n\n"
                                   f"Since '{selected_pkg_info.name}' is an ament_cmake package, "
                                   f"please manually update its CMakeLists.txt to include:\n"
                                   f"  - '{iface_def.relative_path}' in the rosidl_generate_interfaces() call.\n"
                                   f"  - Any new dependencies (e.g., {', '.join(iface_def.interface_package_dependencies) or 'none'}) in find_package().")
                            QMessageBox.information(self, "Manual CMake Update Required", msg)
                            # Removed duplicate/obsolete manual review message after refactor.
                        elif cmake_generated or cmake_updated:
                            msg = (f"Interface file '{iface_def.file_name}' created, package.xml updated, and CMakeLists.txt automatically generated/updated for '{selected_pkg_info.name}'.")
                            QMessageBox.information(self, "CMakeLists.txt Updated", msg)
                            self.output_display.append_text(f"[INFO] CMakeLists.txt for {selected_pkg_info.name} was automatically generated/updated.")
                    # Generate CMakeLists.txt if it doesn't exist
                    cmakelists_path = selected_pkg_info.path / "CMakeLists.txt"
                    cmake_updated = False
                    if selected_pkg_info.build_type == "ament_cmake":
                        if not cmakelists_path.exists():
                            # Try to build a minimal PackageConfig for this package
                            pkg_config = PackageConfig(
                                name=selected_pkg_info.name,
                                build_type=selected_pkg_info.build_type,
                                dependencies=[Dependency(dep) for dep in iface_def.interface_package_dependencies],
                                interface_definitions=[iface_def],
                                library_targets=[],
                                executable_targets=[],
                                launch_configurations=[],
                                config_files_paths=[]
                            )
                            cmake_content = generate_cmake_lists_content(pkg_config)
                            with open(cmakelists_path, "w", encoding="utf-8") as f:
                                f.write(cmake_content)
                            logger.info(f"Generated new CMakeLists.txt for {selected_pkg_info.name}.")
                            self.output_display.append_text(f"[INFO] Generated new CMakeLists.txt for {selected_pkg_info.name}.")
                            cmake_generated = True
                        if cmakelists_path.exists():
                            cmake_status = update_cmakelists_for_new_interface(cmakelists_path, iface_def, selected_pkg_info.name)
                            cmake_updated = cmake_status == CMakeUpdateStatus.UPDATED
                            # Removed redundant/ambiguous message after refactor. Only show clear status above.
                        # Only show manual message if neither generated nor updated
                        if not (cmake_generated or cmake_updated):
                            msg = (f"Interface file '{iface_def.file_name}' created and package.xml updated.\n\n"
                                   f"Since '{selected_pkg_info.name}' is an ament_cmake package, "
                                   f"please manually update its CMakeLists.txt to include:\n"
                                   f"  - '{iface_def.relative_path}' in the rosidl_generate_interfaces() call.\n"
                                   f"  - Any new dependencies (e.g., {', '.join(iface_def.interface_package_dependencies) or 'none'}) in find_package().")
                            QMessageBox.information(self, "Manual CMake Update Required", msg)
                            # Removed duplicate/obsolete manual review message after refactor.
                        else:
                            msg = (f"Interface file '{iface_def.file_name}' created, package.xml updated, and CMakeLists.txt automatically generated/updated for '{selected_pkg_info.name}'.")
                            QMessageBox.information(self, "CMakeLists.txt Updated", msg)
                            self.output_display.append_text(f"[INFO] CMakeLists.txt for {selected_pkg_info.name} was automatically generated/updated.")

                    self.on_refresh_workspace_explorer() # Refresh to show new files if possible
                    self.update_active_workspace_display(f"Interface '{iface_def.file_name}' Added to {selected_pkg_info.name}")
                except Exception as e:
                    error_msg = f"Error processing new interface for {selected_pkg_info.name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    self.output_display.append_text(f"[ERROR] {error_msg}")
                    QMessageBox.critical(self, "Interface Creation Error", error_msg)
        else:
            logger.debug("New interface creation cancelled by user.")
            self.output_display.append_text("[INFO] New interface creation cancelled.")
    def on_edit_pkg_config(self):
        """Placeholder for editing package.xml or CMakeLists.txt."""
        logger.info("Edit Package Config action triggered.")
        self.output_display.append_text("[INFO] Action: Edit Package Config... (Not yet implemented)")
        QMessageBox.information(self, "Edit Package Config", "Functionality to edit package configurations is not yet implemented.")
        # Example: dialog = PackageConfigEditorDialog(parent=self) ...

    def _get_selected_package_info_from_explorer(self) -> Optional[PackageInfo]:
        """
        Retrieves the PackageInfo object for the currently selected item in the WorkspaceExplorer,
        if the selected item is a package.
        """
        current_index = self.workspace_explorer.view.currentIndex()
        if not current_index.isValid():
            return None
        
        item = self.workspace_explorer.model.itemFromIndex(current_index)
        if item:
            pkg_info = item.data(Qt.ItemDataRole.UserRole + 1) # UserRole + 1 is for PackageInfo
            if isinstance(pkg_info, PackageInfo):
                return pkg_info
        return None
    # --- Sidebar Action Slots ---
    def on_sidebar_explorer(self):
        logger.info("Sidebar: Explorer action triggered.")
        # This action might toggle visibility or focus of the workspace explorer
        # For now, just a message.
        self.output_display.append_text("[INFO] Sidebar: Explorer (currently focuses main window)")
        # Ensure explorer button is visually "active" and others are not (if explorer is not a tab)
        for action_unique_id, action_object in self.sidebar_view_action_map.items():
            button = self.sidebar_tool_bar.widgetForAction(action_object)
            if button: self._set_sidebar_button_active_state(button, False)
        
        explorer_button = self.sidebar_tool_bar.widgetForAction(self.sidebar_explorer_action)
        if explorer_button: self._set_sidebar_button_active_state(explorer_button, True)
        self.workspace_explorer.setFocus()

    def _add_or_focus_tab(self, view_widget: QWidget, tab_title: str, tab_icon: Optional[QIcon] = None, unique_id: Optional[str] = None):
        """
        Adds a new tab with the given widget or focuses an existing tab
        if a tab with the same unique_id (or title if unique_id is None) already exists.
        """
        if not unique_id:
            unique_id = tab_title # Use title as unique identifier if no specific ID is given

        # Check if a tab with this unique_id already exists
        for i in range(self.active_view_tabs.count()):
            widget_in_tab = self.active_view_tabs.widget(i)
            # Store unique_id on the widget itself for easy retrieval
            if hasattr(widget_in_tab, 'rosbuddy_tab_id') and widget_in_tab.rosbuddy_tab_id == unique_id:
                self.active_view_tabs.setCurrentIndex(i)
                logger.debug(f"Focused existing tab: '{tab_title}' (ID: {unique_id})")
                return widget_in_tab # Return the existing widget

        # If not found, create a new tab
        # Store the unique_id on the widget
        setattr(view_widget, 'rosbuddy_tab_id', unique_id)

        if tab_icon:
            index = self.active_view_tabs.addTab(view_widget, tab_icon, tab_title)
        else:
            index = self.active_view_tabs.addTab(view_widget, tab_title)
        
        self.active_view_tabs.setCurrentIndex(index)
        logger.info(f"Opened new tab: '{tab_title}' (ID: {unique_id}) at index {index}")
        self._update_empty_tab_placeholder_visibility() # Hide placeholder if this is the first tab
        return view_widget # Return the new widget

    def on_sidebar_settings(self):
        logger.info("Sidebar: Settings action triggered.")
       
        settings_view = SettingsView(parent=self.active_view_tabs) # Parent to tab widget for lifecycle
        self._add_or_focus_tab(
            view_widget=settings_view,
            tab_title="Settings",
            tab_icon=self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), # Reuse icon
            unique_id="rosbuddy_settings_view"
        )

    def on_sidebar_ai_assistant(self):
        logger.info("Sidebar: AI Assistant action triggered.")
        ai_view = AIAssistantView(parent=self.active_view_tabs)
        self._add_or_focus_tab(
            view_widget=ai_view,
            tab_title="AI Assistant",
            # tab_icon=QIcon.fromTheme("preferences-desktop-ai-assistant"), # If you have a theme icon
            unique_id="rosbuddy_ai_assistant_view"
        )

    def on_sidebar_node_wizard(self):
        logger.info("Sidebar: Node Wizard action triggered.")
        view = NodeWizardView(parent=self.active_view_tabs)
        view.set_package_discovery(self.package_discovery)
        self._add_or_focus_tab(view, "Node Wizard", unique_id="rosbuddy_node_wizard_view")

    def on_sidebar_launch_runner(self):
        logger.info("Sidebar: Launch Runner action triggered.")
        view = LaunchRunnerView(parent=self.active_view_tabs)
        self._add_or_focus_tab(view, "Launch Runner", unique_id="rosbuddy_launch_runner_view")

    def on_sidebar_ros_graph(self):
        logger.info("Sidebar: ROS Graph action triggered.")
        view = RosGraphInspectorView(parent=self.active_view_tabs)
        self._add_or_focus_tab(view, "ROS Graph", unique_id="rosbuddy_ros_graph_view")

    def on_sidebar_debug_view(self):
        logger.info("Sidebar: Debug View action triggered.")
        view = DebugView(parent=self.active_view_tabs)
        self._add_or_focus_tab(view, "Debug", unique_id="rosbuddy_debug_view")

    def on_sidebar_ai_agent_actions(self):
        logger.info("Sidebar: AI Agent action triggered.")
        view = AIAgentActionView(parent=self.active_view_tabs)
        self._add_or_focus_tab(view, "AI Agent Actions", unique_id="rosbuddy_ai_agent_actions_view")

    def on_sidebar_ros_doctor(self):
        logger.info("Sidebar: ROS Doctor action triggered.")
        view = RosDoctorView(parent=self.active_view_tabs)
        self._add_or_focus_tab(view, "ROS Doctor", unique_id="rosbuddy_ros_doctor_view")

    def _open_initial_view(self):
        """Opens the WelcomeView as the initial tab."""
        # Check if any tabs are already open (e.g., from a restored session - future)
        if self.active_view_tabs.count() == 0:
            welcome_view = WelcomeView(parent=self.active_view_tabs)
            # Connect signal from WelcomeView for action card clicks
            welcome_view.action_card_clicked.connect(self.handle_welcome_action)
            self._add_or_focus_tab(
                view_widget=welcome_view,
                tab_title="Welcome",
                # tab_icon=QIcon.fromTheme("help-about"), # Example icon
                unique_id="rosbuddy_welcome_view" # Give it a unique ID
            )
    def handle_welcome_action(self, action_id: str):
        """Handles actions triggered from WelcomeView cards."""
        logger.info(f"WelcomeView action card clicked: {action_id}")
        if action_id == "open_workspace": self.on_open_workspace()
        elif action_id == "new_workspace": self.on_new_workspace()
        elif action_id == "create_package": self.on_create_package()
        elif action_id == "ai_assistant": self.on_sidebar_ai_assistant()
        elif action_id == "settings": self.on_sidebar_settings()
        elif action_id == "launch_runner": self.on_sidebar_launch_runner()
        # Add more cases for other actions from WelcomeView


    def _on_explorer_item_double_clicked(self, index: QModelIndex):
        item = self.workspace_explorer.model.itemFromIndex(index)
        if not item:
            return

        file_path_str = item.data(Qt.ItemDataRole.UserRole + 2) # Check for stored file path
        if file_path_str:
            file_path = pathlib.Path(file_path_str)
            if file_path.is_file():
                logger.info(f"Workspace explorer item double-clicked, opening file: {file_path}")
                self._open_file_in_editor(file_path)
            else:
                logger.warning(f"Workspace explorer item double-clicked, but path is not a file: {file_path}")

    def _open_file_in_editor(self, file_path: pathlib.Path):
        editor_view = CodeEditorView(file_path=file_path, parent=self.active_view_tabs)
        
        # Connect the dirty state signal from this specific editor instance
        editor_view.dirty_state_changed.connect(self._on_editor_dirty_state_changed)
        
        self._add_or_focus_tab(
            view_widget=editor_view,
            tab_title=file_path.name, # Initial title
            # Consider adding a file icon based on type later
            unique_id=str(file_path) # Use full path as unique ID for the tab
        )

    def _on_editor_dirty_state_changed(self, is_dirty: bool, file_path_str: str):
        """Updates the tab title when an editor's dirty state changes."""
        # file_path_str here is the unique_id of the tab
        for i in range(self.active_view_tabs.count()):
            widget_in_tab = self.active_view_tabs.widget(i)
            if hasattr(widget_in_tab, 'rosbuddy_tab_id') and widget_in_tab.rosbuddy_tab_id == file_path_str:
                base_title = pathlib.Path(file_path_str).name
                new_tab_title = f"*{base_title}" if is_dirty else base_title
                self.active_view_tabs.setTabText(i, new_tab_title)
                
                # If the active tab is this one, also update the editor's internal file_path_label
                if isinstance(widget_in_tab, CodeEditorView) and self.active_view_tabs.currentIndex() == i:
                     # The editor's _set_dirty already updates its internal label,
                     # but this ensures tab title is primary.
                     pass # Editor handles its own internal label update via its _set_dirty
                break

    def on_active_tab_changed(self, index: int):
        """
        Called when the current tab in active_view_tabs changes.
        Updates the active state of sidebar buttons.
        """
        logger.debug(f"Active tab changed to index: {index}")
        current_active_tab_id = self.active_tab_unique_id # Use the property
        logger.debug(f"Current active tab ID from property: {current_active_tab_id}")

        # Deactivate all mapped sidebar actions first
        for action_unique_id, action_object in self.sidebar_view_action_map.items():
            button = self.sidebar_tool_bar.widgetForAction(action_object)
            if button:
                is_active = (action_unique_id == current_active_tab_id)
                self._set_sidebar_button_active_state(button, is_active)
        
        # Special handling for explorer if needed, but it's not a tab.
        # Explorer button should be active if no other *sidebar-mapped* tab is active,
        # or if explicitly clicked.
        explorer_button = self.sidebar_tool_bar.widgetForAction(self.sidebar_explorer_action)
        if explorer_button:
            # If no sidebar-mapped tab is active, consider explorer active by default,
            # unless the WelcomeView is active (if WelcomeView is not sidebar-mapped).
            # This logic can be complex. For now, explorer is active only on click.
            # If current_active_tab_id is None (e.g. Welcome tab or Code Editor),
            # and explorer was the last clicked sidebar item, it should remain active.
            # This needs a "last_sidebar_action_clicked" state if we want that behavior.
            # For now, only the active tab's corresponding button is highlighted.
            # Explorer button is handled by its on_sidebar_explorer.
            pass

        self._update_empty_tab_placeholder_visibility()

    def _set_sidebar_button_active_state(self, button: QToolButton, active: bool):
        """Helper to set active property and re-polish a sidebar button."""
        if button.property("active") == active: # Avoid unnecessary re-polish
            return
        button.setProperty("active", active)
        logger.debug(f"Setting sidebar button '{button.toolTip()}' active: {active}")
        self.style().unpolish(button)
        self.style().polish(button)

    # --- Action Slots ---
    def on_new_workspace(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is in progress."); return
        logger.info("New Workspace action triggered.")
        self.output_display.append_text("[INFO] Action: New Workspace...")
        parent_dir = QFileDialog.getExistingDirectory(self, "Select Parent Directory", os.path.expanduser("~"))
        if not parent_dir:
            logger.debug("New workspace cancelled by user (no parent directory selected).")
            self.output_display.append_text("[INFO] New workspace cancelled."); return
        ws_name, ok = QInputDialog.getText(self, "New Workspace Name", "Enter name for the new workspace:", text="ros2_ws")
        if not ok or not ws_name.strip():
            logger.debug("New workspace cancelled by user (no name entered or cancel pressed).")
            self.output_display.append_text("[INFO] New workspace cancelled."); return
        ws_name = ws_name.strip()
        self.output_display.append_text(f"[INFO] Attempting to create workspace '{ws_name}' in '{parent_dir}'...")
        # This is a quick operation, doesn't need a worker
        success, message, new_ws_path = self.workspace_manager.create_new_workspace(parent_dir, ws_name)
        self.output_display.append_text(f"[INFO] {message}")
        if success:
            logger.info(f"Workspace '{new_ws_path}' created and set as active.")
            self.update_active_workspace_display(f"Workspace '{ws_name}' Created")
        else:
            logger.error(f"Failed to create workspace '{ws_name}': {message}")
            QMessageBox.critical(self, "Workspace Creation Error", message)
            self.update_active_workspace_display("Workspace Creation Failed")

    def on_open_workspace(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is in progress."); return
        logger.info("Open Workspace action triggered.")
        self.output_display.append_text("[INFO] Action: Open Workspace...")
        ws_dir = QFileDialog.getExistingDirectory(self, "Select ROS 2 Workspace", os.path.expanduser("~"))
        if not ws_dir:
            logger.debug("Open workspace cancelled by user.")
            self.output_display.append_text("[INFO] Open workspace cancelled."); return
        self.output_display.append_text(f"[INFO] Attempting to open workspace '{ws_dir}'...")
        # Quick operation
        success, message = self.workspace_manager.set_active_workspace(ws_dir)
        self.output_display.append_text(f"[INFO] {message}")
        if success:
            logger.info(f"Workspace '{ws_dir}' opened and set as active.")
            self.update_active_workspace_display(f"Workspace '{pathlib.Path(ws_dir).name}' Opened")
        else:
            logger.error(f"Failed to open workspace '{ws_dir}': {message}")
            QMessageBox.warning(self, "Open Workspace Error", message)
            self.update_active_workspace_display("Open Workspace Failed")

    def on_create_package(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is in progress."); return
        active_ws_src_path = self.workspace_manager.get_active_workspace_src_path()
        if not active_ws_src_path:
            QMessageBox.warning(self, "Error", "No active workspace. Please open or create one first.")
            logger.warning("Create package attempted with no active workspace.")
            return

        logger.info("Create Package action triggered.")
        dialog = CreatePackageDialog(default_maintainer_name=self.last_maint_name,
                                     default_maintainer_email=self.last_maint_email, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_package_data()
            if data:
                self.last_maint_name = data['maintainer_name'] # Save for next time
                self.last_maint_email = data['maintainer_email']
                logger.info(f"Package creation data received: {data}")
                self.output_display.append_text(f"[INFO] Creating package '{data['name']}' with build type '{data['build_type']}'...")
                try:
                    cfg = PackageConfig(name=data['name'], version=data['version'], description=data['description'],
                                        maintainer_email=data['maintainer_email'], maintainer_name=data['maintainer_name'],
                                        license_name=data['license_name'], build_type=data['build_type'])
                    # Auto-add hello world C++ node for ament_cmake if requested and no executable target present
                    if data['build_type'] == 'ament_cmake' and data['include_hello_world'] and not cfg.executable_targets:
                        from rosbuddy.data_models.package_config import ExecutableTarget
                        hello_exec = ExecutableTarget(
                            name="hello_world_cpp_node",
                            sources=["src/hello_world_cpp_node.cpp"],
                            linked_libraries=["rclcpp"]
                        )
                        cfg.add_executable_target(hello_exec)

                    # For more complex scenarios, like workspaces with existing packages, or specific user requirements,
                    # additional logic would be needed here.

                    # --- Logging and Feedback ---
                    logger.info(f"PackageConfig created: {cfg}")
                    self.output_display.append_text(f"[INFO] Package '{data['name']}' created successfully.")
                    QMessageBox.information(self, "Package Created", f"Package '{data['name']}' created successfully.")
                    self.on_refresh_workspace_explorer() # Refresh to show new package
                    self.update_active_workspace_display(f"Package '{data['name']}' Created")
                except Exception as e:
                    logger.error(f"Error creating package: {e}", exc_info=True)
                    QMessageBox.critical(self, "Package Creation Error", f"Failed to create package: {e}")

    def _start_worker_task(self, task_description: str, target_fn, *args, **kwargs) -> bool:
        """Start a worker task with the given description and target function.
        
        Returns True if worker was started successfully, False otherwise.
        """
        if self.current_worker and self.current_worker.isRunning():
            logger.warning(f"_start_worker_task: Cannot start '{task_description}' - another worker is already running.")
            return False
        
        try:
            logger.info(f"Starting worker task: {task_description}")
            self.current_worker = Worker(target_fn, *args, **kwargs)
            
            # Connect base worker signals
            self.current_worker.signals.finished.connect(self._on_worker_finished)
            self.current_worker.signals.error.connect(self._on_worker_error)
            self.current_worker.signals.progress.connect(self.output_display.append_text)
            
            # Update UI state
            self.current_action_description = task_description
            self.update_active_workspace_display(task_description)
            
            # Start the worker
            self.current_worker.start()
            logger.debug(f"Worker task '{task_description}' started successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start worker task '{task_description}': {e}", exc_info=True)
            self.current_worker = None
            self.current_action_description = ""
            return False

    def on_build_workspace(self):
        """Build the active workspace using colcon build."""
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path:
            QMessageBox.warning(self, "Build Error", "No active workspace.")
            return
        
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is in progress.")
            return
        
        logger.info("Build Workspace action triggered.")
        self.output_display.append_text("[INFO] Action: Build Workspace...")
        
        task_desc = "Build Workspace"
        if self._start_worker_task(task_desc, self.tool_invoker.colcon_build):
            # Connect specific result handler for build tasks
            self.current_worker.signals.result.connect(self._on_build_clean_result)

    def on_clean_workspace(self):
        """Clean the active workspace (remove build, install, log directories)."""
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path:
            QMessageBox.warning(self, "Clean Error", "No active workspace.")
            return
        
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is in progress.")
            return
        
        logger.info("Clean Workspace action triggered.")
        self.output_display.append_text("[INFO] Action: Clean Workspace...")
        
        task_desc = "Clean Workspace"
        if self._start_worker_task(task_desc, self.tool_invoker.colcon_clean):
            # Connect specific result handler for build tasks
            self.current_worker.signals.result.connect(self._on_build_clean_result)

    def on_run_executable(self):
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path:
            QMessageBox.warning(self, "Run Error", "No active workspace."); return
        if self.current_worker and self.current_worker.isRunning(): # Redundant if _start_worker_task is used, but safe
             QMessageBox.warning(self, "Busy", "Another task is in progress."); return

        dialog = SelectRosItemDialog(package_discovery=self.package_discovery, mode="run", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selection = dialog.get_selection()
            if selection:
                pkg_name, exec_name = selection
                task_desc = f"Run Executable: {pkg_name}/{exec_name}"
                if self._start_worker_task(task_desc, self.tool_invoker.ros2_run,
                                           pkg_name, exec_name, args=[], cwd=str(active_ws_path)):
                    self.current_worker.signals.process_started.connect(self._on_ros_process_started)
                    self.current_worker.signals.result.connect(self._on_run_launch_result)
            else:
                self.output_display.append_text("[INFO] Run executable cancelled: No valid selection.")
                logger.debug("Run executable selection invalid.")
        else:
            self.output_display.append_text("[INFO] Run executable cancelled by user.")
            logger.debug("Run executable dialog cancelled.")

    def on_launch_file(self):
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path:
            QMessageBox.warning(self, "Launch Error", "No active workspace."); return
        if self.current_worker and self.current_worker.isRunning():
             QMessageBox.warning(self, "Busy", "Another task is in progress."); return

        dialog = SelectRosItemDialog(package_discovery=self.package_discovery, mode="launch", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selection = dialog.get_selection()
            if selection:
                pkg_name, launch_name = selection
                task_desc = f"Launch File: {pkg_name}/{launch_name}"
                if self._start_worker_task(task_desc, self.tool_invoker.ros2_launch,
                                           pkg_name, launch_name, args=[], cwd=str(active_ws_path)):
                    self.current_worker.signals.process_started.connect(self._on_ros_process_started)
                    self.current_worker.signals.result.connect(self._on_run_launch_result)
            else:
                self.output_display.append_text("[INFO] Launch file cancelled: No valid selection.")
                logger.debug("Launch file selection invalid.")
        else:
            self.output_display.append_text("[INFO] Launch file cancelled by user.")
            logger.debug("Launch file dialog cancelled.")

    def _on_build_clean_result(self, result_tuple: tuple):
        """Handle results from build/clean operations."""
        # result_tuple for build/clean: (success, stdout_str, stderr_str)
        success, stdout_str, stderr_str = result_tuple
        task_name = self.current_action_description # Should be "Build Workspace" or "Clean Workspace"
        logger.debug(f"Build/Clean task ('{task_name}') worker result: Success={success}")

        # Display stdout output if available
        if stdout_str.strip():
            self.output_display.append_text(f"\n[TASK OUTPUT - {task_name}]:\n{stdout_str.strip()}")
        
        # Display stderr output if available
        if stderr_str.strip():
            self.output_display.append_text(f"\n[TASK STDERR - {task_name}]:\n{stderr_str.strip()}")

        if success:
            self.output_display.append_text(f"[SUCCESS] {task_name} completed successfully.")
            QMessageBox.information(self, f"{task_name} Complete", f"{task_name} completed successfully.")
            # Refresh workspace explorer to show updated state
            if hasattr(self, 'on_refresh_workspace_explorer'):
                self.on_refresh_workspace_explorer()
        else:
            self.output_display.append_text(f"[ERROR] {task_name} failed. Check output above for details.")
            QMessageBox.warning(self, f"{task_name} Failed", f"{task_name} failed. Check output for details.")

    def _on_run_launch_result(self, result_tuple: tuple):
        # result_tuple for run/launch: (success, stdout_str, stderr_str, finished_process_obj)
        success, stdout_str, stderr_str, finished_process_obj = result_tuple
        task_name = self.current_action_description # Should be "Run Executable..." or "Launch File..."
        exit_code = finished_process_obj.returncode if finished_process_obj else "N/A (process object missing)"
        logger.debug(f"Run/Launch task ('{task_name}') worker result: Success={success}, Process Exit Code={exit_code}")

        if not success:
            # SIGTERM (-15) or SIGKILL (-9) are results of user stopping, not errors
            self.output_display.append_text(f"\n[TASK STDERR - {task_name}]:\n{stderr_str.strip()}")
            QMessageBox.warning(self, f"{task_name} Result", f"{task_name} failed or ended unexpectedly. Exit code: {exit_code}. Check output.")
        elif exit_code in [-15, -9]:
            self.output_display.append_text(f"[INFO] {task_name} was stopped by user action.")
        elif exit_code == 130: # Ctrl+C in the terminal where ROSBuddy was launched, if it affects the child
            self.output_display.append_text(f"[INFO] {task_name} may have been interrupted (Ctrl+C).")
        # else: process exited with non-zero but it wasn't a clear error code we identify.
        # If success is True, _on_worker_finished will post the "Finished" status.

    def on_stop_task(self):
        # This is the refined version from previous discussions
        if not self.running_ros_process:
            logger.debug("on_stop_task: No running_ros_process to stop.")
            self.output_display.append_text("[INFO] Stop Task: No ROS process is currently tracked.")
            self.update_active_workspace_display("Stop Task Attempt (No Process)") # Update UI
            return

        pid = self.running_ros_process.pid
        logger.debug(f"on_stop_task: Attempting to stop PID {pid}. Current poll: {self.running_ros_process.poll()}")
        self.output_display.append_text(f"\n--- Attempting to stop ROS process (PID: {pid}) ---")
        self.status_bar.showMessage(f"Stopping PID: {pid}...", 0)

        try:
            self.running_ros_process.terminate() # Send SIGTERM
            self.output_display.append_text(f"[INFO] Sent SIGTERM to process {pid}.")

            # Non-blocking check would involve QTimer. For simplicity and immediate feedback for this version:
            # Brief pause to allow SIGTERM to be processed. This is blocking.
            time.sleep(0.3) # Increased slightly from 0.2

            if self.running_ros_process and self.running_ros_process.poll() is None: # Check if still running
                logger.info(f"on_stop_task: Process {pid} still running after SIGTERM, sending SIGKILL.")
                self.output_display.append_text(f"[INFO] Process {pid} still running after SIGTERM, sending SIGKILL...")
                self.running_ros_process.kill() # Send SIGKILL
                self.output_display.append_text(f"[INFO] Sent SIGKILL to process {pid}.")
            
            # Final check and clear
            if self.running_ros_process:
                final_poll_status = self.running_ros_process.poll()
                logger.debug(f"on_stop_task: After stop attempt, PID {pid} poll is: {final_poll_status}")
                if final_poll_status is not None:
                    logger.info(f"ROS process (PID: {pid}) confirmed terminated by stop action (exit code: {final_poll_status}). Clearing reference.")
                    self.running_ros_process = None # IMPORTANT: Clear the reference
                else:
                    logger.warning(f"ROS process (PID: {pid}) still polls as None after SIGKILL attempt. This is unexpected.")
            else: # Should not happen if guard above is effective
                logger.info(f"on_stop_task: self.running_ros_process was None by the time final poll for PID {pid} was checked (possibly due to rapid events).")

        except ProcessLookupError:
            logger.warning(f"on_stop_task: Process PID {pid} not found during stop sequence. Already terminated?")
            self.output_display.append_text(f"[INFO] Process {pid} already terminated or not found.")
            if self.running_ros_process and self.running_ros_process.pid == pid: # Defensive check
                 self.running_ros_process = None
        except Exception as e:
            error_msg = f"Error stopping process {pid}: {e}"
            logger.error(error_msg, exc_info=True)
            self.output_display.append_text(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "Stop Process Error", error_msg)
            # Attempt to clear reference if process is known to be dead despite error
            if self.running_ros_process and self.running_ros_process.poll() is not None:
                self.running_ros_process = None
        finally:
            # UI state update is crucial here, regardless of how try block went
            self.update_active_workspace_display("Stop Task Action Completed")

    def _on_ros_process_started(self, process_obj: subprocess.Popen):
        if not isinstance(process_obj, subprocess.Popen):
            logger.error(f"_on_ros_process_started did NOT receive a Popen object! Got: {type(process_obj)}")
            self.running_ros_process = None # Ensure it's cleared
        else:
            self.running_ros_process = process_obj
            logger.debug(f"_on_ros_process_started received Popen. PID: {self.running_ros_process.pid}. Poll() immediately: {self.running_ros_process.poll()}")
        
        pid_str = str(self.running_ros_process.pid) if self.running_ros_process else "Unknown"
        self.output_display.append_text(f"[INFO] ROS process event (PID: {pid_str}) - Task '{self.current_action_description}' process started.")
        self.update_active_workspace_display(self.current_action_description) # Refresh UI, current_action_description should be "Task X in progress"

    def _on_worker_finished(self):
        logger.debug(f"_on_worker_finished: ENTERED. self.current_action_description is '{self.current_action_description}'")
        task_desc = self.current_action_description if self.current_action_description else "Background task"
        logger.debug(f"_on_worker_finished: self.current_action_description at this point is '{self.current_action_description}', task_desc resolved to '{task_desc}'")
        logger.info(f"--- Task '{task_desc}' Worker has finished ---")

        if self.running_ros_process:
            poll_status = self.running_ros_process.poll()
            logger.debug(f"_on_worker_finished: For task '{task_desc}', found self.running_ros_process (PID: {self.running_ros_process.pid}). Poll status: {poll_status}")
            if poll_status is not None:
                logger.info(f"ROS process (PID: {self.running_ros_process.pid}) associated with finished worker ('{task_desc}') has terminated (exit: {poll_status}). Clearing reference.")
                self.running_ros_process = None
            else:
                logger.warning(f"_on_worker_finished: For task '{task_desc}', ROS process (PID: {self.running_ros_process.pid}) poll() is None, but its 'supervisor' worker finished. This may indicate a detached process or a very short-lived superviser task. Keeping ROS process reference for stop button if it's a long-running node.")
        else:
            logger.debug(f"_on_worker_finished: For task '{task_desc}', self.running_ros_process was already None.")

        self.current_worker = None
        self.update_active_workspace_display(f"Task '{task_desc}' Finished")

    def _on_worker_error(self, error_tuple):
        logger.debug(f"_on_worker_error: ENTERED. self.current_action_description is '{self.current_action_description}'")
        exctype, value, tb_str = error_tuple
        task_desc = self.current_action_description if self.current_action_description else "Unnamed task"
        
        logger.error(f"--- ERROR during task '{task_desc}' ---", exc_info=False) # tb_str has full traceback
        logger.error(f"Type: {exctype.__name__ if hasattr(exctype, '__name__') else str(exctype)}")
        logger.error(f"Message: {str(value)}")
        logger.error(f"Traceback (from worker signal):\n{tb_str}")

        self.output_display.append_text(f"--- ERROR during task '{task_desc}' ---")
        self.output_display.append_text(f"Type: {exctype.__name__ if hasattr(exctype, '__name__') else str(exctype)}")
        self.output_display.append_text(f"Message: {str(value)}")
        # self.output_display.append_text(f"Traceback:\n{tb_str}") # Generally too verbose for GUI display

        QMessageBox.critical(self, f"Task Error: {task_desc}", f"An error occurred: {value}\n\nSee application logs (Output Panel) for details.")

        if self.running_ros_process: # Check if the error might have killed the ROS process
            poll_status = self.running_ros_process.poll()
            if poll_status is not None:
                logger.info(f"ROS process (PID: {self.running_ros_process.pid}) exited (poll: {poll_status}) concurrently with worker error for task '{task_desc}'. Clearing reference.")
                self.running_ros_process = None
        
        self.current_worker = None
        self.update_active_workspace_display(f"Task '{task_desc}' Failed")

    def on_omni_search_triggered(self):
        logger.info("Omni-Search triggered (mock).")
        QMessageBox.information(self, "Omni-Search", "Omni-Search (Ctrl+K) is coming soon!")


    def on_about(self):
        QMessageBox.about(self, "About ROSBuddy", "ROSBuddy v0.1.2\n\nSimplifying ROS 2 Development")
        logger.debug("About dialog shown.")

    def on_clear_output(self):
        if hasattr(self, 'output_display') and self.output_display:
            self.output_display.clear()
            logger.info("Output console cleared by user.") # This will appear in the now-cleared console
        else: # Should not happen if _create_central_widget runs
            logger.warning("on_clear_output called but output_display is not available.")

    def get_ui_state(self):
        """Return a dict with window geometry and splitter state for persistence."""
        state = {
            'window_geometry': self.saveGeometry().toHex().data().decode('utf-8'),
        }
        if hasattr(self, 'main_splitter'): # Updated to main_splitter
            state['splitter_state'] = self.main_splitter.saveState().toHex().data().decode('utf-8')
        
        # Save last active workspace
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if active_ws_path:
            state['last_workspace'] = str(active_ws_path)

        return state

    def on_close_tab(self, index: int):
        """Handles the tabCloseRequested signal from the QTabWidget."""
        widget = self.active_view_tabs.widget(index)
        tab_name = self.active_view_tabs.tabText(index)
        logger.info(f"Close tab requested for: '{tab_name}' at index {index}")

        can_close = True
        if isinstance(widget, CodeEditorView):
            can_close = widget.close_view() # This will prompt user if dirty

        if not can_close:
            logger.debug(f"Tab close cancelled for '{tab_name}' due to unsaved changes or user action.")
            return # Do not close the tab

        self.active_view_tabs.removeTab(index)
        if widget: # Clean up the widget if necessary
            # If the widget had a rosbuddy_tab_id, ensure its corresponding sidebar button is deactivated
            # This is implicitly handled by currentChanged signal firing after removal,
            # which calls on_active_tab_changed.
            widget.deleteLater()
        self._update_empty_tab_placeholder_visibility() # Show placeholder if last tab closed
    def closeEvent(self, event):
        """Override closeEvent to allow UI state saving from outside."""
        # Save UI state for persistence
        if hasattr(self, 'get_ui_state'):
            ui_state = self.get_ui_state()
            # Store on the QApplication for retrieval after app.exec()
            QApplication.instance()._rosbuddy_ui_state = ui_state
        super().closeEvent(event)