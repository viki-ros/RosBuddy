# run_rosbuddy_prototype.py (at the root of rosbuddy_project_generated/)
import sys
import pathlib
import argparse
import json
import logging

# Add the project directory to Python's path so it can find the 'rosbuddy' package
project_root = pathlib.Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rosbuddy.main_app import main as run_rosbuddy_gui

SETTINGS_PATH = pathlib.Path.home() / ".rosbuddy_settings.json"

def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save settings: {e}")

def main() -> None:
    """Entry point for launching the ROSBuddy GUI application."""
    parser = argparse.ArgumentParser(description="ROSBuddy GUI Launcher")
    parser.add_argument('--workspace', type=str, help='Path to workspace to open on startup')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no GUI)')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    if args.headless:
        logging.info("Headless mode is not yet implemented. Exiting.")
        sys.exit(0)

    if args.debug:
        logging.debug("Debug mode enabled.")

    logging.info("Starting ROSBuddy GUI...")
    settings = load_settings()
    # Placeholder: In the future, pass window geometry/splitter state to the GUI
    window_geometry = settings.get('window_geometry')
    splitter_state = settings.get('splitter_state')
    # Determine workspace to open: CLI > settings > None
    workspace_to_open = args.workspace or settings.get('last_workspace')
    try:
        # Pass window_geometry and splitter_state to run_rosbuddy_gui and get updated state on exit
        ui_state = run_rosbuddy_gui(workspace_path=workspace_to_open, window_geometry=window_geometry, splitter_state=splitter_state)
        if ui_state:
            settings['window_geometry'] = ui_state.get('window_geometry')
            settings['splitter_state'] = ui_state.get('splitter_state')
    except Exception as e:
        logging.error(f"Failed to start ROSBuddy GUI: {e}")
        import traceback
        traceback.print_exc()
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "ROSBuddy Startup Error", f"Failed to start ROSBuddy GUI:\n{e}")
        except Exception as dialog_exc:
            logging.error(f"Additionally failed to show error dialog: {dialog_exc}")
    # Save last workspace and UI state on exit
    if workspace_to_open:
        settings['last_workspace'] = workspace_to_open
    save_settings(settings)

if __name__ == '__main__':
    main()