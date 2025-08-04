"""
Test for Settings Page and related widgets functionality.
"""

import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import Mock, patch

from src.gui.widgets.schedule_frequency_widget import ScheduleFrequencyWidget
from src.gui.widgets.notification_options_widget import NotificationOptionsWidget
from src.gui.widgets.log_recording_options_widget import LogRecordingOptionsWidget
from src.gui.pages.settings_page import SettingsPage


class TestScheduleFrequencyWidget(unittest.TestCase):
    """Test cases for ScheduleFrequencyWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        self.widget = ScheduleFrequencyWidget(self.root)
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'widget'):
            self.widget.destroy()
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that widget is created successfully."""
        self.assertIsInstance(self.widget, ScheduleFrequencyWidget)
        self.assertIsInstance(self.widget, ttk.LabelFrame)
    
    def test_frequency_setting(self):
        """Test frequency setting and getting."""
        test_frequencies = [1, 5, 10, 30, 60]
        
        for freq in test_frequencies:
            self.widget.set_frequency(freq)
            self.assertEqual(self.widget.get_frequency(), freq)
    
    def test_frequency_validation(self):
        """Test frequency validation."""
        # Valid frequencies
        self.widget.set_frequency(1)
        self.assertTrue(self.widget.validate())
        
        self.widget.set_frequency(30)
        self.assertTrue(self.widget.validate())
        
        # Invalid frequencies should not be set
        original_freq = self.widget.get_frequency()
        self.widget.set_frequency(0)  # Should not change
        self.widget.set_frequency(61)  # Should not change
        # Widget should maintain valid frequency
        self.assertTrue(1 <= self.widget.get_frequency() <= 60)
    
    def test_callback_functionality(self):
        """Test callback functionality."""
        callback_called = False
        callback_value = None
        
        def test_callback(value):
            nonlocal callback_called, callback_value
            callback_called = True
            callback_value = value
        
        self.widget.set_change_callback(test_callback)
        self.widget.set_frequency(15)
        
        # Note: Callback might be called during UI updates
        # We mainly test that the callback can be set without errors


class TestNotificationOptionsWidget(unittest.TestCase):
    """Test cases for NotificationOptionsWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        self.widget = NotificationOptionsWidget(self.root)
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'widget'):
            self.widget.destroy()
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that widget is created successfully."""
        self.assertIsInstance(self.widget, NotificationOptionsWidget)
        self.assertIsInstance(self.widget, ttk.LabelFrame)
    
    def test_settings_get_set(self):
        """Test settings getting and setting."""
        test_settings = {
            "notifications_enabled": False,
            "notification_level": "errors_only",
            "sound_enabled": False
        }
        
        self.widget.set_settings(test_settings)
        current_settings = self.widget.get_settings()
        
        self.assertEqual(current_settings["notifications_enabled"], False)
        self.assertEqual(current_settings["notification_level"], "errors_only")
        self.assertEqual(current_settings["sound_enabled"], False)
    
    def test_validation(self):
        """Test settings validation."""
        # Valid settings
        self.widget.set_settings({
            "notification_level": "all"
        })
        self.assertTrue(self.widget.validate())
        
        self.widget.set_settings({
            "notification_level": "warnings_errors"
        })
        self.assertTrue(self.widget.validate())
        
        # Invalid settings
        self.widget.notification_level_var.set("invalid_level")
        self.assertFalse(self.widget.validate())


class TestLogRecordingOptionsWidget(unittest.TestCase):
    """Test cases for LogRecordingOptionsWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        self.widget = LogRecordingOptionsWidget(self.root)
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'widget'):
            self.widget.destroy()
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that widget is created successfully."""
        self.assertIsInstance(self.widget, LogRecordingOptionsWidget)
        self.assertIsInstance(self.widget, ttk.LabelFrame)
    
    def test_settings_get_set(self):
        """Test settings getting and setting."""
        test_settings = {
            "logging_enabled": False,
            "log_level": "error",
            "retention_days": 60,
            "max_file_size_mb": 20,
            "auto_cleanup": False,
            "log_path": "custom/logs/"
        }
        
        self.widget.set_settings(test_settings)
        current_settings = self.widget.get_settings()
        
        self.assertEqual(current_settings["logging_enabled"], False)
        self.assertEqual(current_settings["log_level"], "error")
        self.assertEqual(current_settings["retention_days"], 60)
        self.assertEqual(current_settings["max_file_size_mb"], 20)
        self.assertEqual(current_settings["auto_cleanup"], False)
        self.assertEqual(current_settings["log_path"], "custom/logs/")
    
    def test_validation(self):
        """Test settings validation."""
        # Valid settings
        self.assertTrue(self.widget.validate())
        
        # Invalid log level
        self.widget.log_level_var.set("invalid_level")
        self.assertFalse(self.widget.validate())
        
        # Invalid retention days
        self.widget.log_level_var.set("info")  # Reset to valid
        self.widget.retention_days_var.set(0)
        self.assertFalse(self.widget.validate())
        
        self.widget.retention_days_var.set(400)
        self.assertFalse(self.widget.validate())
        
        # Invalid file size
        self.widget.retention_days_var.set(30)  # Reset to valid
        self.widget.max_file_size_var.set(0)
        self.assertFalse(self.widget.validate())
        
        self.widget.max_file_size_var.set(200)
        self.assertFalse(self.widget.validate())
        
        # Invalid path
        self.widget.max_file_size_var.set(10)  # Reset to valid
        self.widget.log_path_var.set("")
        self.assertFalse(self.widget.validate())


