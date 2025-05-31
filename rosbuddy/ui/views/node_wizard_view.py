# rosbuddy/ui/views/node_wizard_view.py
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTabWidget, QWidget, QSplitter, QScrollArea, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from .base_view import BaseView
from ..components.visual_node_builder import VisualNodeBuilder
from ..dialogs.node_creator_dialog import NodeCreatorDialog
from ..dialogs.cpp_node_creator_dialog import CppNodeCreatorDialog

class NodeWizardView(BaseView):
    """
    Enhanced Node Wizard integrating visual node builder with existing dialogs.
    """
    node_created = pyqtSignal(dict)  # Emit when a node is successfully created
    
    def __init__(self, parent=None):
        super().__init__(view_title="Node Wizard", parent=parent)
        self.setObjectName("nodeWizardView")
        self.package_discovery = None  # Will be set by parent
        self._init_enhanced_ui()
        
    def set_package_discovery(self, package_discovery):
        """Set the package discovery instance."""
        self.package_discovery = package_discovery
        
    def _init_enhanced_ui(self):
        """Initialize the enhanced Node Wizard UI."""
        # Clear the placeholder content
        main_layout = self.clear_base_layout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Title Section
        title_label = QLabel("🧙 Node Wizard")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Create ROS 2 nodes using either the visual designer or traditional forms. "
            "The visual designer lets you configure nodes with drag-and-drop, while "
            "forms provide quick creation with templates."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #aaa; margin-bottom: 15px;")
        main_layout.addWidget(desc_label)
        
        # Create mode selection buttons
        mode_container = QWidget()
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(15)
        
        self.mode_group = QButtonGroup()
        
        # Visual Designer Mode Button
        self.visual_mode_btn = QPushButton("🎨 Visual Designer")
        self.visual_mode_btn.setCheckable(True)
        self.visual_mode_btn.setChecked(True)  # Default mode
        self.visual_mode_btn.setMinimumHeight(40)
        self.visual_mode_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:checked {
                background-color: #0d7377;
                color: white;
            }
        """)
        
        # Quick Create Mode Button  
        self.quick_mode_btn = QPushButton("⚡ Quick Create")
        self.quick_mode_btn.setCheckable(True)
        self.quick_mode_btn.setMinimumHeight(40)
        self.quick_mode_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:checked {
                background-color: #0d7377;
                color: white;
            }
        """)
        
        self.mode_group.addButton(self.visual_mode_btn, 0)
        self.mode_group.addButton(self.quick_mode_btn, 1)
        
        mode_layout.addStretch()
        mode_layout.addWidget(self.visual_mode_btn)
        mode_layout.addWidget(self.quick_mode_btn)
        mode_layout.addStretch()
        
        main_layout.addWidget(mode_container)
        
        # Create tab widget for different modes
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setTabBarAutoHide(True)  # Hide tab bar since we use buttons
        main_layout.addWidget(self.mode_tabs, 1)  # Take remaining space
        
        # Initialize modes
        self._init_visual_mode()
        self._init_quick_mode()
        
        # Connect mode switching
        self.mode_group.buttonClicked.connect(self._switch_mode)
        
    def _init_visual_mode(self):
        """Initialize the visual node designer mode."""
        visual_widget = QWidget()
        visual_layout = QVBoxLayout(visual_widget)
        visual_layout.setContentsMargins(0, 0, 0, 0)
        
        # Integrate the existing VisualNodeBuilder
        self.visual_builder = VisualNodeBuilder()
        self.visual_builder.node_created.connect(self._on_visual_node_created)
        visual_layout.addWidget(self.visual_builder)
        
        self.mode_tabs.addTab(visual_widget, "Visual Designer")
        
    def _init_quick_mode(self):
        """Initialize the quick create mode with form dialogs."""
        quick_widget = QWidget()
        quick_layout = QVBoxLayout(quick_widget)
        quick_layout.setContentsMargins(20, 20, 20, 20)
        quick_layout.setSpacing(20)
        
        # Quick mode title
        quick_title = QLabel("⚡ Quick Node Creation")
        quick_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        quick_layout.addWidget(quick_title)
        
        # Instructions
        instructions = QLabel(
            "Choose a node creation template below. Each option will open a "
            "specialized dialog with the most common settings for that node type."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #bbb; margin-bottom: 20px;")
        quick_layout.addWidget(instructions)
        
        # Quick creation buttons
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        # Python Node Button
        python_btn = QPushButton("🐍 Create Python Node")
        python_btn.setMinimumHeight(50)
        python_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                background-color: #2d3748;
                border: 1px solid #4a5568;
            }
            QPushButton:hover {
                background-color: #3d4a5c;
                border-color: #5a6a7a;
            }
        """)
        python_btn.clicked.connect(self._create_python_node)
        buttons_layout.addWidget(python_btn)
        
        # C++ Node Button
        cpp_btn = QPushButton("⚙️ Create C++ Node")
        cpp_btn.setMinimumHeight(50)
        cpp_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                background-color: #2d3748;
                border: 1px solid #4a5568;
            }
            QPushButton:hover {
                background-color: #3d4a5c;
                border-color: #5a6a7a;
            }
        """)
        cpp_btn.clicked.connect(self._create_cpp_node)
        buttons_layout.addWidget(cpp_btn)
        
        # Template Node Button (Future enhancement)
        template_btn = QPushButton("📋 Create from Template")
        template_btn.setMinimumHeight(50)
        template_btn.setEnabled(False)  # Disabled for now
        template_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                background-color: #2d3748;
                border: 1px solid #4a5568;
                color: #888;
            }
        """)
        buttons_layout.addWidget(template_btn)
        
        quick_layout.addWidget(buttons_container)
        quick_layout.addStretch()  # Push content to top
        
        self.mode_tabs.addTab(quick_widget, "Quick Create")
        
    def _switch_mode(self, button):
        """Switch between visual and quick modes."""
        mode_index = self.mode_group.id(button)
        self.mode_tabs.setCurrentIndex(mode_index)
        
    def _create_python_node(self):
        """Open Python node creation dialog."""
        if not self.package_discovery:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Package discovery not available.")
            return
            
        dialog = NodeCreatorDialog(
            self.package_discovery, 
            parent=self, 
            build_type="ament_python"
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            node_data = dialog.get_data()
            self.node_created.emit({
                'type': 'python',
                'data': node_data,
                'source': 'quick_create'
            })
            
    def _create_cpp_node(self):
        """Open C++ node creation dialog."""
        if not self.package_discovery:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Package discovery not available.")
            return
            
        dialog = CppNodeCreatorDialog(self.package_discovery, parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            node_data = dialog.get_data()
            self.node_created.emit({
                'type': 'cpp',
                'data': node_data,
                'source': 'quick_create'
            })
            
    def _on_visual_node_created(self, node_config):
        """Handle node creation from visual builder."""
        self.node_created.emit({
            'type': 'visual',
            'data': node_config,
            'source': 'visual_builder'
        })
