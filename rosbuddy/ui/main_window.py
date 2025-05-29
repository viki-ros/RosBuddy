# rosbuddy/ui/main_window.py
import sys
import os
import pathlib
import traceback
import subprocess
import time # Keep for now if on_stop_task uses it for a brief pause
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QSplitter, QWidget, QLabel, QStatusBar, QMenuBar, QTextEdit,
    QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QApplication, QToolButton, QToolBar,
    QStyle, # For standard icons
    QTreeView # For Workspace Explorer
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
# Typing imports
from typing import Optional, List, Dict, Any, Callable # Ensure all common types are here
from PyQt6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem
 
# Configure module-level logger
logger = logging.getLogger(__name__)

# Project specific imports
from rosbuddy.core_logic import WorkspaceManager, ToolInvoker, create_package_scaffolding, PackageDiscovery
# from rosbuddy.core_logic.package_discovery import PackageInfo # PackageInfo is used by SelectRosItemDialog
from rosbuddy.data_models import PackageConfig
from rosbuddy.ui.dialogs import CreatePackageDialog, SelectRosItemDialog
from rosbuddy.ui.components import WorkspaceExplorer, OutputPanel, ContextualViewPlaceholder
from rosbuddy.ui.components.worker import Worker, WorkerSignals
from rosbuddy.ui.dialogs.node_creator_dialog import NodeCreatorDialog
from rosbuddy.ui.dialogs.launch_file_composer_dialog import LaunchFileComposerDialog
from rosbuddy.ui.dialogs.msg_srv_action_editor_dialog import MsgSrvActionEditorDialog
from rosbuddy.ui.dialogs.package_config_editor_dialog import PackageConfigEditorDialog

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

