from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QHBoxLayout
from rosbuddy.ui.components.message_type_selector import MessageTypeSelector

class CppNodeCreatorDialog(QDialog):
    """Dialog for creating a new C++ ROS 2 node."""
    def __init__(self, package_discovery, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New C++ Node")
        layout = QVBoxLayout(self)

        # Package selection
        layout.addWidget(QLabel("Select ament_cmake Package:"))
        self.package_combo = QComboBox()
        self.packages = [pkg for pkg in package_discovery.find_packages_in_active_workspace() if pkg.build_type == "ament_cmake"]
        for pkg in self.packages:
            self.package_combo.addItem(pkg.name)
        layout.addWidget(self.package_combo)

        # Node name
        layout.addWidget(QLabel("Node Name:"))
        self.node_name_edit = QLineEdit()
        self.node_name_edit.setPlaceholderText("e.g., my_sensor_processor")
        layout.addWidget(self.node_name_edit)

        # Node role/template
        layout.addWidget(QLabel("Node Role/Template:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Generic rclcpp::Node", "Publisher Node", "Subscriber Node"])
        layout.addWidget(self.role_combo)

        # Conditional: topic and message type
        self.topic_label = QLabel("Topic Name:")
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("e.g., /chatter")
        self.msg_type_selector = MessageTypeSelector(node_type="Publisher")
        layout.addWidget(self.topic_label)
        layout.addWidget(self.topic_edit)
        layout.addWidget(self.msg_type_selector)
        self.topic_label.hide()
        self.topic_edit.hide()
        self.msg_type_selector.hide()

        self.role_combo.currentTextChanged.connect(self._on_role_changed)

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

    def _on_role_changed(self, role):
        if role in ("Publisher Node", "Subscriber Node"):
            self.topic_label.show()
            self.topic_edit.show()
            self.msg_type_selector.show()
            self.msg_type_selector.node_type = "Publisher" if role == "Publisher Node" else "Subscriber"
            self.msg_type_selector.load_available_types()
        else:
            self.topic_label.hide()
            self.topic_edit.hide()
            self.msg_type_selector.hide()

    def _on_msg_type_selected(self, msg_type):
        self.selected_msg_type = msg_type

    def _validate_node_name(self, text):
        import re
        valid = bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', text.strip()))
        self.ok_btn.setEnabled(valid)
        if not valid and text.strip():
            self.node_name_edit.setStyleSheet("border: 1px solid red;")
            self.node_name_edit.setToolTip("Invalid C++ identifier. Use letters, numbers, and underscores. Must not start with a number.")
        else:
            self.node_name_edit.setStyleSheet("")
            self.node_name_edit.setToolTip("")

    def get_data(self):
        role = self.role_combo.currentText()
        return {
            'package_name': self.package_combo.currentText(),
            'node_name': self.node_name_edit.text().strip(),
            'role': role,
            'topic_name': self.topic_edit.text().strip() if role in ("Publisher Node", "Subscriber Node") else None,
            'message_type': self.selected_msg_type or self.msg_type_selector.tree_view.currentIndex().data() if role in ("Publisher Node", "Subscriber Node") else None,
        }
