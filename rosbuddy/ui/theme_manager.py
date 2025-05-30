from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

class ThemeManager:
    @staticmethod
    def apply_theme(app: QApplication):
        """Apply the modern dark theme to the application."""
        # Load and apply the stylesheet
        theme_file = Path(__file__).parent / "resources" / "themes" / "modern_dark.qss"
        try:
            with open(theme_file, "r") as f:
                app.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Theme file not found at {theme_file}")
            return

        # Set the application palette for consistent coloring
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#2d2d2d"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252526"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#252526"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#0078d4"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#0078d4"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d4"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

        app.setPalette(palette) 