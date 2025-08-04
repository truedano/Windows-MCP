"""
Configuration management system for Windows Scheduler GUI.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import logging

from src.models.config import AppConfig
from src.utils.constants import CONFIG_DIR, CONFIG_FILE, BACKUP_DIR


class ConfigObserver(ABC):
    """Abstract base class for configuration change observers."""
    
    @abstractmethod
    def on_config_changed(self, setting_key: str, old_value: Any, new_value: Any) -> None:
        """
        Called when a configuration setting changes.
        
        Args:
            setting_key: The key of the setting that changed
            old_value: The previous value
            new_value: The new value
        """
        pass


@dataclass
class ConfigChangeEvent:
    """Configuration change event data."""
    setting_key: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    source: str = "user"


class ConfigStorage:
    """Handles configuration file storage and retrieval."""
    
    def __init__(self, config_dir: str = CONFIG_DIR, config_file: str = CONFIG_FILE):
        """
        Initialize configuration storage.
        
        Args:
            config_dir: Directory for configuration files
            config_file: Configuration file name
        """
        self.config_dir = Path(config_dir)
        self.config_file = config_file
        self.config_path = self.config_dir / config_file
        self.backup_dir = Path(BACKUP_DIR)
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _ensure_directories(self):
        """Ensure configuration and backup directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary or None if file doesn't exist
        """
        try:
            if not self.config_path.exists():
                self.logger.info(f"Configuration file {self.config_path} does not exist")
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return config_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            # Try to load backup
            return self._load_backup()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return None
    
    def save_config(self, config_data: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        Save configuration to file.
        
        Args:
            config_data: Configuration data to save
            create_backup: Whether to create a backup of existing config
            
        Returns:
            True if save was successful
        """
        try:
            # Create backup if requested and file exists
            if create_backup and self.config_path.exists():
                self._create_backup()
            
            # Write configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """
        Create a backup of the current configuration file.
        
        Returns:
            True if backup was successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            
            # Copy current config to backup
            import shutil
            shutil.copy2(self.config_path, backup_path)
            
            self.logger.info(f"Configuration backup created: {backup_path}")
            
            # Clean old backups (keep last 10)
            self._clean_old_backups()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating configuration backup: {e}")
            return False
    
    def _load_backup(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent backup configuration.
        
        Returns:
            Backup configuration data or None
        """
        try:
            backup_files = list(self.backup_dir.glob("config_backup_*.json"))
            if not backup_files:
                return None
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info(f"Configuration loaded from backup: {latest_backup}")
            return config_data
            
        except Exception as e:
            self.logger.error(f"Error loading backup configuration: {e}")
            return None
    
    def _clean_old_backups(self, max_backups: int = 10):
        """
        Clean old backup files, keeping only the most recent ones.
        
        Args:
            max_backups: Maximum number of backups to keep
        """
        try:
            backup_files = list(self.backup_dir.glob("config_backup_*.json"))
            if len(backup_files) <= max_backups:
                return
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                self.logger.info(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning old backups: {e}")
    
    def get_backup_list(self) -> List[Path]:
        """
        Get list of available backup files.
        
        Returns:
            List of backup file paths, sorted by date (newest first)
        """
        backup_files = list(self.backup_dir.glob("config_backup_*.json"))
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backup_files
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore was successful
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Create backup of current config before restore
            if self.config_path.exists():
                self._create_backup()
            
            # Copy backup to config location
            import shutil
            shutil.copy2(backup_path, self.config_path)
            
            self.logger.info(f"Configuration restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return False


class ConfigurationManager:
    """
    Central configuration management system.
    
    Provides configuration loading, saving, validation, and change notification.
    """
    
    def __init__(self, storage: Optional[ConfigStorage] = None):
        """
        Initialize configuration manager.
        
        Args:
            storage: Configuration storage instance
        """
        self.storage = storage or ConfigStorage()
        self._config: Optional[AppConfig] = None
        self._observers: List[ConfigObserver] = []
        self._change_history: List[ConfigChangeEvent] = []
        self._lock = threading.RLock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load initial configuration
        self._load_initial_config()
    
    def _load_initial_config(self):
        """Load initial configuration on startup."""
        try:
            config_data = self.storage.load_config()
            if config_data:
                self._config = AppConfig.from_dict(config_data)
                if not self._config.validate():
                    self.logger.warning("Loaded configuration is invalid, using defaults")
                    self._config = AppConfig.get_default()
            else:
                self._config = AppConfig.get_default()
                # Save default configuration
                self.save_config()
                
        except Exception as e:
            self.logger.error(f"Error loading initial configuration: {e}")
            self._config = AppConfig.get_default()
    
    def get_config(self) -> AppConfig:
        """
        Get current configuration.
        
        Returns:
            Current AppConfig instance
        """
        with self._lock:
            if self._config is None:
                self._config = AppConfig.get_default()
            return self._config
    
    def load_config(self) -> AppConfig:
        """
        Reload configuration from storage.
        
        Returns:
            Loaded AppConfig instance
        """
        with self._lock:
            try:
                config_data = self.storage.load_config()
                if config_data:
                    new_config = AppConfig.from_dict(config_data)
                    if new_config.validate():
                        old_config = self._config
                        self._config = new_config
                        
                        # Notify observers of changes
                        if old_config:
                            self._notify_config_reload(old_config, new_config)
                        
                        self.logger.info("Configuration reloaded successfully")
                    else:
                        self.logger.error("Loaded configuration is invalid")
                        raise ValueError("Invalid configuration")
                else:
                    self.logger.warning("No configuration file found, using defaults")
                    self._config = AppConfig.get_default()
                
                return self._config
                
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
                self._config = AppConfig.get_default()
                return self._config
    
    def save_config(self, config: Optional[AppConfig] = None) -> bool:
        """
        Save configuration to storage.
        
        Args:
            config: Configuration to save (uses current if None)
            
        Returns:
            True if save was successful
        """
        with self._lock:
            try:
                config_to_save = config or self._config
                if not config_to_save:
                    self.logger.error("No configuration to save")
                    return False
                
                if not config_to_save.validate():
                    self.logger.error("Configuration validation failed")
                    return False
                
                config_data = config_to_save.to_dict()
                success = self.storage.save_config(config_data)
                
                if success:
                    self._config = config_to_save
                    self.logger.info("Configuration saved successfully")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error saving configuration: {e}")
                return False
    
    def get_setting(self, key: str) -> Any:
        """
        Get a specific configuration setting.
        
        Args:
            key: Setting key (dot notation supported, e.g., 'ui.theme')
            
        Returns:
            Setting value or None if not found
        """
        with self._lock:
            try:
                config = self.get_config()
                
                # Handle dot notation
                if '.' in key:
                    parts = key.split('.')
                    value = config
                    for part in parts:
                        if hasattr(value, part):
                            value = getattr(value, part)
                        else:
                            return None
                    return value
                else:
                    return getattr(config, key, None)
                    
            except Exception as e:
                self.logger.error(f"Error getting setting '{key}': {e}")
                return None
    
    def set_setting(self, key: str, value: Any, save_immediately: bool = True) -> bool:
        """
        Set a specific configuration setting.
        
        Args:
            key: Setting key (dot notation supported)
            value: New value
            save_immediately: Whether to save config immediately
            
        Returns:
            True if setting was updated successfully
        """
        with self._lock:
            try:
                config = self.get_config()
                old_value = self.get_setting(key)
                
                # Handle dot notation
                if '.' in key:
                    parts = key.split('.')
                    target = config
                    for part in parts[:-1]:
                        if hasattr(target, part):
                            target = getattr(target, part)
                        else:
                            self.logger.error(f"Invalid setting path: {key}")
                            return False
                    
                    if hasattr(target, parts[-1]):
                        setattr(target, parts[-1], value)
                    else:
                        self.logger.error(f"Invalid setting key: {key}")
                        return False
                else:
                    if hasattr(config, key):
                        setattr(config, key, value)
                    else:
                        self.logger.error(f"Invalid setting key: {key}")
                        return False
                
                # Validate configuration
                if not config.validate():
                    self.logger.error(f"Setting '{key}' to '{value}' makes configuration invalid")
                    return False
                
                # Record change
                change_event = ConfigChangeEvent(
                    setting_key=key,
                    old_value=old_value,
                    new_value=value,
                    timestamp=datetime.now()
                )
                self._change_history.append(change_event)
                
                # Keep only last 100 changes
                if len(self._change_history) > 100:
                    self._change_history = self._change_history[-100:]
                
                # Notify observers
                self._notify_observers(key, old_value, value)
                
                # Save if requested
                if save_immediately:
                    return self.save_config(config)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error setting '{key}' to '{value}': {e}")
                return False
    
    def reset_to_defaults(self, save_immediately: bool = True) -> bool:
        """
        Reset configuration to default values.
        
        Args:
            save_immediately: Whether to save config immediately
            
        Returns:
            True if reset was successful
        """
        with self._lock:
            try:
                old_config = self._config
                self._config = AppConfig.get_default()
                
                # Record change
                change_event = ConfigChangeEvent(
                    setting_key="*",
                    old_value="custom_config",
                    new_value="default_config",
                    timestamp=datetime.now(),
                    source="reset"
                )
                self._change_history.append(change_event)
                
                # Notify observers
                if old_config:
                    self._notify_config_reload(old_config, self._config)
                
                # Save if requested
                if save_immediately:
                    return self.save_config()
                
                self.logger.info("Configuration reset to defaults")
                return True
                
            except Exception as e:
                self.logger.error(f"Error resetting configuration: {e}")
                return False
    
    def add_observer(self, observer: ConfigObserver) -> None:
        """
        Add a configuration change observer.
        
        Args:
            observer: Observer to add
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
                self.logger.debug(f"Added configuration observer: {observer}")
    
    def remove_observer(self, observer: ConfigObserver) -> None:
        """
        Remove a configuration change observer.
        
        Args:
            observer: Observer to remove
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
                self.logger.debug(f"Removed configuration observer: {observer}")
    
    def _notify_observers(self, setting_key: str, old_value: Any, new_value: Any) -> None:
        """
        Notify all observers of a configuration change.
        
        Args:
            setting_key: Key of changed setting
            old_value: Previous value
            new_value: New value
        """
        for observer in self._observers[:]:  # Copy list to avoid modification during iteration
            try:
                observer.on_config_changed(setting_key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"Error notifying observer {observer}: {e}")
    
    def _notify_config_reload(self, old_config: AppConfig, new_config: AppConfig) -> None:
        """
        Notify observers when entire configuration is reloaded.
        
        Args:
            old_config: Previous configuration
            new_config: New configuration
        """
        # Compare configurations and notify for each changed setting
        old_dict = old_config.to_dict()
        new_dict = new_config.to_dict()
        
        for key, new_value in new_dict.items():
            old_value = old_dict.get(key)
            if old_value != new_value:
                self._notify_observers(key, old_value, new_value)
    
    def get_change_history(self, limit: Optional[int] = None) -> List[ConfigChangeEvent]:
        """
        Get configuration change history.
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of configuration change events
        """
        with self._lock:
            if limit:
                return self._change_history[-limit:]
            return self._change_history.copy()
    
    def export_config(self, file_path: Union[str, Path]) -> bool:
        """
        Export current configuration to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if export was successful
        """
        try:
            config = self.get_config()
            config_data = config.to_dict()
            
            # Add metadata
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "application": "Windows Scheduler GUI"
                },
                "configuration": config_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, file_path: Union[str, Path], save_immediately: bool = True) -> bool:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import file
            save_immediately: Whether to save config immediately
            
        Returns:
            True if import was successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Extract configuration data
            if "configuration" in import_data:
                config_data = import_data["configuration"]
            else:
                # Assume entire file is configuration
                config_data = import_data
            
            # Create and validate configuration
            new_config = AppConfig.from_dict(config_data)
            if not new_config.validate():
                self.logger.error("Imported configuration is invalid")
                return False
            
            # Apply configuration
            old_config = self._config
            self._config = new_config
            
            # Record change
            change_event = ConfigChangeEvent(
                setting_key="*",
                old_value="previous_config",
                new_value="imported_config",
                timestamp=datetime.now(),
                source="import"
            )
            self._change_history.append(change_event)
            
            # Notify observers
            if old_config:
                self._notify_config_reload(old_config, new_config)
            
            # Save if requested
            if save_immediately:
                self.save_config()
            
            self.logger.info(f"Configuration imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available configuration backups.
        
        Returns:
            List of backup information dictionaries
        """
        try:
            backup_files = self.storage.get_backup_list()
            backup_info = []
            
            for backup_file in backup_files:
                stat = backup_file.stat()
                backup_info.append({
                    "path": backup_file,
                    "name": backup_file.name,
                    "created_at": datetime.fromtimestamp(stat.st_mtime),
                    "size": stat.st_size
                })
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Error getting backup list: {e}")
            return []
    
    def restore_from_backup(self, backup_path: Union[str, Path]) -> bool:
        """
        Restore configuration from a backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore was successful
        """
        try:
            if self.storage.restore_from_backup(Path(backup_path)):
                # Reload configuration
                self.load_config()
                
                # Record change
                change_event = ConfigChangeEvent(
                    setting_key="*",
                    old_value="current_config",
                    new_value="restored_config",
                    timestamp=datetime.now(),
                    source="restore"
                )
                self._change_history.append(change_event)
                
                self.logger.info(f"Configuration restored from backup: {backup_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def initialize_config_manager(storage: Optional[ConfigStorage] = None) -> ConfigurationManager:
    """
    Initialize the global configuration manager.
    
    Args:
        storage: Optional custom storage instance
        
    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    _config_manager = ConfigurationManager(storage)
    return _config_manager