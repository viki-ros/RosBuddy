from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QHBoxLayout
from rosbuddy.ui.components.message_type_selector import MessageTypeSelector

class NodeCreatorDialog(QDialog):
    """Dialog for creating a new ROS 2 node with selection-based UI."""
    def __init__(self, package_discovery, parent=None, build_type="ament_python"):
        super().__init__(parent)
        self.build_type = build_type
        self.setWindowTitle(f"Create New {'Python' if build_type == 'ament_python' else 'C++'} Node")
        layout = QVBoxLayout(self)

        # Package selection (no typing)
        layout.addWidget(QLabel("Select Package:"))
        self.package_combo = QComboBox()
        self.packages = [pkg for pkg in package_discovery.find_packages_in_active_workspace() if pkg.build_type == build_type]
        for pkg in self.packages:
            self.package_combo.addItem(pkg.name)
        layout.addWidget(self.package_combo)

        # Node name (typing, validated)
        layout.addWidget(QLabel("Node Name:"))
        self.node_name_edit = QLineEdit()
        self.node_name_edit.setPlaceholderText("e.g., my_publisher")
        layout.addWidget(self.node_name_edit)

        # Node type selection
        layout.addWidget(QLabel("Node Type:"))
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItems(["Publisher", "Subscriber"])
        layout.addWidget(self.node_type_combo)

        # Topic name (typing)
        layout.addWidget(QLabel("Topic Name:"))
        self.topic_name_edit = QLineEdit()
        self.topic_name_edit.setPlaceholderText("e.g., /chatter")
        layout.addWidget(self.topic_name_edit)

        # Message type selector (integrated)
        self.msg_type_selector = MessageTypeSelector(node_type="Publisher")
        layout.addWidget(self.msg_type_selector)
        self.node_type_combo.currentTextChanged.connect(self._on_node_type_changed)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Create")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Validation
        self.node_name_edit.textChanged.connect(self._validate_node_name)
        self._validate_node_name(self.node_name_edit.text())
        self.selected_msg_type = None
        self.msg_type_selector.type_selected.connect(self._on_msg_type_selected)

    def _on_node_type_changed(self, node_type):
        self.msg_type_selector.node_type = node_type
        self.msg_type_selector.load_available_types()

    def _on_msg_type_selected(self, msg_type):
        self.selected_msg_type = msg_type

    def _validate_node_name(self, text):
        import re
        valid = bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', text.strip()))
        self.ok_btn.setEnabled(valid)
        if not valid and text.strip():
            self.node_name_edit.setStyleSheet("border: 1px solid red;")
            self.node_name_edit.setToolTip("Invalid Python identifier. Use letters, numbers, and underscores. Must not start with a number.")
        else:
            self.node_name_edit.setStyleSheet("")
            self.node_name_edit.setToolTip("")

    def get_data(self):
        return {
            'package_name': self.package_combo.currentText(),
            'node_name': self.node_name_edit.text().strip(),
            'node_type': self.node_type_combo.currentText(),
            'topic_name': self.topic_name_edit.text().strip(),
            'message_type': self.selected_msg_type or self.msg_type_selector.tree_view.currentIndex().data(),
        }
