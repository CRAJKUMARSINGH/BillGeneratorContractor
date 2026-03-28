"""
Internationalization (i18n) support for the Stream Bill Generator
This module provides localization support for multiple languages.
"""
import os

import yaml


class I18nManager:
    """Internationalization manager for handling multiple languages"""
    
    def __init__(self, locale_dir: str = "i18n"):
        """
        Initialize the I18nManager
        
        Args:
            locale_dir (str): Directory containing locale files
        """
        self.locale_dir = locale_dir
        self.current_locale = "en"
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translations from YAML files"""
        if not os.path.exists(self.locale_dir):
            print(f"Locale directory {self.locale_dir} not found")
            return
        
        # Load English translations
        en_file = os.path.join(self.locale_dir, "en.yml")
        if os.path.exists(en_file):
            with open(en_file, 'r', encoding='utf-8') as f:
                self.translations["en"] = yaml.safe_load(f) or {}
        
        # Load Hindi translations
        hi_file = os.path.join(self.locale_dir, "hi.yml")
        if os.path.exists(hi_file):
            with open(hi_file, 'r', encoding='utf-8') as f:
                self.translations["hi"] = yaml.safe_load(f) or {}
    
    def set_locale(self, locale: str) -> None:
        """
        Set the current locale
        
        Args:
            locale (str): Locale code (e.g., "en", "hi")
        """
        if locale in self.translations:
            self.current_locale = locale
        else:
            print(f"Warning: Locale {locale} not found, using default")
    
    def get_locale(self) -> str:
        """Get the current locale"""
        return self.current_locale
    
    def t(self, key: str, **kwargs) -> str:
        """
        Get translated string for the current locale
        
        Args:
            key (str): Translation key (e.g., "bill.title")
            **kwargs: Format arguments
            
        Returns:
            str: Translated string
        """
        # Navigate to the translation key
        keys = key.split('.')
        current = self.translations.get(self.current_locale, {})
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                # Fallback to English if translation not found
                current = self.translations.get("en", {}).get(k, key)
                break
        
        # Format with kwargs if provided
        if kwargs and isinstance(current, str):
            try:
                current = current.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return unformatted string if formatting fails
        
        return str(current)

# Global I18n manager instance
_i18n_manager = I18nManager()

def get_i18n() -> I18nManager:
    """Get the global I18n manager instance"""
    return _i18n_manager

def t(key: str, **kwargs) -> str:
    """
    Get translated string for the current locale
    
    Args:
        key (str): Translation key
        **kwargs: Format arguments
        
    Returns:
        str: Translated string
    """
    return get_i18n().t(key, **kwargs)

def set_locale(locale: str) -> None:
    """
    Set the current locale
    
    Args:
        locale (str): Locale code
    """
    get_i18n().set_locale(locale)

# Create locale directory and sample files if they don't exist
def create_sample_locales() -> None:
    """Create sample locale files for English and Hindi"""
    locale_dir = "i18n"
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)
    
    # English translations
    en_translations = {
        "bill": {
            "title": "Infrastructure Bill",
            "amount": "Total Amount",
            "date": "Date of Issue",
            "footer": "Generated using Stream-Bill Generator"
        },
        "ui": {
            "upload": "Upload Excel File",
            "premium": "Tender Premium %",
            "generate": "Generate Bill",
            "download": "Download Output"
        }
    }
    
    # Hindi translations
    hi_translations = {
        "bill": {
            "title": "अवसंरचना बिल",
            "amount": "कुल राशि",
            "date": "जारी करने की तिथि",
            "footer": "स्ट्रीम-बिल जेनरेटर द्वारा उत्पन्न"
        },
        "ui": {
            "upload": "एक्सेल फ़ाइल अपलोड करें",
            "premium": "टेंडर प्रीमियम %",
            "generate": "बिल जेनरेट करें",
            "download": "आउटपुट डाउनलोड करें"
        }
    }
    
    # Write files
    with open(os.path.join(locale_dir, "en.yml"), "w", encoding="utf-8") as f:
        yaml.dump(en_translations, f, allow_unicode=True, default_flow_style=False)
    
    with open(os.path.join(locale_dir, "hi.yml"), "w", encoding="utf-8") as f:
        yaml.dump(hi_translations, f, allow_unicode=True, default_flow_style=False)

if __name__ == "__main__":
    # Example usage
    print("Creating sample locale files...")
    create_sample_locales()
    
    # Test translations
    print("English:", t("bill.title"))
    print("Hindi:", t("bill.title"))
    
    set_locale("hi")
    print("Hindi (switched):", t("bill.title"))