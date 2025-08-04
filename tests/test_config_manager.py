"""
Tests for configuration management functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config_manager import ConfigStorage, ConfigurationManager, ConfigObserver
from src.models.config import AppConfig


class TestConfigObserver(ConfigObserver):
    """Test observer for configuration changes."""
    
    def __init__(self):
        self.changes = []
    
    def on_config_changed(self, setting_key: str, old_value, new_value) -> None:
        self.changes.append({
            'key': setting_key,
            'old_value': old_value,
            'new_value': new_value
        })


class TestConfigStorage(unittest.TestCase):
    """Test cases for ConfigStorage class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.backup_dir = Path(self.temp_dir) / "backups"
        self.storage = ConfigStorage(
            config_dir=str(self.config_dir),
            config_file="test_config.json"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_directories(self):
        """Test directory creation."""
        self.assertTrue(self.config_dir.exists())
        self.assertTrue(self.backup_dir.exists())
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        test_config = {
            "schedule_check_frequency": 5,
            "notifications_enabled": False,
            "ui_theme": "dark"
        }
        
        # Save configuration
        success = self.storage.save_config(test_config)
        self.assertTrue(success)
        
        # Load configuration
        loaded_config = self.storage.load_config()
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config["schedule_check_frequency"], 5)
        self.assertEqual(loaded_config["notifications_enabled"], False)
        self.assertEqual(loaded_config["ui_theme"], "dark")
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration."""
        result = self.storage.load_config()
        self.assertIsNone(result)
    
    def test_backup_creation(self):
        """Test configuration backup creation."""
        test_config = {"test": "value"}
        
        # Save initial config
        self.storage.save_config(test_config)
        
        # Save again to trigger backup
        updated_config = {"test": "updated_value"}
        success = self.storage.save_config(updated_config, create_backup=True)
        self.assertTrue(success)
        
        # Check backup was created
        backups = self.storage.get_backup_list()
        self.assertGreater(len(backups), 0)
    
    def test_restore_from_backup(self):
        """Test restoring configuration from backup."""
        original_config = {"test": "original"}
        updated_config = {"test": "updated"}
        
        # Save original and create backup
        self.storage.save_config(original_config)
        self.storage.save_config(updated_config, create_backup=True)
        
        # Get backup list and restore from first backup
        backups = self.storage.get_backup_list()
        self.assertGreater(len(backups), 0)
        
        success = self.storage.restore_from_backup(backups[0])
        self.assertTrue(success)
        
        # Verify restoration
        loaded_config = self.storage.load_config()
        self.assertEqual(loaded_config["test"], "updated")


class TestAppConfig(unittest.TestCase):
    """Test cases for AppConfig class."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = AppConfig.get_default()
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.schedule_check_frequency, 1)
        self.assertTrue(config.notifications_enabled)
        self.assertEqual(config.ui_theme, "default")
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        valid_config = AppConfig()
        self.assertTrue(valid_config.validate())
        
        # Invalid schedule frequency
        invalid_config = AppConfig(schedule_check_frequency=0)
        self.assertFalse(invalid_config.validate())
        
        # Invalid window dimensions
        invalid_config = AppConfig(window_width=500)
        self.assertFalse(invalid_config.validate())
        
        # Invalid theme
        invalid_config = AppConfig(ui_theme="invalid_theme")
        self.assertFalse(invalid_config.validate())
    
    def test_to_dict_and_from_dict(self):
        """Test configuration serialization."""
        original_config = AppConfig(
            schedule_check_frequency=5,
            notifications_enabled=False,
            ui_theme="dark"
        )
        
        # Convert to dict
        config_dict = original_config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict["schedule_check_frequency"], 5)
        
        # Convert back from dict
        restored_config = AppConfig.from_dict(config_dict)
        self.assertEqual(restored_config.schedule_check_frequency, 5)
        self.assertEqual(restored_config.notifications_enabled, False)
        self.assertEqual(restored_config.ui_theme, "dark")
    
    def test_update_from_dict(self):
        """Test configuration update from dictionary."""
        config = AppConfig()
        original_frequency = config.schedule_check_frequency
        
        updates = {
            "schedule_check_frequency": 10,
            "ui_theme": "dark"
        }
        
        config.update_from_dict(updates)
        self.assertEqual(config.schedule_check_frequency, 10)
        self.assertEqual(config.ui_theme, "dark")
        self.assertNotEqual(config.schedule_check_frequency, original_frequency)


