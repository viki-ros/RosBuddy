# rosbuddy/ui/views/ros_tools_navigation_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeView, QStyledItemDelegate, QStyleOptionViewItem, QStyle, QAbstractItemView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPainter
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from rosbuddy.utils.icon_manager import IconManager

class ModernTreeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # Custom paint for full-width highlight, rounded corners, hover, etc.
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = option.rect.adjusted(2, 2, -2, -2)
            painter.setBrush(option.palette.highlight())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 8, 8)
            painter.restore()
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = option.rect.adjusted(2, 2, -2, -2)
            painter.setBrush(option.palette.alternateBase())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 8, 8)
            painter.restore()
        super().paint(painter, option, index)

class RosToolsNavigationView(QWidget):
    item_activated = pyqtSignal(str)  # Emits the action_id of the clicked sub-item

    def __init__(self, icon_manager: IconManager, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self._init_ui()
        self._populate_model()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search ROS Tools...")
        self.search_bar.setClearButtonEnabled(True)
        layout.addWidget(self.search_bar)
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(ModernTreeDelegate())
        layout.addWidget(self.tree, 1)
        self.model = QStandardItemModel()
        self.tree.setModel(self.model)
        self.search_bar.textChanged.connect(self._filter_tree)
        self.tree.clicked.connect(self._on_item_clicked)

    def _populate_model(self):
        self.model.clear()
        # Top-level categories and their children
        nav = [
            ("Overview", "gauge", [
                ("Workspace Dashboard", "dashboard", "dashboard")
            ]),
            ("Create New...", "add", [
                ("+ Workspace", "workspace", "create_workspace"),
                ("+ Package", "package", "create_package"),
                ("+ Node (C++/Python)", "node", "create_node"),
                ("+ Interface (Msg/Srv/Action)", "interface", "create_interface"),
                ("+ Launch File (Python/XML)", "launch", "create_launch_file"),
                ("+ Parameter File (YAML)", "parameter", "create_param_file")
            ]),
            ("Workspace Management", "folder-settings", [
                ("Manage Dependencies", "dependency", "manage_deps"),
                ("Configure Build System", "build", "configure_build")
            ]),
            ("Introspection & Visualization", "eye", [
                ("ROS Graph Visualizer", "ros-graph", "ros_graph"),
                ("Topic Monitor", "topic", "topic_monitor"),
                ("Service Explorer", "service", "service_explorer"),
                ("Action Explorer", "action", "action_explorer"),
                ("Parameter Browser", "parameter", "param_browser"),
                ("TF Tree Visualizer", "tf", "tf_tree"),
                ("ROS Doctor Dashboard", "ros-doctor", "ros_doctor")
            ]),
            ("Simulation (Future)", "cube", [])
        ]
        for cat, cat_icon, children in nav:
            cat_item = QStandardItem(self.icon_manager.get_icon(cat_icon), cat)
            cat_item.setEditable(False)
            cat_item.setSelectable(False)
            for label, icon, action_id in children:
                child = QStandardItem(self.icon_manager.get_icon(icon), label)
                child.setEditable(False)
                child.setData(action_id, Qt.ItemDataRole.UserRole)
                cat_item.appendRow(child)
            self.model.appendRow(cat_item)

    def _filter_tree(self, text):
        # Simple filter: expand all and hide rows that don't match
        for i in range(self.model.rowCount()):
            cat_item = self.model.item(i)
            match_cat = text.lower() in cat_item.text().lower()
            any_child_visible = False
            for j in range(cat_item.rowCount()):
                child = cat_item.child(j)
                match_child = text.lower() in child.text().lower()
                self.tree.setRowHidden(j, self.model.index(i, 0), not (match_cat or match_child))
                if match_child:
                    any_child_visible = True
            self.tree.setRowHidden(i, self.model.invisibleRootItem().index(), not (match_cat or any_child_visible))
        self.tree.expandAll()

    def _on_item_clicked(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        action_id = item.data(Qt.ItemDataRole.UserRole)
        if action_id:
            self.item_activated.emit(action_id)
