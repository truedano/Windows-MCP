"""
Tests for ExecutionPreviewWidget functionality.
"""

import unittest
import tkinter as tk
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.widgets.execution_preview_widget import ExecutionPreviewWidget
from models.action import ActionType
from models.schedule import ScheduleType, ConditionType, ConditionalTrigger


class TestExecutionPreviewWidget(unittest.TestCase):
    """Test cases for ExecutionPreviewWidget."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        self.widget = ExecutionPreviewWidget(self.root)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_widget_initialization(self):
        """Test widget initialization."""
        # Widget should be created successfully
        self.assertIsInstance(self.widget, ExecutionPreviewWidget)
        
        # Preview text widget should exist
        self.assertTrue(hasattr(self.widget, 'preview_text'))
        self.assertIsInstance(self.widget.preview_text, tk.Text)
        
        # Text widget should be disabled initially
        self.assertEqual(self.widget.preview_text.cget('state'), 'disabled')
    
    def test_empty_preview_display(self):
        """Test empty preview display."""
        # Widget should show empty preview message initially
        content = self.widget.preview_text.get("1.0", tk.END).strip()
        self.assertIn("請填寫排程資訊以查看執行預覽", content)
    
    def test_basic_schedule_preview(self):
        """Test basic schedule preview functionality."""
        config = {
            'name': '測試排程',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        # Update preview with config
        self.widget.update_preview(config)
        
        # Check that preview content is updated
        content = self.widget.preview_text.get("1.0", tk.END)
        self.assertIn("測試排程", content)
        self.assertIn("notepad", content)
        self.assertIn("一次性執行", content)
        self.assertIn("啟動應用程式", content)
    
    def test_daily_schedule_preview(self):
        """Test daily schedule preview."""
        config = {
            'name': '每日備份',
            'target_app': 'backup_tool',
            'schedule': {
                'schedule_type': ScheduleType.DAILY.value,
                'start_time': datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'backup_tool'},
            'options': {
                'repeat_enabled': True,
                'retry_enabled': True,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("每日備份", content)
        self.assertIn("每日重複", content)
        self.assertIn("10:00", content)
        self.assertIn("重複執行: 啟用", content)
        self.assertIn("失敗重試: 啟用", content)
    
    def test_weekly_schedule_preview(self):
        """Test weekly schedule preview."""
        config = {
            'name': '週報生成',
            'target_app': 'excel',
            'schedule': {
                'schedule_type': ScheduleType.WEEKLY.value,
                'start_time': datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
                'days_of_week': [0, 4]  # Monday and Friday
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'excel'},
            'options': {
                'repeat_enabled': True,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("週報生成", content)
        self.assertIn("每週重複", content)
        self.assertIn("週一", content)
        self.assertIn("週五", content)
        self.assertIn("09:00", content)
    
    def test_conditional_trigger_preview(self):
        """Test conditional trigger preview."""
        conditional_trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="工作",
            enabled=True
        )
        
        config = {
            'name': '條件觸發測試',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'conditional_trigger': conditional_trigger,
            'action_type': ActionType.CLOSE_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("條件觸發", content)
        self.assertIn("視窗標題包含", content)
        self.assertIn("工作", content)
        self.assertIn("只有在條件滿足時才會執行", content)
    
    def test_action_parameters_preview(self):
        """Test action parameters preview."""
        # Test resize window action
        config = {
            'name': '調整視窗',
            'target_app': 'chrome',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'action_type': ActionType.RESIZE_WINDOW,
            'action_params': {
                'app_name': 'chrome',
                'width': 1024,
                'height': 768
            },
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("調整視窗大小", content)
        self.assertIn("1024 x 768", content)
        
        # Test move window action
        config['action_type'] = ActionType.MOVE_WINDOW
        config['action_params'] = {
            'app_name': 'chrome',
            'x': 100,
            'y': 200
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("移動視窗位置", content)
        self.assertIn("(100, 200)", content)
        
        # Test type text action
        config['action_type'] = ActionType.TYPE_TEXT
        config['action_params'] = {
            'app_name': 'notepad',
            'text': 'Hello World',
            'x': 50,
            'y': 100
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("輸入文字", content)
        self.assertIn("Hello World", content)
        self.assertIn("(50, 100)", content)
        
        # Test send keys action
        config['action_type'] = ActionType.SEND_KEYS
        config['action_params'] = {
            'keys': ['ctrl', 's']
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("發送按鍵", content)
        self.assertIn("ctrl + s", content)
    
    def test_execution_timeline_preview(self):
        """Test execution timeline preview."""
        # Test future execution
        future_time = datetime.now() + timedelta(hours=2, minutes=30)
        config = {
            'name': '未來執行',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': future_time
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("執行時間軸", content)
        self.assertIn("下次執行", content)
        self.assertIn("距離執行", content)
        self.assertIn("2小時30分鐘", content)
    
    def test_warnings_and_notes_preview(self):
        """Test warnings and notes in preview."""
        # Test custom command warning
        config = {
            'name': '危險命令',
            'target_app': 'cmd',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'action_type': ActionType.CUSTOM_COMMAND,
            'action_params': {
                'command': 'del /f /q C:\\temp\\*'
            },
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("注意事項", content)
        self.assertIn("自訂命令可能對系統造成影響", content)
        self.assertIn("操作系統關鍵應用程式", content)
        
        # Test short interval warning
        config = {
            'name': '高頻執行',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.CUSTOM.value,
                'start_time': datetime.now(),
                'interval': timedelta(seconds=30)
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': True,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("執行間隔過短可能影響系統效能", content)
    
    def test_error_handling_in_preview(self):
        """Test error handling in preview update."""
        # Test with invalid config
        invalid_config = {
            'name': '無效配置',
            # Missing required fields
        }
        
        # Should not raise exception
        try:
            self.widget.update_preview(invalid_config)
            content = self.widget.preview_text.get("1.0", tk.END)
            # Should show error message
            self.assertIn("預覽生成錯誤", content)
        except Exception as e:
            self.fail(f"Preview update should handle errors gracefully, but raised: {e}")
    
    def test_real_time_preview_updates(self):
        """Test real-time preview updates."""
        # Initial config
        config = {
            'name': '初始配置',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        initial_content = self.widget.preview_text.get("1.0", tk.END)
        self.assertIn("初始配置", initial_content)
        
        # Update config
        config['name'] = '更新配置'
        config['action_type'] = ActionType.CLOSE_APP
        
        self.widget.update_preview(config)
        updated_content = self.widget.preview_text.get("1.0", tk.END)
        
        self.assertIn("更新配置", updated_content)
        self.assertIn("關閉應用程式", updated_content)
        self.assertNotIn("初始配置", updated_content)
    
    def test_format_timedelta_utility(self):
        """Test timedelta formatting utility."""
        # Test seconds
        td = timedelta(seconds=30)
        result = self.widget._format_timedelta(td)
        self.assertEqual(result, "30秒")
        
        # Test minutes
        td = timedelta(minutes=5, seconds=30)
        result = self.widget._format_timedelta(td)
        self.assertEqual(result, "5分鐘30秒")
        
        # Test hours
        td = timedelta(hours=2, minutes=30)
        result = self.widget._format_timedelta(td)
        self.assertEqual(result, "2小時30分鐘")
        
        # Test days
        td = timedelta(days=1, hours=3)
        result = self.widget._format_timedelta(td)
        self.assertEqual(result, "1天3小時")
    
    def test_execution_confirmation_mechanism(self):
        """Test execution confirmation mechanism."""
        # The preview widget should show confirmation notes
        config = {
            'name': '確認測試',
            'target_app': 'notepad',
            'schedule': {
                'schedule_type': ScheduleType.ONCE.value,
                'start_time': datetime.now() + timedelta(hours=1)
            },
            'action_type': ActionType.LAUNCH_APP,
            'action_params': {'app_name': 'notepad'},
            'options': {
                'repeat_enabled': False,
                'retry_enabled': False,
                'notification_enabled': True,
                'logging_enabled': True
            }
        }
        
        self.widget.update_preview(config)
        content = self.widget.preview_text.get("1.0", tk.END)
        
        # Should show confirmation message
        self.assertIn("這是預覽模式，實際執行前請先測試", content)


if __name__ == '__main__':
    unittest.main()