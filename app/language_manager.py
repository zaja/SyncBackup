"""
Language Manager for SyncBackup

Handles loading and managing language files for internationalization (i18n)

Author: Goran Zajec
Website: https://svejedobro.hr
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class LanguageManager:
    """Manages language files and translations"""
    
    def __init__(self, languages_dir: str = None):
        """Initialize language manager
        
        Args:
            languages_dir: Path to languages directory. If None, uses default.
        """
        if languages_dir is None:
            # Default to app/languages directory
            base_dir = Path(__file__).parent
            self.languages_dir = base_dir / "languages"
        else:
            self.languages_dir = Path(languages_dir)
        
        self.current_language = "en"
        self.translations = {}
        self.available_languages = {}
        
        # Scan for available languages
        self.scan_languages()
        
        # Load default language
        self.load_language(self.current_language)
    
    def scan_languages(self):
        """Scan languages directory for available language files"""
        self.available_languages = {}
        
        if not self.languages_dir.exists():
            print(f"Warning: Languages directory not found: {self.languages_dir}")
            return
        
        # Find all .json files in languages directory
        for file_path in self.languages_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract language info
                    lang_code = data.get('language_code', file_path.stem)
                    lang_name = data.get('language_name', lang_code)
                    
                    self.available_languages[lang_code] = {
                        'name': lang_name,
                        'file': file_path
                    }
                    
                    print(f"Found language: {lang_name} ({lang_code})")
            except Exception as e:
                print(f"Error loading language file {file_path}: {e}")
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available languages
        
        Returns:
            Dict with language codes as keys and language names as values
        """
        return {code: info['name'] for code, info in self.available_languages.items()}
    
    def load_language(self, language_code: str) -> bool:
        """Load a specific language
        
        Args:
            language_code: Language code (e.g., 'en', 'hr')
            
        Returns:
            True if successful, False otherwise
        """
        if language_code not in self.available_languages:
            print(f"Warning: Language '{language_code}' not found. Using English.")
            language_code = 'en'
            
            if language_code not in self.available_languages:
                print("Error: No languages available!")
                return False
        
        try:
            lang_file = self.available_languages[language_code]['file']
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
                self.current_language = language_code
                print(f"Loaded language: {self.translations.get('language_name', language_code)}")
                return True
        except Exception as e:
            print(f"Error loading language '{language_code}': {e}")
            return False
    
    def get(self, key_path: str, default: str = None, **kwargs) -> str:
        """Get translation for a key path
        
        Args:
            key_path: Dot-separated path to translation key (e.g., 'buttons.save')
            default: Default value if key not found
            **kwargs: Format arguments for string formatting
            
        Returns:
            Translated string
        """
        # Split key path
        keys = key_path.split('.')
        
        # Navigate through nested dictionary
        value = self.translations
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                # Key not found, return default or key path
                return default if default is not None else key_path
        
        # Format string if kwargs provided
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing format key {e} for '{key_path}'")
                return value
        
        return value
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def get_language_name(self, language_code: str = None) -> str:
        """Get language name
        
        Args:
            language_code: Language code. If None, returns current language name.
            
        Returns:
            Language name
        """
        if language_code is None:
            language_code = self.current_language
        
        if language_code in self.available_languages:
            return self.available_languages[language_code]['name']
        
        return language_code

# Global instance
_language_manager = None

def get_language_manager() -> LanguageManager:
    """Get global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def set_language(language_code: str) -> bool:
    """Set current language
    
    Args:
        language_code: Language code to set
        
    Returns:
        True if successful
    """
    return get_language_manager().load_language(language_code)

def get_text(key_path: str, default: str = None, **kwargs) -> str:
    """Get translated text
    
    Args:
        key_path: Dot-separated path to translation key
        default: Default value if key not found
        **kwargs: Format arguments
        
    Returns:
        Translated string
    """
    return get_language_manager().get(key_path, default, **kwargs)

def get_available_languages() -> Dict[str, str]:
    """Get available languages
    
    Returns:
        Dict with language codes as keys and names as values
    """
    return get_language_manager().get_available_languages()
