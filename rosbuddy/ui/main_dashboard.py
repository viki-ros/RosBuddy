from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                               QDockWidget, QMenuBar, QStatusBar, QToolBar)
from PyQt6.QtCore import Qt, QSize, QSettings, QByteArray
from PyQt6.QtGui import QAction, QIcon

from .components.visual_node_builder import VisualNodeBuilder
from .components.parameter_configurator import ParameterConfigurator
from .components.launch_builder import LaunchBuilder
from .components import (OutputConsole, PackageExplorer)

class MainDashboard(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ROSBuddy - Visual ROS 2 Development Environment")
        self.setObjectName("MainWindow")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        # Create central widget with tabs
        self.central_tabs = QTabWidget()
        self.setCentralWidget(self.central_tabs)

        # Create main tools
        self.node_builder = VisualNodeBuilder()
        self.param_config = ParameterConfigurator()
        self.launch_builder = LaunchBuilder()

        # Add main tools to tabs
        self.central_tabs.addTab(self.node_builder, "Node Builder")
        self.central_tabs.addTab(self.param_config, "Parameter Configuration")
        self.central_tabs.addTab(self.launch_builder, "Launch Configuration")

        # Create dock widgets for additional tools
        self.create_dock_widgets()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create toolbar
        self.create_toolbar()

        # Connect signals
        self.connect_signals()

    def create_dock_widgets(self):
        # Package Explorer
        self.pkg_explorer = QDockWidget("Package Explorer", self)
        self.pkg_explorer.setObjectName("pkg_explorer_dock")
        self.pkg_explorer.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                        Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.pkg_explorer)

        # Output Console
        self.output_console = QDockWidget("Output Console", self)
        self.output_console.setObjectName("output_console_dock")
        self.output_console.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_console)

        # Properties Panel
        self.properties_panel = QDockWidget("Properties", self)
        self.properties_panel.setObjectName("properties_dock")
        self.properties_panel.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_panel)

        # Launch Builder
        self.launch_builder_dock = QDockWidget("Launch Builder", self)
        self.launch_builder_dock.setObjectName("launch_builder_dock")
        self.launch_builder_dock.setWidget(self.launch_builder)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.launch_builder_dock)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        new_action = QAction("New Project", self)
        open_action = QAction("Open Project", self)
        save_action = QAction("Save", self)
        file_menu.addActions([new_action, open_action, save_action])

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")
        undo_action = QAction("Undo", self)
        redo_action = QAction("Redo", self)
        edit_menu.addActions([undo_action, redo_action])

        # View Menu
        view_menu = menubar.addMenu("View")
        view_pkg_explorer = QAction("Package Explorer", self)
        view_output = QAction("Output Console", self)
        view_properties = QAction("Properties Panel", self)
        view_menu.addActions([view_pkg_explorer, view_output, view_properties])

        # Build Menu
        build_menu = menubar.addMenu("Build")
        build_all_action = QAction("Build All", self)
        clean_action = QAction("Clean", self)
        build_menu.addActions([build_all_action, clean_action])

        # Run Menu
        run_menu = menubar.addMenu("Run")
        run_action = QAction("Run", self)
        debug_action = QAction("Debug", self)
        run_menu.addActions([run_action, debug_action])

        # Tools Menu
        tools_menu = menubar.addMenu("Tools")
        settings_action = QAction("Settings", self)
        tools_menu.addAction(settings_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setObjectName("main_toolbar")
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)

        # Add quick access tools
        new_node_action = QAction("New Node", self)
        new_launch_action = QAction("New Launch", self)
        build_action = QAction("Build", self)
        run_action = QAction("Run", self)
        
        toolbar.addActions([new_node_action, new_launch_action, build_action, run_action])

    def connect_signals(self):
        # Connect node builder signals
        self.node_builder.node_created.connect(self.handle_node_created)
        
        # Connect parameter configurator signals
        self.param_config.parameter_updated.connect(self.handle_parameter_updated)
        
        # Connect launch builder signals
        self.launch_builder.launch_updated.connect(self.handle_launch_updated)

    def handle_node_created(self, node_config):
        self.statusBar.showMessage(f"Node created: {node_config['name']}")

    def handle_parameter_updated(self, parameters):
        self.statusBar.showMessage(f"Parameters updated: {len(parameters)} parameters")

    def handle_launch_updated(self, launch_config):
        self.statusBar.showMessage(f"Launch configuration updated: {len(launch_config['nodes'])} nodes")

    def load_settings(self):
        """Load window state from settings."""
        settings = QSettings("ROSBuddy", "GUI")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def save_settings(self):
        """Save window state to settings."""
        settings = QSettings("ROSBuddy", "GUI")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def closeEvent(self, event):
        """Save window state when closing."""
        self.save_settings()
        super().closeEvent(event) 