"""
Test settings validation and storage functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from tkinter import ttk

from src.gui.pages.settings_page import SettingsPage
from src.core.config_manager import ConfigurationManager, ConfigStorage
from src.models.config import AppConfig


class TestSettingsValidation(unittest.TestCase):
    """Test settings validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
        # Mock config manager
        self.mock_storage = Mock(spec=ConfigStorage)
        self.config_manager = ConfigurationManager(self.mock_storage)
        
        # Create settings page
        with patch('src.gui.pages.settings_page.get_config_manager', return_value=self.config_manager):
            self.settings_page = SettingsPage(self.root)
    
    def tearDown(self):
        """Clean up test environment."""
        self.settings_page.destroy()
        self.root.destroy()
    
    def test_validate_schedule_frequency(self):
        """Test schedule frequency validation."""
        # Mock frequency widget
        mock_widget = Mock()
        mock_widget.validate.return_value = True
        mock_widget.get_frequency.return_value = 5
        self.settings_page.schedule_frequency_widget = mock_widget
        
        # Test valid frequency
        self.assertTrue(self.settings_page._validate_all_settings())
        
        # Test invalid frequency
        mock_widget.validate.return_value = False
        self.assertFalse(self.settings_page._validate_all_settings())
    
    def test_validate_retry_attempts(self):
        """Test retry attempts validation."""
        # Mock spinbox widget
        mock_spinbox = Mock()
        mock_spinbox.get.return_value = "5"
        self.settings_page.additional_widgets["max_retry_attempts"] = mock_spinbox
        
        # Test valid retry attempts
        self.assertTrue(self.settings_page._validate_all_settings())
        
        # Test invalid retry attempts (too high)
        mock_spinbox.get.return_value = "15"
        self.assertFalse(self.settings_page._validate_all_settings())
        
        # Test invalid retry attempts (non-numeric)
        mock_spinbox.get.return_value = "invalid"
        self.assertFalse(self.settings_page._validate_all_settings())
    
    def test_collect_all_settings(self):
        """Test settings collection."""
        # Mock widgets
        mock_freq_widget = Mock()
        mock_freq_widget.get_frequency.return_value = 10
        self.settings_page.schedule_frequency_widget = mock_freq_widget
        
        mock_notif_widget = Mock()
        mock_notif_widget.get_settings.return_value = {
            "notifications_enabled": True,
            "sound_enabled": False
        }
        self.settings_page.notification_options_widget = mock_notif_widget
        
        mock_log_widget = Mock()
        mock_log_widget.get_settings.return_value = {
            "logging_enabled": True,
            "retention_days": 30
        }
        self.settings_page.log_recording_widget = mock_log_widget
        
        mock_spinbox = Mock()
        mock_spinbox.get.return_value = "3"
        self.settings_page.additional_widgets["max_retry_attempts"] = mock_spinbox
        
        # Collect settings
        settings = self.settings_page._collect_all_settings()
        
        # Verify collected settings
        self.assertEqual(settings["schedule_check_frequency"], 10)
        self.assertEqual(settings["notifications_enabled"], True)
        self.assertEqual(settings["notification_sound_enabled"], False)
        self.assertEqual(settings["log_recording_enabled"], True)
        self.assertEqual(settings["log_retention_days"], 30)
        self.assertEqual(settings["max_retry_attempts"], 3)
    
    def test_apply_settings_with_rollback_success(self):
        """Test successful settings application."""
        # Mock successful config operations
        self.mock_storage.save_config.return_value = True
        
        updates = {
            "schedule_check_frequency": 5,
            "notifications_enabled": True
        }
        
        # Test successful application
        result = self.settings_page._apply_settings_with_rollback(updates)
        self.assertTrue(result)
    
    def test_apply_settings_with_rollback_failure(self):
        """Test settings application with rollback."""
        # Mock failed config operations
        self.mock_storage.save_config.return_value = False
        
        updates = {
            "schedule_check_frequency": 5,
            "notifications_enabled": True
        }
        
        # Test failed application with rollback
        result = self.settings_page._apply_settings_with_rollback(updates)
        self.assertFalse(result)
    
    def test_create_temp_config(self):
        """Test temporary config creation for validation."""
        # Mock widgets
        mock_freq_widget = Mock()
        mock_freq_widget.get_frequency.return_value = 15
        self.settings_page.schedule_frequency_widget = mock_freq_widget
        
        # Create temporary config
        temp_config = self.settings_page._create_temp_config()
        
        # Verify temp config
        self.assertIsInstance(temp_config, AppConfig)
        self.assertEqual(temp_config.schedule_check_frequency, 15)
    
    @patch('src.gui.pages.settings_page.messagebox')
    def test_save_settings_validation_failure(self, mock_messagebox):
        """Test save settings with validation failure."""
        # Mock validation failure
        with patch.object(self.settings_page, '_validate_all_settings', return_value=False):
            self.settings_page._save_settings()
        
        # Verify no save attempt was made
        self.mock_storage.save_config.assert_not_called()
    
    @patch('src.gui.pages.settings_page.messagebox')
    def test_save_settings_success(self, mock_messagebox):
        """Test successful settings save."""
        # Mock successful validation and save
        with patch.object(self.settings_page, '_validate_all_settings', return_value=True):
            with patch.object(self.settings_page, '_collect_all_settings', return_value={"test": "value"}):
                with patch.object(self.settings_page, '_apply_settings_with_rollback', return_value=True):
                    with patch.object(self.settings_page, '_apply_immediate_changes'):
                        self.settings_page._save_settings()
        
        # Verify success message
        mock_messagebox.showinfo.assert_called_once()


class TestSettingsIntegration(unittest.TestCase):
    """Test settings page integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Use real config manager with mock storage
        self.mock_storage = Mock(spec=ConfigStorage)
        self.mock_storage.load_config.return_value = None  # Use defaults
        self.config_manager = ConfigurationManager(self.mock_storage)
    
    def tearDown(self):
        """Clean up test environment."""
        self.root.destroy()
    
    def test_settings_page_initialization(self):
        """Test settings page initialization."""
        with patch('src.gui.pages.settings_page.get_config_manager', return_value=self.config_manager):
            settings_page = SettingsPage(self.root)
            
            # Verify page is initialized
            self.assertIsNotNone(settings_page.config_manager)
            self.assertEqual(settings_page.config_manager, self.config_manager)
            
            # Verify observer is registered
            self.assertIn(settings_page, self.config_manager._observers)
            
            settings_page.destroy()
    
    def test_config_change_notification(self):
        """Test configuration change notification."""
        with patch('src.gui.pages.settings_page.get_config_manager', return_value=self.config_manager):
            settings_page = SettingsPage(self.root)
            
            # Mock load settings method
            with patch.object(settings_page, '_load_settings') as mock_load:
                # Trigger config change
                self.config_manager.set_setting("schedule_check_frequency", 10)
                
                # Verify settings are reloaded
                mock_load.assert_called_once()
            
            settings_page.destroy()


if __name__ == '__main__':
    unittest.main()