# /home/viki/rosbuddy_app/RosBuddy/rosbuddy/ui/views/code_editor_view.py
import pathlib
import logging
from typing import Optional # Added Optional for type hinting
from PyQt6.QtWidgets import ( QStyle, # Added QStyle
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from .base_view import BaseView

logger = logging.getLogger(__name__)

class CodeEditorView(BaseView):
    """
    A view for editing text files, primarily code.
    """
    document_saved = pyqtSignal(str) # Emits file path on successful save
    dirty_state_changed = pyqtSignal(bool, str) # Emits is_dirty, file_path

    def __init__(self, file_path: Optional[pathlib.Path] = None, parent=None):
        super().__init__(view_title="Code Editor", parent=parent)
        self.setObjectName("codeEditorView")
        self._file_path: Optional[pathlib.Path] = None
        self._is_dirty: bool = False

        self._init_ui()

        if file_path:
            self.load_file(file_path)

    def _init_ui(self):
        # Get the layout set by BaseView.
        # CodeEditorView will clear BaseView's content and populate this layout.
        main_view_layout = self.layout()
        if not main_view_layout:
            # This should not happen if BaseView's __init__ always sets a layout.
            # As a fallback, create one if BaseView didn't.
            main_view_layout = QVBoxLayout(self)
        else:
            # Clear any widgets previously added by BaseView (e.g., placeholder_label)
            while main_view_layout.count():
                item = main_view_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                # Note: If BaseView could add sub-layouts, they'd need recursive clearing.
                # For now, BaseView only adds a single QLabel.

        main_view_layout.setContentsMargins(5, 5, 5, 5) # Tighter margins for editor
        main_view_layout.setSpacing(5)
        # --- Header (File Path & Save Button) ---
        header_layout = QHBoxLayout()
        self.file_path_label = QLabel("Untitled")
        self.file_path_label.setObjectName("editorFilePathLabel")
        self.file_path_label.setStyleSheet("font-style: italic; color: #aaa;")
        header_layout.addWidget(self.file_path_label, 1) # Stretch

        # AI Action Buttons (as QToolButton for icons)
        self.ai_explain_button = QToolButton(self)
        self.ai_explain_button.setText("📄➡️🧠") # Placeholder, use QIcon
        self.ai_explain_button.setToolTip("AI: Explain Code")
        self.ai_explain_button.clicked.connect(self.on_ai_explain)
        header_layout.addWidget(self.ai_explain_button)

        self.ai_optimize_button = QToolButton(self)
        self.ai_optimize_button.setText("⚡")
        self.ai_optimize_button.setToolTip("AI: Optimize Code")
        self.ai_optimize_button.clicked.connect(self.on_ai_optimize)
        header_layout.addWidget(self.ai_optimize_button)

        self.ai_docstring_button = QToolButton(self)
        self.ai_docstring_button.setText("✍️")
        self.ai_docstring_button.setToolTip("AI: Generate Docstring")
        self.ai_docstring_button.clicked.connect(self.on_ai_docstring)
        header_layout.addWidget(self.ai_docstring_button)

        self.save_button = QPushButton("Save")
        self.save_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setEnabled(False) # Disabled until dirty
        header_layout.addWidget(self.save_button)
        main_view_layout.addLayout(header_layout)

        # --- Code Area ---
        self.code_area = QTextEdit()
        self.code_area.setObjectName("codeEditorArea")
        # Use a monospace font
        font = QFont("Fira Mono", 11) # Or Consolas, Monaco, etc.
        if not font.exactMatch(): # Fallback if Fira Mono (or the initially requested font) was not exactly matched
            font.setFamily("Monospace")
        self.code_area.setFont(font)
        self.code_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) # Common for code
        self.code_area.cursorPositionChanged.connect(self._update_status_label)
        self.code_area.textChanged.connect(self._on_text_changed)
        main_view_layout.addWidget(self.code_area, 1) # Stretch
        # No self.setLayout() here, as we are modifying the layout already set by BaseView.

        # Footer (mock)
        footer_layout = QHBoxLayout()
        self.status_label = QLabel("Ln 1, Col 1 | Python (mock)")
        self.status_label.setStyleSheet("font-size: 10pt; color: #999;")
        footer_layout.addWidget(self.status_label)
        main_view_layout.addLayout(footer_layout)

    def get_file_path(self) -> Optional[pathlib.Path]:
        return self._file_path

    def is_dirty(self) -> bool:
        return self._is_dirty

    def _set_dirty(self, dirty: bool):
        if self._is_dirty == dirty:
            return
        self._is_dirty = dirty
        self.save_button.setEnabled(dirty)
        
        title_prefix = "*" if dirty else ""
        base_title = self._file_path.name if self._file_path else "Untitled"
        
        # Update the tab title (this needs to be done by MainWindow)
        self.dirty_state_changed.emit(dirty, str(self._file_path) if self._file_path else "Untitled")
        
        # Update internal view title (if BaseView uses it)
        super().set_view_title(f"{title_prefix}{base_title}")
        
        # Also update the file path label in this view
        self.file_path_label.setText(f"{title_prefix}{str(self._file_path) if self._file_path else 'Untitled'}")


    def _on_text_changed(self):
        if not self.is_dirty(): # Only set dirty if it wasn't already (e.g. during load)
            self._set_dirty(True)
        # self._update_status_label() # Cursor position change handles this better for Ln/Col

    def _update_status_label(self):
        cursor = self.code_area.textCursor()
        self.status_label.setText(f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1} | Python (mock)")

    def load_file(self, file_path: pathlib.Path) -> bool:
        self._file_path = file_path.resolve()
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            was_dirty = self._is_dirty # Preserve dirty state before setText
            self.code_area.setPlainText(content)
            self._set_dirty(was_dirty) # Restore or clear dirty state
            
            self.file_path_label.setText(str(self._file_path))
            super().set_view_title(self._file_path.name) # Update BaseView title
            self._update_status_label() # Update for new content
            logger.info(f"File loaded into editor: {self._file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading file '{self._file_path}': {e}", exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Could not load file: {self._file_path}\n\n{e}")
            self.file_path_label.setText(f"Error loading: {self._file_path.name}")
            self._file_path = None # Invalidate path on error
            return False

    def save_file(self) -> bool:
        if not self._file_path:
            # Implement "Save As" logic if needed, or just disallow saving untitled
            QMessageBox.warning(self, "Save Error", "No file path specified. Cannot save.")
            return False
        if not self.is_dirty():
            logger.info(f"File '{self._file_path}' not dirty. Save skipped.")
            return True # Nothing to save, considered success

        try:
            content = self.code_area.toPlainText()
            with open(self._file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._set_dirty(False)
            logger.info(f"File saved: {self._file_path}")
            self.document_saved.emit(str(self._file_path))
            QMessageBox.information(self, "File Saved", f"File '{self._file_path.name}' saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving file '{self._file_path}': {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Could not save file: {self._file_path}\n\n{e}")
            return False

    def get_content(self) -> str:
        return self.code_area.toPlainText()

    def close_view(self) -> bool:
        """
        Called when the tab containing this view is about to be closed.
        Checks for unsaved changes.
        Returns True if safe to close, False otherwise.
        """
        if self.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"File '{self._file_path.name if self._file_path else 'Untitled'}' has unsaved changes.\n"
                "Do you want to save them before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_file():
                    return False # Save failed, don't close
            elif reply == QMessageBox.StandardButton.Cancel:
                return False # User cancelled closing
            # If Discard, proceed to close
        return True

    # --- AI Action Placeholders ---
    def on_ai_explain(self):
        QMessageBox.information(self, "AI Action", "Explain code feature coming soon!")
        logger.info("AI Explain action triggered.")

    def on_ai_optimize(self):
        QMessageBox.information(self, "AI Action", "Optimize code feature coming soon!")
        logger.info("AI Optimize action triggered.")

    def on_ai_docstring(self):
        QMessageBox.information(self, "AI Action", "Generate docstring feature coming soon!")
        logger.info("AI Docstring action triggered.")

if __name__ == '__main__':
    import sys

    # Adjust sys.path to allow running this module directly for testing
    # This assumes the script is in rosbuddy_app/RosBuddy/rosbuddy/ui/views/
    # We need to add rosbuddy_app/RosBuddy to sys.path
    project_root_for_views = pathlib.Path(__file__).resolve().parent.parent.parent
    if str(project_root_for_views) not in sys.path:
        sys.path.insert(0, str(project_root_for_views))

    # Now the relative import should work, or we can re-import if needed.
    # For this test, we'll rely on the path adjustment.
    # If you were to re-import, it would be:
    # from rosbuddy.ui.views.base_view import BaseView

    app = QApplication(sys.argv)

    # Test with a dummy file
    dummy_file_path = pathlib.Path("dummy_test_file.py")
    with open(dummy_file_path, "w", encoding='utf-8') as f:
        f.write("print('Hello from CodeEditorView test!')\n\n# This is a test file.\n# Edit me!")

    editor = CodeEditorView(file_path=dummy_file_path)
    editor.setWindowTitle("Code Editor View - Standalone Test")
    editor.setGeometry(100, 100, 800, 600)
    editor.show()

    exit_code = app.exec()
    dummy_file_path.unlink() # Clean up dummy file
    sys.exit(exit_code)