# --- Worker Thread Definition ---
class Worker(QThread):
    def __init__(self, target_fn: Callable, *args, **kwargs):
        super().__init__()
        self.target_fn = target_fn
        self.args = args
        self.target_fn_kwargs = kwargs.copy()
        self.signals = WorkerSignals()

        # Setup realtime_output_callback to emit progress
        # If Worker user passes 'realtime_output_callback', it's assumed to be the one to use.
        # Otherwise, default to self.signals.progress.emit.
        # The logic in your previous paste was good for this.
        original_realtime_callback = self.target_fn_kwargs.pop('realtime_output_callback', self.signals.progress.emit)
        self.target_fn_kwargs['realtime_output_callback'] = original_realtime_callback


        # Setup process_started_callback to emit process_started signal
        if 'process_started_callback' not in self.target_fn_kwargs: # Only add if not already specified
             self.target_fn_kwargs['process_started_callback'] = self.signals.process_started.emit


    def run(self):
        result_tuple = None
        try:
            logger.debug(f"Worker.run() calling target_fn with args: {self.args}, kwargs: {list(self.target_fn_kwargs.keys())}")
            result_tuple = self.target_fn(*self.args, **self.target_fn_kwargs)

            if not isinstance(result_tuple, tuple) or not (len(result_tuple) == 3 or len(result_tuple) == 4):
                logger.warning(f"target_fn did not return the expected tuple format. Got: {type(result_tuple)}. Content: {result_tuple}")
                self.signals.result.emit((False, str(result_tuple), "Unexpected return format from task", None))
            else:
                logger.debug(f"target_fn (e.g., ToolInvoker) finished. Result success: {result_tuple[0]}")
                self.signals.result.emit(result_tuple)
        except Exception as e:
            logger.error(f"Worker.run() caught ERROR during target_fn execution: {e}", exc_info=True)
            self.signals.error.emit((type(e), e, traceback.format_exc()))
        finally:
            logger.debug("Worker.run() completed. Emitting finished signal.")
            self.signals.finished.emit()

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self, workspace_manager: WorkspaceManager, tool_invoker: ToolInvoker, parent=None, window_geometry=None, splitter_state=None):
        super().__init__(parent)
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

        # --- Modular UI Components ---
        self.workspace_explorer = WorkspaceExplorer(self.package_discovery, self.workspace_manager)
        self.output_panel = OutputPanel()
        self.contextual_view_placeholder = ContextualViewPlaceholder()

        # Connect clear button
        self.output_panel.clear_output_button.clicked.connect(self.on_clear_output)
        self.output_display = self.output_panel.output_display

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()
        # Restore splitter state if provided
        if splitter_state and hasattr(self, 'vertical_splitter'):
            self.vertical_splitter.restoreState(splitter_state)

        # --- Setup GUI Logging ---
        self.log_signal_emitter = QtLogSignal()
        self.log_signal_emitter.log_message_written.connect(self.output_display.append_text)
        gui_log_handler = QtLogHandler(self.log_signal_emitter)
        gui_log_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(gui_log_handler)
        
        self.update_active_workspace_display()
        logger.info("MainWindow initialized and GUI logging handler set up.")

        # --- Apply Modern Dark Theme (LM Studio-like) ---
        dark_stylesheet = """
        QMainWindow {
            background-color: #23272e;
            color: #e6e6e6;
        }
        QWidget {
            background-color: #23272e;
            color: #e6e6e6;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 13px;
        }
        QTreeView, QTableView {
            background-color: #23272e;
            alternate-background-color: #262b33;
            border: 1px solid #353b45;
            selection-background-color: #3a3f4b;
            selection-color: #e6e6e6;
            show-decoration-selected: 1;
        }
        QHeaderView::section {
            background-color: #23272e;
            color: #b0b0b0;
            border: none;
            font-weight: bold;
        }
        QToolBar {
            background: #23272e;
            border-bottom: 1px solid #353b45;
            spacing: 8px;
        }
        QToolButton {
            background: #2c313a;
            color: #e6e6e6;
            border-radius: 6px;
            padding: 6px 12px;
            margin: 2px;
        }
        QToolButton:hover {
            background: #353b45;
        }
        QStatusBar {
            background: #23272e;
            color: #b0b0b0;
            border-top: 1px solid #353b45;
        }
        QMenuBar {
            background: #23272e;
            color: #e6e6e6;
        }
        QMenuBar::item:selected {
            background: #353b45;
        }
        QMenu {
            background: #23272e;
            color: #e6e6e6;
        }
        QMenu::item:selected {
            background: #353b45;
        }
        QLabel#contextualViewPlaceholder {
            color: #b0b0b0;
            font-size: 15px;
            font-weight: 600;
            padding: 16px;
        }
        QTextEdit, QPlainTextEdit {
            background: #181a20;
            color: #e6e6e6;
            border: 1px solid #353b45;
            font-family: 'Fira Mono', 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            border-radius: 6px;
            padding: 8px;
        }
        QSplitter::handle {
            background: #353b45;
        }
        QMessageBox {
            background-color: #23272e;
            color: #e6e6e6;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def _create_actions(self):
        style = self.style()

        icon_new_ws = QIcon.fromTheme("document-new", style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        icon_open_ws = QIcon.fromTheme("document-open", style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        icon_exit = QIcon.fromTheme("application-exit", style.standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        icon_create_pkg = QIcon.fromTheme("package-x-generic", QIcon()) # Using a generic package icon
        icon_build = QIcon.fromTheme("system-run", style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)) # SP_DialogApplyButton or SP_MediaPlay
        icon_clean = QIcon.fromTheme("edit-clear", style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        icon_run_exec = QIcon.fromTheme("utilities-terminal", style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)) # Changed placeholder
        icon_launch = QIcon.fromTheme("application-x-executable", style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight)) # Changed placeholder
        icon_stop = QIcon.fromTheme("process-stop", style.standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        icon_refresh = QIcon.fromTheme("view-refresh", style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))

        self.new_workspace_action = QAction(icon_new_ws, "&New Workspace...", self)
        self.new_workspace_action.triggered.connect(self.on_new_workspace)
        self.open_workspace_action = QAction(icon_open_ws, "&Open Workspace...", self)
        self.open_workspace_action.triggered.connect(self.on_open_workspace)
        self.exit_action = QAction(icon_exit, "&Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.create_package_action = QAction(icon_create_pkg, "&Create New Package...", self)
        self.create_package_action.triggered.connect(self.on_create_package)
        self.build_workspace_action = QAction(icon_build, "&Build Workspace", self)
        self.build_workspace_action.triggered.connect(self.on_build_workspace)
        self.clean_workspace_action = QAction(icon_clean, "&Clean Workspace", self)
        self.clean_workspace_action.triggered.connect(self.on_clean_workspace)
        self.run_executable_action = QAction(icon_run_exec, "Run &Executable...", self)
        self.run_executable_action.triggered.connect(self.on_run_executable)
        self.launch_file_action = QAction(icon_launch, "&Launch File...", self)
        self.launch_file_action.triggered.connect(self.on_launch_file)
        self.stop_task_action = QAction(icon_stop, "&Stop Current Task", self)
        self.stop_task_action.triggered.connect(self.on_stop_task)
        
        self.refresh_workspace_action = QAction(icon_refresh, "&Refresh Workspace Explorer", self)
        self.refresh_workspace_action.setStatusTip("Reload the list of packages from the current workspace")
        self.refresh_workspace_action.triggered.connect(self.on_refresh_workspace_explorer)

        self.new_node_action = QAction("New Node...", self)
        self.new_node_action.triggered.connect(self.on_new_node)
        self.new_launch_action = QAction("New Launch File...", self)
        self.new_launch_action.triggered.connect(self.on_new_launch_file)
        self.new_msg_srv_action = QAction("New Msg/Srv/Action...", self)
        self.new_msg_srv_action.triggered.connect(self.on_new_msg_srv_action)
        self.edit_pkg_config_action = QAction("Edit package.xml/CMakeLists.txt...", self)
        self.edit_pkg_config_action.triggered.connect(self.on_edit_pkg_config)

        # Set initial enabled states directly or rely on first update_active_workspace_display
        # For clarity, we'll let update_active_workspace_display handle all dynamic enabling.
        # The actions that depend on workspace or busy state are initially disabled by default
        # if not explicitly setEnabled(True) here and no workspace is active.
        self.create_package_action.setEnabled(False)
        self.build_workspace_action.setEnabled(False)
        self.clean_workspace_action.setEnabled(False)
        self.run_executable_action.setEnabled(False)
        self.launch_file_action.setEnabled(False)
        self.stop_task_action.setEnabled(False)
        self.refresh_workspace_action.setEnabled(False)

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
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.active_ws_label = QLabel("Active Workspace: None")
        self.status_bar.addPermanentWidget(self.active_ws_label)
        # Initial message will be set by update_active_workspace_display

    def _create_central_widget(self):
        logger.debug(f"_create_central_widget: Method START.")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_hbox_layout = QHBoxLayout(self.central_widget)
        main_hbox_layout.setContentsMargins(0,0,0,0)
        self.vertical_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_hbox_layout.addWidget(self.vertical_splitter)

        # --- Left Pane: Workspace Explorer ---
        self.vertical_splitter.addWidget(self.workspace_explorer)

        # --- Right Pane Container ---
        right_pane_container_widget = QWidget()
        right_pane_vbox_layout = QVBoxLayout(right_pane_container_widget)
        right_pane_vbox_layout.setContentsMargins(0,0,0,0)
        self.horizontal_splitter_right = QSplitter(Qt.Orientation.Vertical)
        right_pane_vbox_layout.addWidget(self.horizontal_splitter_right)

        # --- Right-Top Pane: Contextual View Placeholder ---
        self.horizontal_splitter_right.addWidget(self.contextual_view_placeholder)

        # --- Right-Bottom Pane: Output Area ---
        self.horizontal_splitter_right.addWidget(self.output_panel)
        right_pane_vbox_layout.addWidget(self.horizontal_splitter_right)
        self.vertical_splitter.addWidget(right_pane_container_widget)
        self.vertical_splitter.setSizes([250, 950])
        self.horizontal_splitter_right.setSizes([500, 300])
        self.vertical_splitter.setOpaqueResize(False)
        self.horizontal_splitter_right.setOpaqueResize(False)
        logger.debug(f"_create_central_widget: Method END. Splitter children count: {self.vertical_splitter.count()}")
        main_hbox_layout.setSpacing(0)
        main_hbox_layout.setContentsMargins(0,0,0,0)
        right_pane_vbox_layout.setSpacing(0)
        right_pane_vbox_layout.setContentsMargins(0,0,0,0)

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
            self.workspace_explorer.update()
        QApplication.processEvents() # Ensure UI updates are processed

    def _update_workspace_explorer(self):
        """Populates/Updates the workspace explorer QTreeView with the active workspace and its packages."""
        logger.debug("_update_workspace_explorer: Method START.") # <-- ADD THIS LINE
        # Clear previous items but keep the model instance
        self.workspace_explorer.model().clear()
        # self.workspace_explorer_model.setHorizontalHeaderLabels(['Workspace Structure']) # Optional

        active_ws_path = self.workspace_manager.get_active_workspace_path()

        if not active_ws_path:
            root_item = QStandardItem("No Active Workspace")
            root_item.setEditable(False)
            self.workspace_explorer.model().appendRow(root_item)
            logger.debug("Workspace explorer updated: No active workspace.")
            self.workspace_explorer.header().setVisible(False)
            return

        # Create a root item for the workspace name
        ws_name = active_ws_path.name
        ws_root_item = QStandardItem(f"Workspace: {ws_name}")
        ws_root_item.setEditable(False)
        # icon_folder = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        # ws_root_item.setIcon(icon_folder)
        self.workspace_explorer.model().appendRow(ws_root_item)

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
                    # icon_pkg = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # Example
                    # package_item.setIcon(icon_pkg)
                    packages_parent_item.appendRow(package_item)
                logger.debug(f"Workspace explorer updated with {len(discovered_packages)} packages.")
                self.workspace_explorer.expand(packages_parent_item.index())

            else:
                no_packages_item = QStandardItem("No packages found in src/")
                no_packages_item.setEditable(False)
                ws_root_item.appendRow(no_packages_item)
                logger.info("Workspace explorer: Added 'No packages found in src/' under workspace node.")
            
            self.workspace_explorer.expand(ws_root_item.index()) # Expand the workspace root item
        except Exception as e:
            error_msg = f"Error during package discovery or populating tree: {e}"
            logger.error(error_msg, exc_info=True)
            if self.output_display: self.output_display.append_text(f"[ERROR] {error_msg}")
            error_item = QStandardItem("Error loading packages")
            error_item.setEditable(False)
            if ws_root_item: ws_root_item.appendRow(error_item) # Check if ws_root_item exists
            
        
        self.workspace_explorer.header().setVisible(False)

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
        """Placeholder for creating a new ROS message, service, or action definition."""
        logger.info("New Msg/Srv/Action action triggered.")
        self.output_display.append_text("[INFO] Action: New Msg/Srv/Action... (Not yet implemented)")
        QMessageBox.information(self, "New Msg/Srv/Action", "Functionality to create new Msg/Srv/Action definitions is not yet implemented.")
        # Example: dialog = MsgSrvActionEditorDialog(parent=self) ...

    def on_edit_pkg_config(self):
        """Placeholder for editing package.xml or CMakeLists.txt."""
        logger.info("Edit Package Config action triggered.")
        self.output_display.append_text("[INFO] Action: Edit Package Config... (Not yet implemented)")
        QMessageBox.information(self, "Edit Package Config", "Functionality to edit package configurations is not yet implemented.")
        # Example: dialog = PackageConfigEditorDialog(parent=self) ...



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
                # Quick operation for scaffolding
                try:
                    cfg = PackageConfig(name=data['name'], version=data['version'], description=data['description'],
                                        maintainer_email=data['maintainer_email'], maintainer_name=data['maintainer_name'],
                                        license_name=data['license_name'], build_type=data['build_type'])
                    # Future: Add more complex PackageConfig setup here if needed based on dialog
                    ok = create_package_scaffolding(str(active_ws_src_path), cfg, data['include_hello_world'])
                    msg = f"Package '{data['name']}' {'created successfully.' if ok else 'creation failed.'}"
                    self.output_display.append_text(f"[INFO] {msg}")
                    logger.info(msg)
                    if ok:
                        QMessageBox.information(self, "Package Creation", msg)
                        self.update_active_workspace_display(f"Package '{data['name']}' Created")
                        # TODO: Optionally refresh workspace explorer here
                    else:
                        QMessageBox.critical(self, "Package Creation Error", msg)
                        self.update_active_workspace_display(f"Package '{data['name']}' Creation Failed")
                except Exception as e:
                    error_msg = f"Critical error during package creation: {e}"
                    logger.error(error_msg, exc_info=True)
                    self.output_display.append_text(f"[ERROR] {error_msg}")
                    QMessageBox.critical(self, "Package Creation Error", error_msg)
                    self.update_active_workspace_display("Package Creation Error")
            else: # Should not happen if dialog accepted
                logger.warning("Create package dialog accepted but no data returned.")
        else:
            logger.debug("Package creation cancelled by user.")
            self.output_display.append_text("[INFO] Package creation cancelled.")

    def on_refresh_workspace_explorer(self):
        logger.info("Refresh Workspace Explorer action triggered.")
        self.output_display.append_text("[INFO] Refreshing workspace explorer...")
        # The update_active_workspace_display method now has logic to call
        # _update_workspace_explorer if "refresh workspace" is in the action_description.
        self.update_active_workspace_display("Refresh Workspace")
        # If you wanted a more direct call, you could do:
        # self._update_workspace_explorer()
        # self.output_display.append_text("[INFO] Workspace explorer refreshed.")
    def _start_worker_task(self, task_description: str, target_fn: Callable, *args, **kwargs):
        """Helper to start a worker, managing UI busy state."""
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is already running. Please wait.")
            return False
        
        logger.info(f"Starting task: {task_description}")
        self.output_display.append_text(f"\n--- Starting: {task_description} ---")
        self.update_active_workspace_display(task_description) # Sets busy state and current_action_description

        self.current_worker = Worker(target_fn, *args, **kwargs)
        self.current_worker.signals.progress.connect(self.output_display.append_text)
        self.current_worker.signals.finished.connect(self._on_worker_finished)
        self.current_worker.signals.error.connect(self._on_worker_error)
        # Specific signals like result and process_started are connected by the caller if needed
        self.current_worker.start()
        return True

    def on_build_workspace(self):
        if self._start_worker_task("Build Workspace", self.tool_invoker.colcon_build):
            # Connect result for build/clean
            self.current_worker.signals.result.connect(self._on_build_clean_result)

    def on_clean_workspace(self):
        if self._start_worker_task("Clean Workspace", self.tool_invoker.colcon_clean):
            # Connect result for build/clean
            self.current_worker.signals.result.connect(self._on_build_clean_result)

    def _on_build_clean_result(self, result_tuple: tuple):
        # result_tuple for build/clean: (success, stdout_str, stderr_str)
        # ToolInvoker might return 4th element as None if Popen object not applicable
        success, stdout_str, stderr_str = result_tuple[:3]
        logger.debug(f"Build/Clean task result: Success={success}")
        task_name = self.current_action_description # Should be "Build Workspace" or "Clean Workspace"
        if not success: # Could be actual error or just non-zero exit like for clean
            # For clean, shutil might not produce much stderr, ToolInvoker logs its own messages
            # For build, stderr_str could contain compiler errors
            if stderr_str: # Only show if there's actual stderr content
                 self.output_display.append_text(f"\n[TASK STDERR - {task_name}]:\n{stderr_str.strip()}")
            QMessageBox.warning(self, f"{task_name} Result", f"{task_name} finished. Non-zero exit or errors occurred. Please check output.")
        else:
            self.output_display.append_text(f"[INFO] {task_name} completed successfully.")
        # _on_worker_finished handles final UI state update and status message

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

    def _on_run_launch_result(self, result_tuple: tuple):
        # result_tuple for run/launch: (success, stdout_str, stderr_str, finished_process_obj)
        success, stdout_str, stderr_str, finished_process_obj = result_tuple
        task_name = self.current_action_description # Should be "Run Executable..." or "Launch File..."
        exit_code = finished_process_obj.returncode if finished_process_obj else "N/A (process object missing)"
        logger.debug(f"Run/Launch task ('{task_name}') worker result: Success={success}, Process Exit Code={exit_code}")

        if not success:
            # SIGTERM (-15) or SIGKILL (-9) are results of user stopping, not usually an error popup.
            if finished_process_obj and exit_code not in [0, -15, -9, 130]: # 130 is often Ctrl+C
                # Some actual error or unexpected termination
                if stderr_str: # Show stderr if available
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
        task_desc = self.current_action_description if self.current_action_description else "Background task"
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
            'window_geometry': self.saveGeometry().data().hex(),
        }
        if hasattr(self, 'vertical_splitter'):
            state['splitter_state'] = self.vertical_splitter.saveState().data().hex()
        return state

    def closeEvent(self, event):
        """Override closeEvent to allow UI state saving from outside."""
        logger.info("Close event received. ROSBuddy shutting down...")
        if self.running_ros_process and self.running_ros_process.poll() is None:
            logger.info(f"Attempting to stop active ROS process (PID: {self.running_ros_process.pid}) on exit.")
            # Use a more direct stop here, as on_stop_task updates UI which might be closing
            try:
                self.running_ros_process.terminate()
                self.running_ros_process.wait(timeout=0.5) # Brief wait for terminate
                if self.running_ros_process.poll() is None:
                    self.running_ros_process.kill()
                    self.running_ros_process.wait(timeout=0.2)
                logger.info(f"ROS Process PID {self.running_ros_process.pid} stop attempt on exit. Final poll: {self.running_ros_process.poll()}")
            except Exception as e:
                logger.error(f"Error stopping ROS process on exit: {e}")
        
        # Worker handling (QThread usually exits when app does if not detached, but explicit quit is cleaner)
        if self.current_worker and self.current_worker.isRunning():
            logger.info("Requesting active worker to quit on application exit.")
            # self.current_worker.quit() # Request clean exit
            # self.current_worker.wait(500) # Wait max 500ms
            # if self.current_worker.isRunning(): # Still running?
            #     logger.warning("Worker did not stop on quit(), forcing terminate(). This may be unsafe.")
            #     self.current_worker.terminate() # Force terminate
        super().closeEvent(event)

# Standalone Test (keep your dummy classes here for testing MainWindow in isolation)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # --- Dummy Classes for Standalone Test ---
    # (These should be the same dummy classes you had before)
    class DummyProcess(subprocess.Popen):
        # ... (implementation as you had) ...
        pass
    class DummyPackageInfo:
        # ... (implementation as you had) ...
        pass
    class DummyPackageDiscovery:
        # ... (implementation as youhad) ...
        pass
    class DummyWorkspaceManager:
        # ... (implementation as you had) ...
        pass
    class DummyToolInvoker:
        # ... (implementation as you had, ensure it uses DummyProcess and has process_started_callback kwarg) ...
        def _dummy_task_simulated_process(self, task_name, args_tuple, realtime_output_callback, process_started_callback=None, **kwargs):
            simulated_process = DummyProcess(pid=os.getpid()+100) # Give it a unique-ish PID
            if process_started_callback:
                process_started_callback(simulated_process)
            
            logger.debug(f"DummyToolInvoker: {task_name} called with {args_tuple}. PID: {simulated_process.pid}")
            realtime_output_callback(f"[DUMMY_TOOL] Starting dummy {task_name}...")
            time.sleep(0.1)
            
            for i in range(5): # Shorter for quicker tests
                if simulated_process.poll() is not None:
                    realtime_output_callback(f"[DUMMY_TOOL] {task_name} detected external stop (poll={simulated_process.poll()}).")
                    break
                realtime_output_callback(f"[DUMMY_TOOL] {task_name} progress {i+1}/5")
                time.sleep(0.3)
            
            final_success = True
            if "error_test" in args_tuple:
                realtime_output_callback(f"[DUMMY_TOOL][ERR] Simulated error in {task_name}")
                final_success = False # Simulate error
                # raise ValueError(f"Simulated error from {task_name}") # Don't raise, return error status
            
            # Simulate process ending if not stopped externally
            if simulated_process.poll() is None:
                simulated_process._poll_result = 0 if final_success else 1

            realtime_output_callback(f"[DUMMY_TOOL] Dummy {task_name} finished.")
            return final_success, f"Dummy {task_name} stdout", ("Error" if not final_success else ""), simulated_process

        def colcon_build(self, realtime_output_callback=None, process_started_callback=None):
             return self._dummy_task_simulated_process("colcon_build", (), realtime_output_callback, process_started_callback=process_started_callback)
        def colcon_clean(self, realtime_output_callback=None, process_started_callback=None):
             return self._dummy_task_simulated_process("colcon_clean", (), realtime_output_callback, process_started_callback=process_started_callback)
        def ros2_launch(self, package_name, launch_file_name, args=None, cwd=None, realtime_output_callback=None, process_started_callback=None):
             return self._dummy_task_simulated_process("ros2_launch", (package_name, launch_file_name), realtime_output_callback, process_started_callback=process_started_callback)
        def ros2_run(self, package_name, executable_name, args=None, cwd=None, realtime_output_callback=None, process_started_callback=None):
             return self._dummy_task_simulated_process("ros2_run", (package_name, executable_name), realtime_output_callback, process_started_callback=process_started_callback)

    # --- End Dummy Classes ---

    # Setup basic logging for the standalone test if main_app isn't run
    if not logging.getLogger().handlers: # Check if handlers are already added (e.g. by main_app)
        log_format = '%(asctime)s - %(levelname)s - %(name)s : %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=log_format, stream=sys.stdout)


    ws_m = DummyWorkspaceManager()
    ti = DummyToolInvoker()
    # Create a dummy workspace for testing
    ws_m.set_active_workspace(os.path.expanduser("~/dummy_rosbuddy_ws_test"))


    # Mock create_package_scaffolding if it's called by on_create_package
    original_create_scaffolding = create_package_scaffolding # Keep original
    def mock_create_pkg_scaffold(base_path, pkg_cfg, include_hw):
        logger.info(f"MOCK: create_package_scaffolding called for {pkg_cfg.name}")
        return True
    # Replace the actual function with the mock for testing UI flow
    # This requires rosbuddy.core_logic.create_package_scaffolding to be the actual import path
    # For a direct import like 'from rosbuddy.core_logic import create_package_scaffolding', this is harder to mock
    # Simpler: just ensure on_create_package doesn't crash.
    # sys.modules['rosbuddy.core_logic'].create_package_scaffolding = mock_create_pkg_scaffold # If imported as module

    main_win = MainWindow(workspace_manager=ws_m, tool_invoker=ti)
    main_win.show()
    exit_code = app.exec()
    # create_package_scaffolding = original_create_scaffolding # Restore
    sys.exit(exit_code)