from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit,
                               QToolBar, QPushButton, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat

import queue
import threading
import datetime

class OutputConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.log_queue = queue.Queue()
        self.start_log_consumer()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QToolBar()
        
        # Log level filter
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "Debug", "Info", "Warning", "Error"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        toolbar.addWidget(self.level_combo)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_output)
        toolbar.addWidget(clear_btn)
        
        # Save button
        save_btn = QPushButton("Save Logs")
        save_btn.clicked.connect(self.save_logs)
        toolbar.addWidget(save_btn)
        
        layout.addWidget(toolbar)

        # Output text area
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumBlockCount(10000)  # Limit for performance
        layout.addWidget(self.output_text)

        # Log colors
        self.log_colors = {
            "DEBUG": QColor("#808080"),    # Gray
            "INFO": QColor("#FFFFFF"),     # White
            "WARNING": QColor("#FFA500"),  # Orange
            "ERROR": QColor("#FF0000")     # Red
        }

    def start_log_consumer(self):
        """Start the log consumer thread."""
        def consume_logs():
            while True:
                try:
                    log_entry = self.log_queue.get()
                    if log_entry is None:  # Poison pill
                        break
                    self.append_log(log_entry)
                except queue.Empty:
                    continue

        self.consumer_thread = threading.Thread(target=consume_logs, daemon=True)
        self.consumer_thread.start()

    def append_log(self, log_entry):
        """Append a log entry to the console."""
        level = log_entry.get("level", "INFO")
        message = log_entry.get("message", "")
        timestamp = log_entry.get("timestamp", datetime.datetime.now())
        
        # Create formatted log line
        log_line = f"[{timestamp.strftime('%H:%M:%S')}] [{level}] {message}"
        
        # Set text color based on log level
        format = QTextCharFormat()
        format.setForeground(self.log_colors.get(level, QColor("#FFFFFF")))
        
        # Add text with formatting
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(log_line + "\n", format)
        
        # Auto-scroll to bottom
        self.output_text.setTextCursor(cursor)

    def log(self, message, level="INFO"):
        """Add a log message to the queue."""
        log_entry = {
            "message": message,
            "level": level.upper(),
            "timestamp": datetime.datetime.now()
        }
        self.log_queue.put(log_entry)

    def debug(self, message):
        """Log a debug message."""
        self.log(message, "DEBUG")

    def info(self, message):
        """Log an info message."""
        self.log(message, "INFO")

    def warning(self, message):
        """Log a warning message."""
        self.log(message, "WARNING")

    def error(self, message):
        """Log an error message."""
        self.log(message, "ERROR")

    def clear_output(self):
        """Clear the console output."""
        self.output_text.clear()

    def filter_logs(self, level):
        """Filter logs by level."""
        # This would require storing logs and re-displaying them
        # For now, just clear and start fresh
        self.clear_output()
        self.info(f"Log level filter set to: {level}")

    def save_logs(self):
        """Save logs to a file."""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            "",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.output_text.toPlainText())
                self.info(f"Logs saved to: {filename}")
            except Exception as e:
                self.error(f"Failed to save logs: {e}")

    def closeEvent(self, event):
        """Clean up on close."""
        self.log_queue.put(None)  # Send poison pill
        self.consumer_thread.join()
        super().closeEvent(event) 