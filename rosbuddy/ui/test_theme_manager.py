import pytest
from PyQt6.QtWidgets import QApplication
from rosbuddy.ui.theme_manager import ThemeManager

def test_theme_manager_applies_palette(qtbot):
    app = QApplication.instance() or QApplication([])
    ThemeManager.apply_theme(app)
    palette = app.palette()
    # Check a few palette roles for expected color values
    assert palette.color(palette.ColorRole.Window).name() == '#23272e'
    assert palette.color(palette.ColorRole.Button).name() == '#0078d4'
    assert palette.color(palette.ColorRole.ButtonText).name() == '#ffffff'
