import pytest
from PyQt6.QtWidgets import QApplication
from rosbuddy.ui.main_window import MainWindow
from rosbuddy.core_logic import WorkspaceManager, ToolInvoker

@pytest.fixture(scope="module")
def app():
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    yield app

@pytest.fixture
def main_window(app):
    ws_manager = WorkspaceManager()
    tool_invoker = ToolInvoker(ws_manager)
    win = MainWindow(workspace_manager=ws_manager, tool_invoker=tool_invoker)
    yield win
    win.close()

def test_main_window_starts_and_shows(app, main_window):
    main_window.show()
    assert main_window.isVisible()
    assert main_window.windowTitle().startswith("ROSBuddy")

def test_activity_bar_exists(main_window):
    assert hasattr(main_window, 'sidebar_tool_bar')
    assert main_window.sidebar_tool_bar is not None

def test_tab_widget_exists(main_window):
    assert hasattr(main_window, 'active_view_tabs')
    assert main_window.active_view_tabs is not None

def test_status_bar_exists(main_window):
    assert hasattr(main_window, 'status_bar')
    assert main_window.status_bar is not None
