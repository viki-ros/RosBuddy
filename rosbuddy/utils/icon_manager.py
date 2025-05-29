from pathlib import Path
import logging
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QStyle

logger = logging.getLogger(__name__)

class IconManager:
    """Manages icon loading and fallback mechanisms for the application."""
    
    def __init__(self, style=None):
        self.style = style
        self.icon_path = Path(__file__).parent.parent / 'resources' / 'icons'
        self.icon_cache = {}

    def get_icon(self, name: str, fallback_standard: QStyle.StandardPixmap = None) -> QIcon:
        """
        Get an icon by name with fallback mechanisms.
        
        Args:
            name: The name of the icon to load
            fallback_standard: A QStyle.StandardPixmap to use if theme icon is not found
        
        Returns:
            QIcon: The loaded icon or a fallback icon
        """
        if name in self.icon_cache:
            return self.icon_cache[name]

        icon = QIcon.fromTheme(name)
        
        # If theme icon not found and we have a fallback
        if icon.isNull() and fallback_standard and self.style:
            icon = self.style.standardIcon(fallback_standard)
            
        # If still no icon, try to load from our resources
        if icon.isNull():
            resource_path = self.icon_path / f"{name}.png"
            if resource_path.exists():
                icon = QIcon(str(resource_path))
        
        self.icon_cache[name] = icon
        return icon

    def set_style(self, style):
        """Update the style reference, useful when style changes."""
        self.style = style
