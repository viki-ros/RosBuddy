from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                           QTreeView, QLabel, QCompleter, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QStringListModel, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import rclpy
from rclpy.utilities import get_available_rmw_implementations
from ament_index_python.packages import get_packages_with_prefixes
import importlib
import re

class MessageTypeSelector(QGroupBox):
    """Widget for selecting ROS 2 message types."""
    
    type_selected = pyqtSignal(str)  # Emits selected message type
    
    def __init__(self, node_type, parent=None):
        super().__init__("Message Type", parent)
        self.node_type = node_type
        self.available_types = []
        self.init_ui()
        self.load_available_types()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(f"Filter {self._get_type_category()} types...")
        layout.addWidget(self.filter_input)
        
        # Tree view for types
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Message Types"])
        
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.tree_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setExpandsOnDoubleClick(True)
        layout.addWidget(self.tree_view)
        
        # Results label
        self.results_label = QLabel("Loading available types...")
        layout.addWidget(self.results_label)
        
        # Connect signals
        self.filter_input.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.tree_view.clicked.connect(self._handle_selection)
    
    def _get_type_category(self):
        """Get the category of types based on node type."""
        if self.node_type in ["Publisher", "Subscriber"]:
            return "message"
        elif self.node_type == "Service":
            return "service"
        else:  # Action
            return "action"
    
    def load_available_types(self):
        """Load available ROS 2 message types."""
        try:
            # Initialize ROS 2 if needed
            if not rclpy.ok():
                rclpy.init()
            
            # Get all ROS 2 packages
            packages = get_packages_with_prefixes()
            
            # Clear existing items
            self.tree_model.clear()
            self.tree_model.setHorizontalHeaderLabels(["Message Types"])
            
            # Track packages and types
            package_items = {}
            type_count = 0
            
            # Collect message types
            for package_name in sorted(packages):
                package_item = None
                
                if self.node_type in ["Publisher", "Subscriber"]:
                    # Look for message types
                    try:
                        msgs = importlib.import_module(f"{package_name}.msg")
                        for name in dir(msgs):
                            if (not name.startswith('_') and 
                                not name.endswith('_Request') and 
                                not name.endswith('_Response')):
                                if package_item is None:
                                    package_item = QStandardItem(package_name)
                                    self.tree_model.appendRow(package_item)
                                msg_item = QStandardItem(name)
                                msg_item.setData(f"{package_name}/msg/{name}", Qt.ItemDataRole.UserRole)
                                package_item.appendRow(msg_item)
                                type_count += 1
                    except ImportError:
                        pass
                
                elif self.node_type == "Service":
                    # Look for service types
                    try:
                        srvs = importlib.import_module(f"{package_name}.srv")
                        for name in dir(srvs):
                            if not name.startswith('_'):
                                if package_item is None:
                                    package_item = QStandardItem(package_name)
                                    self.tree_model.appendRow(package_item)
                                srv_item = QStandardItem(name)
                                srv_item.setData(f"{package_name}/srv/{name}", Qt.ItemDataRole.UserRole)
                                package_item.appendRow(srv_item)
                                type_count += 1
                    except ImportError:
                        pass
                
                else:  # Action
                    # Look for action types
                    try:
                        actions = importlib.import_module(f"{package_name}.action")
                        for name in dir(actions):
                            if not name.startswith('_'):
                                if package_item is None:
                                    package_item = QStandardItem(package_name)
                                    self.tree_model.appendRow(package_item)
                                action_item = QStandardItem(name)
                                action_item.setData(f"{package_name}/action/{name}", Qt.ItemDataRole.UserRole)
                                package_item.appendRow(action_item)
                                type_count += 1
                    except ImportError:
                        pass
            
            # Expand all items for better visibility
            self.tree_view.expandAll()
            
            # Update label
            self.results_label.setText(f"Found {type_count} types")
            
        except Exception as e:
            self.results_label.setText(f"Error loading types: {str(e)}")
    
    def _handle_selection(self, index):
        """Handle type selection from tree."""
        if not index.isValid():
            return
            
        # Get the selected item
        source_index = self.proxy_model.mapToSource(index)
        item = self.tree_model.itemFromIndex(source_index)
        
        # Only emit if it's a leaf node (actual type, not package)
        if item and not item.hasChildren():
            msg_type = item.data(Qt.ItemDataRole.UserRole)
            if msg_type:
                self.type_selected.emit(msg_type)
    
    def get_selected_type(self):
        """Get the currently selected type."""
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            source_index = self.proxy_model.mapToSource(indexes[0])
            item = self.tree_model.itemFromIndex(source_index)
            if item and not item.hasChildren():
                return item.data(Qt.ItemDataRole.UserRole)
        return ""
    
    def set_selected_type(self, type_name):
        """Set the selected type."""
        if not type_name:
            return
            
        # Clear current selection
        self.tree_view.clearSelection()
        
        # Find and select the type
        for package_idx in range(self.tree_model.rowCount()):
            package_item = self.tree_model.item(package_idx)
            for type_idx in range(package_item.rowCount()):
                type_item = package_item.child(type_idx)
                if type_item.data(Qt.ItemDataRole.UserRole) == type_name:
                    # Select the item
                    index = self.tree_model.indexFromItem(type_item)
                    proxy_index = self.proxy_model.mapFromSource(index)
                    self.tree_view.setCurrentIndex(proxy_index)
                    return 