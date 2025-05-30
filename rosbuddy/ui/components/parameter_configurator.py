from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QComboBox, QLabel,
                               QSpinBox, QDoubleSpinBox, QLineEdit)
from PyQt6.QtCore import pyqtSignal

class ParameterConfigurator(QWidget):
    parameter_updated = pyqtSignal(dict)  # Emits parameter updates

    PARAM_TYPES = [
        "String",
        "Integer",
        "Double",
        "Boolean",
        "Array",
        "Dictionary"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.parameters = {}

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Parameter table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Value", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Add parameter button
        add_btn = QPushButton("Add Parameter")
        add_btn.clicked.connect(self.add_parameter_row)
        layout.addWidget(add_btn)

    def add_parameter_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Parameter name
        name_edit = QLineEdit()
        self.table.setCellWidget(row, 0, name_edit)

        # Parameter type selector
        type_combo = QComboBox()
        type_combo.addItems(self.PARAM_TYPES)
        type_combo.currentTextChanged.connect(lambda text: self.update_value_widget(row, text))
        self.table.setCellWidget(row, 1, type_combo)

        # Initial value widget (string by default)
        value_edit = QLineEdit()
        self.table.setCellWidget(row, 2, value_edit)

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_parameter_row(row))
        actions_layout.addWidget(delete_btn)

        self.table.setCellWidget(row, 3, actions_widget)

    def update_value_widget(self, row, param_type):
        if param_type == "String":
            widget = QLineEdit()
        elif param_type == "Integer":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
        elif param_type == "Double":
            widget = QDoubleSpinBox()
            widget.setRange(-999999.99, 999999.99)
            widget.setDecimals(2)
        elif param_type == "Boolean":
            widget = QComboBox()
            widget.addItems(["True", "False"])
        elif param_type == "Array":
            widget = QLineEdit()
            widget.setPlaceholderText("Enter comma-separated values")
        elif param_type == "Dictionary":
            widget = QLineEdit()
            widget.setPlaceholderText("Enter key:value pairs (key1:value1, key2:value2)")

        self.table.setCellWidget(row, 2, widget)
        widget.editingFinished.connect(lambda: self.parameter_changed(row))

    def delete_parameter_row(self, row):
        self.table.removeRow(row)
        self.update_parameters()

    def parameter_changed(self, row):
        self.update_parameters()

    def update_parameters(self):
        parameters = {}
        for row in range(self.table.rowCount()):
            name = self.table.cellWidget(row, 0).text()
            param_type = self.table.cellWidget(row, 1).currentText()
            value_widget = self.table.cellWidget(row, 2)

            if not name:
                continue

            if param_type == "String":
                value = value_widget.text()
            elif param_type == "Integer":
                value = value_widget.value()
            elif param_type == "Double":
                value = value_widget.value()
            elif param_type == "Boolean":
                value = value_widget.currentText() == "True"
            elif param_type == "Array":
                try:
                    value = [v.strip() for v in value_widget.text().split(",")]
                except:
                    value = []
            elif param_type == "Dictionary":
                try:
                    pairs = [p.strip() for p in value_widget.text().split(",")]
                    value = {k.strip(): v.strip() for k, v in 
                            (p.split(":") for p in pairs if ":" in p)}
                except:
                    value = {}

            parameters[name] = {"type": param_type, "value": value}

        self.parameters = parameters
        self.parameter_updated.emit(parameters)

    def get_parameters(self):
        return self.parameters

    def load_parameters(self, parameters):
        self.table.setRowCount(0)
        for name, config in parameters.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_edit = QLineEdit(name)
            self.table.setCellWidget(row, 0, name_edit)
            
            # Type
            type_combo = QComboBox()
            type_combo.addItems(self.PARAM_TYPES)
            type_combo.setCurrentText(config["type"])
            self.table.setCellWidget(row, 1, type_combo)
            
            # Value
            self.update_value_widget(row, config["type"])
            value_widget = self.table.cellWidget(row, 2)
            
            if config["type"] == "String":
                value_widget.setText(str(config["value"]))
            elif config["type"] in ["Integer", "Double"]:
                value_widget.setValue(config["value"])
            elif config["type"] == "Boolean":
                value_widget.setCurrentText(str(config["value"]))
            elif config["type"] == "Array":
                value_widget.setText(",".join(map(str, config["value"])))
            elif config["type"] == "Dictionary":
                value_widget.setText(",".join(f"{k}:{v}" for k, v in config["value"].items()))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda row=row: self.delete_parameter_row(row))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 3, actions_widget) 