# /home/viki/rosbuddy_app/RosBuddy/rosbuddy/ui/views/code_editor_view.py
import pathlib
import logging
from typing import Optional # Added Optional for type hinting
from PyQt6.QtWidgets import ( QStyle, # Added QStyle
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QPalette, QColor, QSyntaxHighlighter, QTextCharFormat, QTextDocument, QPainter

from .base_view import BaseView

logger = logging.getLogger(__name__)

class LineNumberArea(QWidget):
    """Line number area widget for the code editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
        
    def sizeHint(self):
        return self.code_editor.line_number_area_width()
        
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Define formats
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue for keywords
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del",
            "elif", "else", "except", "finally", "for", "from", "global", "if",
            "import", "in", "is", "lambda", "not", "or", "pass", "raise",
            "return", "try", "while", "with", "yield", "async", "await", "nonlocal"
        ]
        
        for keyword in keywords:
            self.highlighting_rules.append((f"\\b{keyword}\\b", keyword_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append(('""".*?"""', string_format))
        self.highlighting_rules.append(("'''.*?'''", string_format))
        self.highlighting_rules.append('"[^"\\\\]*(\\\\.[^"\\\\]*)*"', string_format)
        self.highlighting_rules.append("'[^'\\\\]*(\\\\.[^'\\\\]*)*'", string_format)
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append(("#[^\r\n]*", comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green for numbers
        self.highlighting_rules.append(("\\b[0-9]+\\.?[0-9]*\\b", number_format))
        
        # Function definitions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))  # Yellow for functions
        function_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(("\\bdef\\s+([a-zA-Z_][a-zA-Z0-9_]*)", function_format))
        
        # Class definitions
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4EC9B0"))  # Teal for classes
        class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(("\\bclass\\s+([a-zA-Z_][a-zA-Z0-9_]*)", class_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CppSyntaxHighlighter(QSyntaxHighlighter):
    """C++ syntax highlighter."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Define formats
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue for keywords
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
            "bool", "break", "case", "catch", "char", "char16_t", "char32_t",
            "class", "compl", "const", "constexpr", "const_cast", "continue",
            "decltype", "default", "delete", "do", "double", "dynamic_cast",
            "else", "enum", "explicit", "export", "extern", "false", "float",
            "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
            "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
            "or", "or_eq", "private", "protected", "public", "register",
            "reinterpret_cast", "return", "short", "signed", "sizeof", "static",
            "static_assert", "static_cast", "struct", "switch", "template",
            "this", "thread_local", "throw", "true", "try", "typedef", "typeid",
            "typename", "union", "unsigned", "using", "virtual", "void",
            "volatile", "wchar_t", "while", "xor", "xor_eq", "override", "final"
        ]
        
        for keyword in keywords:
            self.highlighting_rules.append((f"\\b{keyword}\\b", keyword_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append('"[^"\\\\]*(\\\\.[^"\\\\]*)*"', string_format)
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append(("//[^\r\n]*", comment_format))
        self.highlighting_rules.append(("/\\*.*?\\*/", comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green for numbers
        self.highlighting_rules.append(("\\b[0-9]+\\.?[0-9]*[fFlL]?\\b", number_format))
        
        # Preprocessor directives
        preprocessor_format = QTextCharFormat()
        preprocessor_format.setForeground(QColor("#C586C0"))  # Purple for preprocessor
        self.highlighting_rules.append(("^\\s*#[^\r\n]*", preprocessor_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class XmlSyntaxHighlighter(QSyntaxHighlighter):
    """XML/YAML syntax highlighter."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # XML tags
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569CD6"))  # Blue for tags
        tag_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(("<[^>]+>", tag_format))
        
        # XML attributes
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#92C5F8"))  # Light blue for attributes
        self.highlighting_rules.append(("\\b[a-zA-Z_][a-zA-Z0-9_]*(?=\\s*=)", attr_format))
        
        # String values
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append('"[^"]*"', string_format)
        self.highlighting_rules.append("'[^']*'", string_format)
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append(("<!--.*?-->", comment_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CMakeSyntaxHighlighter(QSyntaxHighlighter):
    """CMake syntax highlighter for CMakeLists.txt files."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Define formats
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue for keywords
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # CMake commands
        cmake_commands = [
            "cmake_minimum_required", "project", "find_package", "add_executable",
            "add_library", "target_link_libraries", "target_include_directories",
            "target_compile_definitions", "install", "set", "option", "if", "else",
            "elseif", "endif", "foreach", "endforeach", "while", "endwhile",
            "function", "endfunction", "macro", "endmacro", "include", "add_subdirectory",
            "message", "list", "string", "file", "configure_file"
        ]
        
        for command in cmake_commands:
            self.highlighting_rules.append((f"\\b{command}\\b", keyword_format))
        
        # Variables
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("#4FC1FF"))  # Light blue for variables
        self.highlighting_rules.append((r"\$\{[^}]+\}", variable_format))
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append(('"[^"]*"', string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append((r"#[^\r\n]*", comment_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class YamlSyntaxHighlighter(QSyntaxHighlighter):
    """YAML syntax highlighter for configuration files."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Define formats
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9CDCFE"))  # Light blue for keys
        key_format.setFontWeight(QFont.Weight.Bold)
        
        # YAML keys (word: or word followed by colon)
        self.highlighting_rules.append((r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:", key_format))
        
        # String values
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append(('"[^"]*"', string_format))
        self.highlighting_rules.append("'[^']*'", string_format)
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green for numbers
        self.highlighting_rules.append((r"\b[0-9]+\.?[0-9]*\b", number_format))
        
        # Boolean values
        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor("#569CD6"))  # Blue for booleans
        bool_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"\b(true|false|True|False|yes|no|Yes|No)\b", bool_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append((r"#[^\r\n]*", comment_format))
        
        # Special YAML characters
        special_format = QTextCharFormat()
        special_format.setForeground(QColor("#D4D4D4"))  # Light gray
        self.highlighting_rules.append((r"[-|>]", special_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class LaunchSyntaxHighlighter(QSyntaxHighlighter):
    """Launch file syntax highlighter for ROS 2 launch files."""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # Define formats
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569CD6"))  # Blue for tags
        tag_format.setFontWeight(QFont.Weight.Bold)
        
        # ROS Launch specific tags
        launch_tags = [
            "launch", "node", "param", "remap", "include", "group", "test",
            "executable", "arg", "let", "set_env", "unset_env", "declare_parameter"
        ]
        
        for tag in launch_tags:
            self.highlighting_rules.append((f"</?{tag}\\b[^>]*>", tag_format))
        
        # Generic XML tags
        self.highlighting_rules.append((r"<[^>]+>", tag_format))
        
        # Attributes
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#92C5F8"))  # Light blue for attributes
        self.highlighting_rules.append((r"\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*=)", attr_format))
        
        # String values
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange for strings
        self.highlighting_rules.append(('"[^"]*"', string_format))
        self.highlighting_rules.append("'[^']*'", string_format)
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        self.highlighting_rules.append((r"<!--.*?-->", comment_format))
        
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CodeEditorTextEdit(QTextEdit):
    """Enhanced QTextEdit with line numbers and syntax highlighting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.syntax_highlighter = None
        
        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Set up line highlighting
        self.current_line_color = QColor("#2A2D30")
        
    def set_syntax_highlighting(self, file_path):
        """Set syntax highlighting based on file path and extension."""
        if self.syntax_highlighter:
            self.syntax_highlighter.setDocument(None)
            
        if isinstance(file_path, str):
            file_path = pathlib.Path(file_path)
            
        file_extension = file_path.suffix.lower()
        file_name = file_path.name.lower()
            
        if file_extension in ['.py', '.pyx']:
            self.syntax_highlighter = PythonSyntaxHighlighter(self.document())
        elif file_extension in ['.cpp', '.cc', '.cxx', '.hpp', '.h', '.hxx']:
            self.syntax_highlighter = CppSyntaxHighlighter(self.document())
        elif file_extension in ['.xml'] or file_name.endswith('.launch'):
            self.syntax_highlighter = XmlSyntaxHighlighter(self.document())
        elif file_extension in ['.yaml', '.yml']:
            self.syntax_highlighter = YamlSyntaxHighlighter(self.document())
        elif file_name == 'cmakelists.txt' or file_extension == '.cmake':
            self.syntax_highlighter = CMakeSyntaxHighlighter(self.document())
        elif file_name.endswith('.launch.py'):
            self.syntax_highlighter = LaunchSyntaxHighlighter(self.document())
        # Add more highlighters as needed
        
    def line_number_area_width(self):
        """Calculate the width needed for line numbers."""
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
        
    def update_line_number_area_width(self, new_block_count):
        """Update the line number area width."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self, rect, dy):
        """Update the line number area when scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        
    def line_number_area_paint_event(self, event):
        """Paint the line number area."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        painter.setPen(QColor("#858585"))
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(0, top, self.line_number_area.width() - 3, 
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
                               
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
            
    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)

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
        self.code_area = CodeEditorTextEdit()
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
        language = self._detect_language()
        self.status_label.setText(f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1} | {language}")
        
    def _detect_language(self):
        """Detect the language based on file extension."""
        if not self._file_path:
            return "Text"
            
        file_extension = self._file_path.suffix.lower()
        file_name = self._file_path.name.lower()
        
        if file_extension in ['.py', '.pyx']:
            return "Python"
        elif file_extension in ['.cpp', '.cc', '.cxx']:
            return "C++"
        elif file_extension in ['.hpp', '.h', '.hxx']:
            return "C++ Header"
        elif file_extension == '.xml' or file_name.endswith('.launch'):
            return "XML"
        elif file_extension in ['.yaml', '.yml']:
            return "YAML"
        elif file_name == 'cmakelists.txt' or file_extension == '.cmake':
            return "CMake"
        elif file_name.endswith('.launch.py'):
            return "Launch (Python)"
        else:
            return "Text"

    def load_file(self, file_path: pathlib.Path) -> bool:
        self._file_path = file_path.resolve()
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            was_dirty = self._is_dirty # Preserve dirty state before setText
            self.code_area.setPlainText(content)
            self._set_dirty(was_dirty) # Restore or clear dirty state
            
            # Set syntax highlighting based on file path
            self.code_area.set_syntax_highlighting(self._file_path)
            
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
    from PyQt6.QtWidgets import QApplication

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
