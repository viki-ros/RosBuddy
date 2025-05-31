from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel, QComboBox, QPushButton, QHBoxLayout, QDialogButtonBox, QWidget, QSpinBox, QCheckBox, QGroupBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import os

from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
from rosbuddy.ui.components.message_type_selector import MessageTypeSelector
from rosbuddy.ui.dialogs.select_dependency_dialog import SelectRosPackageDependencyDialog
from typing import Optional, List, Set
import re

class MessageTypeSelectorDialog(QDialog):
    def __init__(self, node_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Message Type")
        self.selected_type = None
        layout = QVBoxLayout(self)
        self.selector = MessageTypeSelector(node_type, self)
        layout.addWidget(self.selector)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.selector.type_selected.connect(self._on_type_selected)
        self.setLayout(layout)

    def _on_type_selected(self, type_str):
        self.selected_type = type_str
        self.accept()

    def _on_accept(self):
        # Accept only if a type is selected
        if self.selector.get_selected_type():
            self.selected_type = self.selector.get_selected_type()
            self.accept()
        else:
            # Optionally, show a warning or just do nothing
            pass

    def get_selected_type(self):
        return self.selected_type

class FieldRow(QWidget):
    def __init__(self, parent=None, type_list=None, type_doc_lookup=None):
        super().__init__(parent)
        self.type_doc_lookup = type_doc_lookup or (lambda t: "")
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        # Visual delineation
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(4, 4, 4, 4)
        # Field type dropdown (replacing label/button with a QComboBox for direct selection)
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.setToolTip("Select or enter the type for this field (e.g., int32, std_msgs/msg/String, geometry_msgs/msg/Pose, etc.). Start typing to filter or add a custom type.")
        common_types = [
            "bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64",
            "float32", "float64", "string", "std_msgs/msg/String", "std_msgs/msg/Bool", "geometry_msgs/msg/Pose"
        ]
        self.type_combo.addItems(common_types)
        self.type_combo.currentTextChanged.connect(lambda _: self._set_type(self.type_combo.currentText()))
        frame_layout.addWidget(self.type_combo)
        # Type doc label (hidden by default)
        self.type_doc = QLabel()
        self.type_doc.setVisible(False)
        frame_layout.addWidget(self.type_doc)
        # Field name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Field name (e.g., position)")
        self.name_edit.setToolTip("Enter the field name. Must follow ROS conventions.")
        self.name_edit.textChanged.connect(self._validate_name)
        frame_layout.addWidget(self.name_edit)
        # Name validation icon
        self.name_valid_icon = QLabel()
        frame_layout.addWidget(self.name_valid_icon)
        # Is Array?
        self.is_array = QCheckBox("Is Array?")
        self.is_array.setToolTip("Check if this field is an array type.")
        self.is_array.toggled.connect(self._on_array_toggled)
        frame_layout.addWidget(self.is_array)
        # Array type and size controls
        self.array_type_combo = QComboBox()
        self.array_type_combo.addItems(["Variable Size", "Fixed Size"])
        self.array_type_combo.setVisible(False)
        self.array_type_combo.currentTextChanged.connect(self._on_array_type_changed)
        frame_layout.addWidget(self.array_type_combo)
        self.array_size_spin = QSpinBox()
        self.array_size_spin.setMinimum(1)
        self.array_size_spin.setMaximum(1000)
        self.array_size_spin.setVisible(False)
        frame_layout.addWidget(self.array_size_spin)
        self.array_max_spin = QSpinBox()
        self.array_max_spin.setMinimum(1)
        self.array_max_spin.setMaximum(1000)
        self.array_max_spin.setVisible(False)
        frame_layout.addWidget(self.array_max_spin)
        # Is Constant? (only for primitives)
        self.is_constant = QCheckBox("Is Constant?")
        self.is_constant.setToolTip("If checked, this field is a constant (for primitives only). Name will be uppercased.")
        self.is_constant.setVisible(False)
        self.is_constant.toggled.connect(self._on_constant_toggled)
        frame_layout.addWidget(self.is_constant)
        self.constant_value_edit = QLineEdit()
        self.constant_value_edit.setPlaceholderText("Constant value")
        self.constant_value_edit.setVisible(False)
        frame_layout.addWidget(self.constant_value_edit)
        # Move Up/Down
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setToolTip("Move this field up.")
        frame_layout.addWidget(self.move_up_btn)
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setToolTip("Move this field down.")
        frame_layout.addWidget(self.move_down_btn)
        # Remove
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setFixedWidth(60)
        frame_layout.addWidget(self.remove_btn)
        layout.addWidget(frame)
        self.setLayout(layout)
        # Defaults
        self._set_type("int32")

    def _set_type(self, type_str):
        # No label to update, but update doc and constant visibility
        doc = self.type_doc_lookup(type_str)
        self.type_doc.setText(doc)
        self.type_doc.setVisible(bool(doc))
        if type_str in ["bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "string"]:
            self.is_constant.setVisible(True)
        else:
            self.is_constant.setVisible(False)
            self.is_constant.setChecked(False)
            self.constant_value_edit.setVisible(False)

    def _on_array_toggled(self, checked):
        self.array_type_combo.setVisible(checked)
        if checked:
            self.array_type_combo.setCurrentIndex(0)
            self._on_array_type_changed(self.array_type_combo.currentText())
        else:
            self.array_size_spin.setVisible(False)
            self.array_max_spin.setVisible(False)

    def _on_array_type_changed(self, text):
        if text == "Fixed Size":
            self.array_size_spin.setVisible(True)
            self.array_max_spin.setVisible(False)
        else:
            self.array_size_spin.setVisible(False)
            self.array_max_spin.setVisible(True)

    def _on_constant_toggled(self, checked):
        self.constant_value_edit.setVisible(checked)
        if checked:
            self.name_edit.setText(self.name_edit.text().upper())
        else:
            self.name_edit.setText(self.name_edit.text().lower())

    def _validate_name(self, text):
        # ROS field name: lower_case_with_underscores, starts with letter, no spaces, not a duplicate (handled in section)
        valid = bool(re.match(r'^[a-z][a-z0-9_]*$', text))
        if valid:
            self.name_edit.setStyleSheet("border: 1px solid green;")
            # Show a green tick icon
            tick_path = os.path.join(os.path.dirname(__file__), '../resources/icons/tick.png')
            if os.path.exists(tick_path):
                self.name_valid_icon.setPixmap(QPixmap(tick_path).scaled(16, 16))
            else:
                self.name_valid_icon.clear()
        else:
            self.name_edit.setStyleSheet("border: 1px solid red;")
            # Show a red cross icon
            cross_path = os.path.join(os.path.dirname(__file__), '../resources/icons/cross.png')
            if os.path.exists(cross_path):
                self.name_valid_icon.setPixmap(QPixmap(cross_path).scaled(16, 16))
            else:
                self.name_valid_icon.clear()

    def get_field(self):
        t = self.type_combo.currentText().strip()
        n = self.name_edit.text().strip()
        arr = self.is_array.isChecked()
        arr_type = self.array_type_combo.currentText() if arr else None
        arr_len = self.array_size_spin.value() if arr and arr_type == "Fixed Size" else None
        arr_max = self.array_max_spin.value() if arr and arr_type == "Variable Size" else None
        is_const = self.is_constant.isChecked() if self.is_constant.isVisible() else False
        const_val = self.constant_value_edit.text().strip() if is_const else None
        return (t, n, arr, arr_len, arr_max, is_const, const_val)
    def connect_field_changed(self, slot):
        self.name_edit.textChanged.connect(slot)
        self.is_array.toggled.connect(slot)
        self.array_type_combo.currentTextChanged.connect(slot)
        self.array_size_spin.valueChanged.connect(slot)
        self.array_max_spin.valueChanged.connect(slot)
        self.is_constant.toggled.connect(slot)
        self.constant_value_edit.textChanged.connect(slot)

class FieldSection(QGroupBox):
    def __init__(self, label, parent=None):
        super().__init__(label, parent)
        self.setToolTip(f"{label}: Add fields for this section.")
        self.layout = QVBoxLayout(self)
        self.rows: List[FieldRow] = []
        self.rows_layout = QVBoxLayout()
        self.layout.addLayout(self.rows_layout)
        self.add_btn = QPushButton("Add Field")
        self.add_btn.setToolTip(f"Add a new field to {label.lower()}.")
        self.add_btn.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_btn)
        self.setLayout(self.layout)
        self.add_row()
    def add_row(self):
        row = FieldRow(self)
        row.remove_btn.clicked.connect(lambda: self.remove_row(row))
        row.connect_field_changed(self.parent().parent().update_preview)
        self.rows.append(row)
        self.rows_layout.addWidget(row)
        self.parent().parent().update_preview()
    def remove_row(self, row):
        self.rows_layout.removeWidget(row)
        row.setParent(None)
        self.rows.remove(row)
        self.parent().parent().update_preview()
    def get_fields(self):
        return [r.get_field() for r in self.rows if r.name_edit.text().strip() and r.type_combo.currentText().strip()]

class MsgSrvActionEditorDialog(QDialog):
    """Dialog for creating a new ROS 2 message, service, or action file."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_deps = []
        self.setWindowTitle("Create New ROS Interface (.msg/.srv/.action)")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Interface Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["msg", "srv", "action"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        # Name
        layout.addWidget(QLabel("Interface Name (e.g., MotorStatus, SetTarget):"))
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.setToolTip("Enter or select the name for the interface file (without extension)")
        common_iface_names = ["Status", "Command", "Goal", "Result", "Feedback", "SetTarget", "GetStatus"]
        self.name_combo.addItems(common_iface_names)
        layout.addWidget(self.name_combo)
        self.name_edit = self.name_combo  # For compatibility with rest of code
        # Field sections
        self.sections = {}
        self.sections_widget = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_widget)
        layout.addWidget(self.sections_widget)
        # Real-time preview (must be created before _setup_sections)
        layout.addWidget(QLabel("Preview of generated file content:"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMinimumHeight(100)
        layout.addWidget(self.preview_edit)
        # Dependencies (move this up before _setup_sections)
        dep_layout = QHBoxLayout()
        dep_layout.addWidget(QLabel("Package Dependencies:"))
        self.dep_btn = QPushButton("Select Dependencies")
        self.dep_btn.clicked.connect(self._select_dependencies)
        dep_layout.addWidget(self.dep_btn)
        self.dep_label = QLabel("")
        dep_layout.addWidget(self.dep_label)
        layout.addLayout(dep_layout)
        self._setup_sections()
        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self.name_edit.currentTextChanged.connect(self._update_ok_button_state)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.update_preview()
    def _setup_sections(self):
        # Remove old
        for s in self.sections.values():
            s.setParent(None)
        self.sections.clear()
        t = self.type_combo.currentText()
        if t == "msg":
            self.sections["fields"] = FieldSection("Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["fields"])
        elif t == "srv":
            self.sections["request"] = FieldSection("Request Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["request"])
            self.sections["response"] = FieldSection("Response Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["response"])
        elif t == "action":
            self.sections["goal"] = FieldSection("Goal Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["goal"])
            self.sections["result"] = FieldSection("Result Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["result"])
            self.sections["feedback"] = FieldSection("Feedback Fields", self.sections_widget)
            self.sections_layout.addWidget(self.sections["feedback"])
        self.update_preview()
    def _on_type_changed(self, _):
        self._setup_sections()
    def _update_ok_button_state(self, text: str):
        self.ok_button.setEnabled(bool(text.strip()))
    def _select_dependencies(self):
        dlg = SelectRosPackageDependencyDialog(self.selected_deps, self)
        if dlg.exec():
            self.selected_deps = dlg.get_selected_dependencies()
            self.dep_label.setText(", ".join(self.selected_deps))
    def update_preview(self):
        iface_type = self.type_combo.currentText()
        content_lines = []
        deps: Set[str] = set(self.selected_deps)
        def extract_dep(type_str):
            # Extract package from type string like 'geometry_msgs/msg/Pose' or 'std_msgs/String'
            if '/' in type_str:
                return type_str.split('/')[0]
            return None
        if iface_type == "msg" and "fields" in self.sections:
            for t, n, arr, arr_len, arr_max, is_const, const_val in self.sections["fields"].get_fields():
                line = ""
                if is_const:
                    line = f"{t} {n.upper()}={const_val}"
                else:
                    line = f"{t} {n}"
                    if arr:
                        if arr_len:
                            line += f"[{arr_len}]"
                        elif arr_max:
                            line += f"[<=%d]" % arr_max
                        else:
                            line += "[]"
                content_lines.append(line)
                dep = extract_dep(t)
                if dep:
                    deps.add(dep)
        elif iface_type == "srv" and "request" in self.sections and "response" in self.sections:
            for t, n, arr, arr_len, arr_max, is_const, const_val in self.sections["request"].get_fields():
                line = ""
                if is_const:
                    line = f"{t} {n.upper()}={const_val}"
                else:
                    line = f"{t} {n}"
                    if arr:
                        if arr_len:
                            line += f"[{arr_len}]"
                        elif arr_max:
                            line += f"[<=%d]" % arr_max
                        else:
                            line += "[]"
                content_lines.append(line)
                dep = extract_dep(t)
                if dep:
                    deps.add(dep)
            content_lines.append("---")
            for t, n, arr, arr_len, arr_max, is_const, const_val in self.sections["response"].get_fields():
                line = ""
                if is_const:
                    line = f"{t} {n.upper()}={const_val}"
                else:
                    line = f"{t} {n}"
                    if arr:
                        if arr_len:
                            line += f"[{arr_len}]"
                        elif arr_max:
                            line += f"[<=%d]" % arr_max
                        else:
                            line += "[]"
                content_lines.append(line)
                dep = extract_dep(t)
                if dep:
                    deps.add(dep)
        elif iface_type == "action" and all(k in self.sections for k in ("goal", "result", "feedback")):
            for sec in ["goal", "result", "feedback"]:
                for t, n, arr, arr_len, arr_max, is_const, const_val in self.sections[sec].get_fields():
                    line = ""
                    if is_const:
                        line = f"{t} {n.upper()}={const_val}"
                    else:
                        line = f"{t} {n}"
                        if arr:
                            if arr_len:
                                line += f"[{arr_len}]"
                            elif arr_max:
                                line += f"[<=%d]" % arr_max
                            else:
                                line += "[]"
                    content_lines.append(line)
                    dep = extract_dep(t)
                    if dep:
                        deps.add(dep)
                if sec != "feedback":
                    content_lines.append("---")
        self.preview_edit.setPlainText("\n".join(content_lines))
        # Auto-update dependencies label
        self.selected_deps = sorted(deps)
        self.dep_label.setText(", ".join(self.selected_deps))
    def get_data(self) -> Optional[InterfaceFileDefinition]:
        if self.result() != QDialog.DialogCode.Accepted:
            return None
        base_name = self.name_edit.currentText().strip()
        iface_type = self.type_combo.currentText()
        if not base_name:
            return None
        file_name_with_ext = f"{base_name}.{iface_type}"
        # Generate content
        content = self.preview_edit.toPlainText().strip()
        # Collect dependencies
        deps: Set[str] = set(self.selected_deps)
        for line in content.splitlines():
            if "/" in line:
                deps.add(line.split("/")[0].split()[0])
        return InterfaceFileDefinition(
            file_name=file_name_with_ext,
            interface_type=iface_type,
            content=content,
            interface_package_dependencies=sorted(deps)
        )

# Standalone test for the dialog
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = MsgSrvActionEditorDialog()
    if dialog.exec():
        data = dialog.get_data()
        if data:
            print("Interface Data Accepted:")
            print(f"  File Name: {data.file_name}")
            print(f"  Type: {data.interface_type}")
            print(f"  Relative Path: {data.relative_path}")
            print(f"  Content:\n{data.content}")
            print(f"  Dependencies: {data.interface_package_dependencies}")
    else:
        print("Interface Creation Cancelled.")