class TestConfigurationManager(unittest.TestCase):
    """Test cases for ConfigurationManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = ConfigStorage(
            config_dir=str(Path(self.temp_dir) / "config"),
            config_file="test_config.json"
        )
        self.manager = ConfigurationManager(self.storage)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_config(self):
        """Test getting current configuration."""
        config = self.manager.get_config()
        self.assertIsInstance(config, AppConfig)
    
    def test_set_and_get_setting(self):
        """Test setting and getting individual settings."""
        # Set a setting
        success = self.manager.set_setting("schedule_check_frequency", 5, save_immediately=False)
        self.assertTrue(success)
        
        # Get the setting
        value = self.manager.get_setting("schedule_check_frequency")
        self.assertEqual(value, 5)
    
    def test_invalid_setting_key(self):
        """Test handling of invalid setting keys."""
        success = self.manager.set_setting("invalid_key", "value", save_immediately=False)
        self.assertFalse(success)
        
        value = self.manager.get_setting("invalid_key")
        self.assertIsNone(value)
    
    def test_config_validation_on_set(self):
        """Test configuration validation when setting values."""
        # Try to set invalid value
        success = self.manager.set_setting("schedule_check_frequency", -1, save_immediately=False)
        self.assertFalse(success)
        
        # Verify original value is preserved
        value = self.manager.get_setting("schedule_check_frequency")
        self.assertNotEqual(value, -1)
    
    def test_observer_notification(self):
        """Test observer notification on configuration changes."""
        observer = TestConfigObserver()
        self.manager.add_observer(observer)
        
        # Change a setting
        self.manager.set_setting("schedule_check_frequency", 10, save_immediately=False)
        
        # Check observer was notified
        self.assertEqual(len(observer.changes), 1)
        self.assertEqual(observer.changes[0]["key"], "schedule_check_frequency")
        self.assertEqual(observer.changes[0]["new_value"], 10)
        
        # Remove observer
        self.manager.remove_observer(observer)
        
        # Change setting again
        self.manager.set_setting("notifications_enabled", False, save_immediately=False)
        
        # Observer should not be notified
        self.assertEqual(len(observer.changes), 1)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        # Change some settings
        self.manager.set_setting("schedule_check_frequency", 10, save_immediately=False)
        self.manager.set_setting("ui_theme", "dark", save_immediately=False)
        
        # Reset to defaults
        success = self.manager.reset_to_defaults(save_immediately=False)
        self.assertTrue(success)
        
        # Verify settings are back to defaults
        config = self.manager.get_config()
        default_config = AppConfig.get_default()
        self.assertEqual(config.schedule_check_frequency, default_config.schedule_check_frequency)
        self.assertEqual(config.ui_theme, default_config.ui_theme)
    
    def test_change_history(self):
        """Test configuration change history tracking."""
        # Make some changes
        self.manager.set_setting("schedule_check_frequency", 5, save_immediately=False)
        self.manager.set_setting("ui_theme", "dark", save_immediately=False)
        
        # Get change history
        history = self.manager.get_change_history()
        self.assertGreaterEqual(len(history), 2)
        
        # Check history entries
        recent_changes = history[-2:]
        keys = [change.setting_key for change in recent_changes]
        self.assertIn("schedule_check_frequency", keys)
        self.assertIn("ui_theme", keys)
    
    def test_export_and_import_config(self):
        """Test configuration export and import."""
        # Change some settings
        self.manager.set_setting("schedule_check_frequency", 15, save_immediately=False)
        self.manager.set_setting("ui_theme", "dark", save_immediately=False)
        
        # Export configuration
        export_path = Path(self.temp_dir) / "exported_config.json"
        success = self.manager.export_config(export_path)
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # Reset to defaults
        self.manager.reset_to_defaults(save_immediately=False)
        
        # Import configuration
        success = self.manager.import_config(export_path, save_immediately=False)
        self.assertTrue(success)
        
        # Verify settings were restored
        self.assertEqual(self.manager.get_setting("schedule_check_frequency"), 15)
        self.assertEqual(self.manager.get_setting("ui_theme"), "dark")
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Change some settings
        self.manager.set_setting("schedule_check_frequency", 20, save_immediately=False)
        
        # Save configuration
        success = self.manager.save_config()
        self.assertTrue(success)
        
        # Create new manager with same storage
        new_manager = ConfigurationManager(self.storage)
        
        # Verify settings were loaded
        self.assertEqual(new_manager.get_setting("schedule_check_frequency"), 20)


if __name__ == "__main__":
    unittest.main()