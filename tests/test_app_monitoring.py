"""
Tests for application monitoring functionality.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.gui.widgets.app_list_widget import AppListWidget
from src.gui.widgets.app_detail_widget import AppDetailWidget
from src.gui.widgets.app_monitor_panel import AppMonitorPanel
from src.models.data_models import App


class TestAppListWidget(unittest.TestCase):
    """Test cases for AppListWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
    def tearDown(self):
        """Clean up test environment."""
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that AppListWidget can be created."""
        widget = AppListWidget(self.root)
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, AppListWidget)
        widget.destroy()
    
    @patch('src.core.windows_controller.WindowsController.get_running_apps')
    def test_app_list_display(self, mock_get_apps):
        """Test that applications are displayed correctly."""
        # Mock applications data
        mock_apps = [
            App(
                name="notepad.exe",
                title="Untitled - Notepad",
                process_id=1234,
                window_handle=12345,
                is_visible=True,
                x=100,
                y=100,
                width=800,
                height=600
            ),
            App(
                name="chrome.exe",
                title="Google Chrome",
                process_id=5678,
                window_handle=56789,
                is_visible=True,
                x=200,
                y=200,
                width=1024,
                height=768
            )
        ]
        mock_get_apps.return_value = mock_apps
        
        widget = AppListWidget(self.root)
        widget.refresh_apps()
        
        # Wait for background refresh to complete
        self.root.update()
        
        # Check that apps are loaded
        self.assertEqual(len(widget.apps), 2)
        self.assertEqual(widget.apps[0].name, "notepad.exe")
        self.assertEqual(widget.apps[1].name, "chrome.exe")
        
        widget.destroy()
    
    def test_search_functionality(self):
        """Test search functionality."""
        widget = AppListWidget(self.root)
        
        # Mock some apps
        widget.apps = [
            App(name="notepad.exe", title="Notepad", process_id=1, is_visible=True),
            App(name="chrome.exe", title="Chrome", process_id=2, is_visible=True),
            App(name="calculator.exe", title="Calculator", process_id=3, is_visible=True)
        ]
        
        # Test search
        widget.search_var.set("note")
        widget._on_search_changed()
        
        # Should find notepad
        self.assertEqual(len(widget.filtered_apps), 1)
        self.assertEqual(widget.filtered_apps[0].name, "notepad.exe")
        
        widget.destroy()
    
    def test_filter_functionality(self):
        """Test filter functionality."""
        widget = AppListWidget(self.root)
        
        # Mock some apps with different visibility
        widget.apps = [
            App(name="visible.exe", title="Visible App", process_id=1, is_visible=True),
            App(name="hidden.exe", title="Hidden App", process_id=2, is_visible=False),
            App(name="notitle.exe", title="", process_id=3, is_visible=True)
        ]
        
        # Test "Visible Only" filter
        widget.filter_var.set("Visible Only")
        widget._on_filter_changed()
        
        # Should only show visible apps
        self.assertEqual(len(widget.filtered_apps), 2)
        self.assertTrue(all(app.is_visible for app in widget.filtered_apps))
        
        # Test "With Windows" filter
        widget.filter_var.set("With Windows")
        widget._on_filter_changed()
        
        # Should only show apps with titles
        self.assertEqual(len(widget.filtered_apps), 2)
        self.assertTrue(all(app.title for app in widget.filtered_apps))
        
        widget.destroy()


class TestAppDetailWidget(unittest.TestCase):
    """Test cases for AppDetailWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
    def tearDown(self):
        """Clean up test environment."""
        self.root.destroy()
    
    def test_widget_creation(self):
        """Test that AppDetailWidget can be created."""
        widget = AppDetailWidget(self.root)
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, AppDetailWidget)
        widget.destroy()
    
    def test_app_info_display(self):
        """Test that app information is displayed correctly."""
        widget = AppDetailWidget(self.root)
        
        # Create test app
        test_app = App(
            name="test.exe",
            title="Test Application",
            process_id=1234,
            window_handle=12345,
            is_visible=True,
            x=100,
            y=200,
            width=800,
            height=600
        )
        
        # Set app
        widget.set_app(test_app)
        
        # Check that info is displayed
        self.assertEqual(widget.info_labels["app_name"].cget("text"), "test.exe")
        self.assertEqual(widget.info_labels["window_title"].cget("text"), "Test Application")
        self.assertEqual(widget.info_labels["process_id"].cget("text"), "1234")
        self.assertEqual(widget.info_labels["position"].cget("text"), "(100, 200)")
        self.assertEqual(widget.info_labels["size"].cget("text"), "800 × 600")
        self.assertEqual(widget.info_labels["visibility"].cget("text"), "Visible")
        
        widget.destroy()
    
    def test_empty_state(self):
        """Test empty state when no app is selected."""
        widget = AppDetailWidget(self.root)
        
        # Should show empty state
        for label in widget.info_labels.values():
            self.assertEqual(label.cget("text"), "N/A")
        
        widget.destroy()


class TestAppMonitorPanel(unittest.TestCase):
    """Test cases for AppMonitorPanel."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        
    def tearDown(self):
        """Clean up test environment."""
        self.root.destroy()
    
    def test_panel_creation(self):
        """Test that AppMonitorPanel can be created."""
        panel = AppMonitorPanel(self.root)
        self.assertIsNotNone(panel)
        self.assertIsInstance(panel, AppMonitorPanel)
        
        # Check that child widgets are created
        self.assertIsNotNone(panel.app_list_widget)
        self.assertIsNotNone(panel.app_detail_widget)
        
        panel.destroy()
    
    def test_app_selection_integration(self):
        """Test that app selection works between list and detail widgets."""
        panel = AppMonitorPanel(self.root)
        
        # Create test app
        test_app = App(
            name="test.exe",
            title="Test Application",
            process_id=1234,
            is_visible=True
        )
        
        # Simulate app selection
        panel._on_app_selected(test_app)
        
        # Check that detail widget is updated
        self.assertEqual(panel.current_app, test_app)
        self.assertEqual(panel.app_detail_widget.current_app, test_app)
        
        panel.destroy()


if __name__ == '__main__':
    unittest.main()