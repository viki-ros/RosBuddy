# run_rosbuddy_prototype.py (at the root of rosbuddy_project_generated/)
import sys
import pathlib

# Add the project directory to Python's path so it can find the 'rosbuddy' package
project_root = pathlib.Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rosbuddy.main_app import main as run_rosbuddy_gui

if __name__ == '__main__':
    print("Starting ROSBuddy GUI...")
    run_rosbuddy_gui()