"""
Configuration settings for the Stream Bill Generator
This module manages application settings and branding information.
"""
from typing import Any, Dict

# Default settings
DEFAULT_SETTINGS = {
    "app": {
        "name": "Stream Bill Generator",
        "version": "1.0.0",
        "description": "A comprehensive solution for generating contractor bills, deviation statements, and related documents from Excel data."
    },
    "branding": {
        "primary_color": "#005b9f",
        "secondary_color": "#fdb813",
        "accent_color": "#0ea5e9",
        "font_family": "Inter, sans-serif",
        "logo_path": "static/logo.png"
    },
    "pdf": {
        "default_margin_top": "15mm",
        "default_margin_bottom": "15mm",
        "default_margin_left": "10mm",
        "default_margin_right": "10mm",
        "page_size": "A4"
    },
    "paths": {
        "template_dir": "templates",
        "temp_dir": "temp",
        "output_dir": "output"
    },
    "performance": {
        "cache_ttl": 3600,
        "max_cache_size": 1024
    }
}

class SettingsManager:
    """Manages application settings"""
    
    def __init__(self, config_file: str = "config/settings.json"):
        """
        Initialize the SettingsManager
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.settings = DEFAULT_SETTINGS.copy()
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from configuration file"""
        # In a real implementation, this would load from a JSON file
        # For now, we'll just use the default settings
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation
        
        Args:
            key (str): Setting key (e.g., "branding.primary_color")
            default (Any): Default value if key not found
            
        Returns:
            Any: Setting value
        """
        keys = key.split('.')
        current = self.settings
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value using dot notation
        
        Args:
            key (str): Setting key (e.g., "branding.primary_color")
            value (Any): Value to set
        """
        keys = key.split('.')
        current = self.settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value

# Global settings manager instance
_settings_manager = SettingsManager()

def get_settings() -> SettingsManager:
    """Get the global settings manager instance"""
    return _settings_manager

def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a setting value
    
    Args:
        key (str): Setting key
        default (Any): Default value
        
    Returns:
        Any: Setting value
    """
    return get_settings().get(key, default)

def set_setting(key: str, value: Any) -> None:
    """
    Set a setting value
    
    Args:
        key (str): Setting key
        value (Any): Value to set
    """
    get_settings().set(key, value)

# Branding utilities
def get_branding_colors() -> Dict[str, str]:
    """Get branding colors"""
    return {
        "primary": get_setting("branding.primary_color", "#005b9f"),
        "secondary": get_setting("branding.secondary_color", "#fdb813"),
        "accent": get_setting("branding.accent_color", "#0ea5e9")
    }

def get_branding_font() -> str:
    """Get branding font family"""
    return get_setting("branding.font_family", "Inter, sans-serif")

def get_logo_path() -> str:
    """Get logo path"""
    return get_setting("branding.logo_path", "static/logo.png")

# PDF settings
def get_pdf_margins() -> Dict[str, str]:
    """Get default PDF margins"""
    return {
        "top": get_setting("pdf.default_margin_top", "15mm"),
        "bottom": get_setting("pdf.default_margin_bottom", "15mm"),
        "left": get_setting("pdf.default_margin_left", "10mm"),
        "right": get_setting("pdf.default_margin_right", "10mm")
    }

def get_pdf_page_size() -> str:
    """Get PDF page size"""
    return get_setting("pdf.page_size", "A4")

if __name__ == "__main__":
    # Example usage
    print("App Name:", get_setting("app.name"))
    print("Primary Color:", get_setting("branding.primary_color"))
    print("PDF Margins:", get_pdf_margins())
    
    # Test setting a value
    set_setting("app.version", "1.1.0")
    print("Updated Version:", get_setting("app.version"))