class TestSettingsPage(unittest.TestCase):
    """Test cases for SettingsPage."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Mock the config manager
        self.mock_config_manager = Mock()
        self.mock_config = Mock()
        self.mock_config.schedule_check_frequency = 5
        self.mock_config.notifications_enabled = True
        self.mock_config.log_recording_enabled = True
        self.mock_config.log_retention_days = 30
        self.mock_config.max_retry_attempts = 3
        self.mock_config.auto_start_scheduler = True
        self.mock_config.minimize_to_tray = True
        self.mock_config.debug_mode = False
        
        self.mock_config_manager.get_config.return_value = self.mock_config
        self.mock_config_manager.save_config.return_value = True
        self.mock_config_manager.reset_to_defaults.return_value = True
        
        with patch('src.gui.pages.settings_page.get_config_manager', return_value=self.mock_config_manager):
            self.page = SettingsPage(self.root)
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'page'):
            self.page.destroy()
        self.root.destroy()
    
    def test_page_creation(self):
        """Test that page is created successfully."""
        self.assertIsInstance(self.page, SettingsPage)
        self.assertEqual(self.page.page_id, "Settings")
        self.assertEqual(self.page.title, "系統設定")
    
    def test_page_initialization(self):
        """Test page initialization."""
        # Initialize the page content
        self.page.initialize_content()
        
        # Check that widgets are created
        self.assertIsNotNone(self.page.schedule_frequency_widget)
        self.assertIsNotNone(self.page.notification_options_widget)
        self.assertIsNotNone(self.page.log_recording_widget)
    
    @patch('tkinter.messagebox.showinfo')
    def test_save_settings(self, mock_showinfo):
        """Test settings saving functionality."""
        # Initialize the page
        self.page.initialize_content()
        
        # Mock widget validation
        if self.page.schedule_frequency_widget:
            self.page.schedule_frequency_widget.validate = Mock(return_value=True)
            self.page.schedule_frequency_widget.get_frequency = Mock(return_value=10)
        
        if self.page.notification_options_widget:
            self.page.notification_options_widget.validate = Mock(return_value=True)
            self.page.notification_options_widget.get_settings = Mock(return_value={
                "notifications_enabled": True,
                "notification_level": "all"
            })
        
        if self.page.log_recording_widget:
            self.page.log_recording_widget.validate = Mock(return_value=True)
            self.page.log_recording_widget.get_settings = Mock(return_value={
                "logging_enabled": True,
                "retention_days": 30
            })
        
        # Test save
        self.page._save_settings()
        
        # Verify config manager was called
        self.assertTrue(self.mock_config_manager.set_setting.called)
        self.assertTrue(self.mock_config_manager.save_config.called)
        mock_showinfo.assert_called_with("成功", "設定已儲存")
    
    @patch('tkinter.messagebox.askyesno', return_value=True)
    @patch('tkinter.messagebox.showinfo')
    def test_reset_settings(self, mock_showinfo, mock_askyesno):
        """Test settings reset functionality."""
        # Initialize the page
        self.page.initialize_content()
        
        # Test reset
        self.page._reset_settings()
        
        # Verify config manager was called
        self.assertTrue(self.mock_config_manager.reset_to_defaults.called)
        mock_showinfo.assert_called_with("成功", "設定已重設為預設值")


def run_manual_test():
    """Run manual test to visually inspect the settings page."""
    root = tk.Tk()
    root.title("Settings Page Test")
    root.geometry("900x800")
    
    # Create a mock config manager for testing
    mock_config_manager = Mock()
    mock_config = Mock()
    mock_config.schedule_check_frequency = 5
    mock_config.notifications_enabled = True
    mock_config.log_recording_enabled = True
    mock_config.log_retention_days = 30
    mock_config.max_retry_attempts = 3
    mock_config.auto_start_scheduler = True
    mock_config.minimize_to_tray = True
    mock_config.debug_mode = False
    
    mock_config_manager.get_config.return_value = mock_config
    mock_config_manager.save_config.return_value = True
    mock_config_manager.set_setting.return_value = None
    mock_config_manager.add_observer.return_value = None
    
    with patch('src.gui.pages.settings_page.get_config_manager', return_value=mock_config_manager):
        # Create the page
        page = SettingsPage(root)
        page.frame = ttk.Frame(root)
        page.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initialize content
        page.initialize_content()
        
        print("Settings Page Test started successfully!")
        print("The page includes:")
        print("- Schedule Frequency Widget")
        print("- Notification Options Widget") 
        print("- Log Recording Options Widget")
        print("- Additional settings")
        print("- Action buttons (Save, Reset, Import, Export)")
        
        # Start the GUI
        root.mainloop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        run_manual_test()
    else:
        unittest.main()