"""
Execution preview widget for schedule dialog.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from src.models.action import ActionType
from src.models.schedule import ScheduleType, ConditionType


class ExecutionPreviewWidget(ttk.Frame):
    """Widget for previewing schedule execution details."""
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize the execution preview widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create UI
        self._create_ui()
        
        # Initialize with empty preview
        self._show_empty_preview()
    
    def _create_ui(self):
        """Create the widget UI."""
        # Main container with scrollable text
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="執行預覽", font=("", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Preview text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        self.preview_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                  font=("Consolas", 9), bg="white", fg="black",
                                  padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text tags for formatting
        self.preview_text.tag_configure("header", font=("", 10, "bold"), foreground="blue")
        self.preview_text.tag_configure("subheader", font=("", 9, "bold"), foreground="darkblue")
        self.preview_text.tag_configure("info", font=("", 9), foreground="black")
        self.preview_text.tag_configure("warning", font=("", 9), foreground="orange")
        self.preview_text.tag_configure("error", font=("", 9), foreground="red")
        self.preview_text.tag_configure("success", font=("", 9), foreground="green")
    
    def _show_empty_preview(self):
        """Show empty preview message."""
        self._update_text_content([
            ("請填寫排程資訊以查看執行預覽", "info")
        ])
    
    def _update_text_content(self, content_lines: List[tuple]):
        """
        Update text content with formatting.
        
        Args:
            content_lines: List of (text, tag) tuples
        """
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        
        for text, tag in content_lines:
            self.preview_text.insert(tk.END, text + "\n", tag)
        
        self.preview_text.configure(state=tk.DISABLED)
        
        # Scroll to top
        self.preview_text.see("1.0")
    
    def update_preview(self, config: Dict[str, Any]):
        """
        Update the preview with schedule configuration.
        
        Args:
            config: Schedule configuration dictionary
        """
        try:
            content_lines = []
            
            # Header
            content_lines.append(("=== 排程執行預覽 ===", "header"))
            content_lines.append(("", "info"))
            
            # Basic information
            content_lines.append(("基本資訊:", "subheader"))
            content_lines.append((f"  排程名稱: {config['name']}", "info"))
            content_lines.append((f"  目標應用程式: {config['target_app']}", "info"))
            content_lines.append(("", "info"))
            
            # Schedule information
            self._add_schedule_info(content_lines, config.get('schedule', {}))
            
            # Conditional trigger information
            if config.get('conditional_trigger'):
                self._add_conditional_trigger_info(content_lines, config['conditional_trigger'])
            
            # Action information
            self._add_action_sequence_info(content_lines, config.get('action_sequence', []))
            
            # Options information
            self._add_options_info(content_lines, config.get('options', {}))
            
            # Execution timeline
            self._add_execution_timeline(content_lines, config)
            
            # Warnings and notes
            self._add_warnings_and_notes(content_lines, config)
            
            self._update_text_content(content_lines)
            
        except Exception as e:
            # Show error in preview
            error_lines = [
                ("預覽生成錯誤", "error"),
                ("", "info"),
                (f"錯誤詳情: {str(e)}", "error"),
                ("", "info"),
                ("請檢查配置是否正確", "warning")
            ]
            self._update_text_content(error_lines)
    
    def _add_schedule_info(self, content_lines: List[tuple], schedule_config: Dict[str, Any]):
        """Add schedule information to preview."""
        content_lines.append(("排程設定:", "subheader"))
        
        schedule_type = schedule_config.get('schedule_type')
        start_time = schedule_config.get('start_time')
        end_time = schedule_config.get('end_time')
        
        if schedule_type == ScheduleType.MANUAL.value:
            content_lines.append(("  類型: 不主動執行", "info"))
        elif schedule_type == ScheduleType.ONCE.value:
            content_lines.append(("  類型: 一次性執行", "info"))
            if start_time:
                content_lines.append((f"  執行時間: {start_time.strftime('%Y-%m-%d %H:%M')}", "info"))
        
        elif schedule_type == ScheduleType.DAILY.value:
            content_lines.append(("  類型: 每日重複", "info"))
            if start_time:
                content_lines.append((f"  每日執行時間: {start_time.strftime('%H:%M')}", "info"))
        
        elif schedule_type == ScheduleType.WEEKLY.value:
            content_lines.append(("  類型: 每週重複", "info"))
            if start_time:
                content_lines.append((f"  執行時間: {start_time.strftime('%H:%M')}", "info"))
            
            days_of_week = schedule_config.get('days_of_week', [])
            if days_of_week:
                day_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
                selected_days = [day_names[i] for i in days_of_week if 0 <= i < 7]
                content_lines.append((f"  執行日期: {', '.join(selected_days)}", "info"))
        
        elif schedule_type == ScheduleType.CUSTOM.value:
            content_lines.append(("  類型: 自訂間隔", "info"))
            if start_time:
                content_lines.append((f"  開始時間: {start_time.strftime('%Y-%m-%d %H:%M')}", "info"))
            
            interval = schedule_config.get('interval')
            if interval:
                interval_str = self._format_timedelta(interval)
                content_lines.append((f"  重複間隔: {interval_str}", "info"))
        
        if end_time:
            content_lines.append((f"  結束時間: {end_time.strftime('%Y-%m-%d %H:%M')}", "info"))
        
        content_lines.append(("", "info"))
    
    def _add_conditional_trigger_info(self, content_lines: List[tuple], trigger_config):
        """Add conditional trigger information to preview."""
        content_lines.append(("條件觸發:", "subheader"))
        
        if hasattr(trigger_config, 'condition_type'):
            condition_type = trigger_config.condition_type
            condition_value = trigger_config.condition_value
        else:
            condition_type = trigger_config.get('condition_type')
            condition_value = trigger_config.get('condition_value')
        
        condition_descriptions = {
            ConditionType.WINDOW_TITLE_CONTAINS: "視窗標題包含",
            ConditionType.WINDOW_TITLE_EQUALS: "視窗標題等於",
            ConditionType.WINDOW_EXISTS: "視窗存在",
            ConditionType.PROCESS_RUNNING: "程序運行中",
            ConditionType.TIME_RANGE: "時間範圍",
            ConditionType.SYSTEM_IDLE: "系統閒置"
        }
        
        if hasattr(condition_type, 'value'):
            condition_type_value = condition_type.value
        else:
            condition_type_value = condition_type
        
        description = condition_descriptions.get(ConditionType(condition_type_value), "未知條件")
        content_lines.append((f"  條件類型: {description}", "info"))
        content_lines.append((f"  條件值: {condition_value}", "info"))
        content_lines.append(("  註: 只有在條件滿足時才會執行動作", "warning"))
        content_lines.append(("", "info"))
    
    def _add_action_sequence_info(self, content_lines: List[tuple], action_sequence: List[Dict[str, Any]]):
        """Add action sequence information to preview."""
        content_lines.append(("執行動作:", "subheader"))
        
        if not action_sequence:
            content_lines.append(("  無動作配置", "warning"))
            content_lines.append(("", "info"))
            return
        
        action_descriptions = {
            ActionType.LAUNCH_APP: "啟動應用程式",
            ActionType.CLOSE_APP: "關閉應用程式",
            ActionType.RESIZE_WINDOW: "調整視窗大小",
            ActionType.MOVE_WINDOW: "移動視窗位置",
            ActionType.MINIMIZE_WINDOW: "最小化視窗",
            ActionType.MAXIMIZE_WINDOW: "最大化視窗",
            ActionType.RESTORE_WINDOW: "還原視窗",
            ActionType.FOCUS_WINDOW: "聚焦視窗",
            ActionType.CLICK_ELEMENT: "點擊元素",
            ActionType.TYPE_TEXT: "輸入文字",
            ActionType.SEND_KEYS: "發送按鍵",
            ActionType.CUSTOM_COMMAND: "執行自訂命令"
        }
        
        for i, action_config in enumerate(action_sequence):
            action_type = action_config.get('action_type')
            action_params = action_config.get('action_params', {})
            
            content_lines.append((f"  動作 {i + 1}:", "subheader"))
            
            # Handle both enum and string values
            if hasattr(action_type, 'value'):
                action_key = action_type
            else:
                # Try to convert string to enum
                try:
                    action_key = ActionType(action_type)
                except (ValueError, TypeError):
                    action_key = action_type
            
            description = action_descriptions.get(action_key, "未知動作")
            content_lines.append((f"    類型: {description}", "info"))
            
            # Add parameter details
            if 'app_name' in action_params:
                content_lines.append((f"    目標應用程式: {action_params['app_name']}", "info"))
            
            if 'width' in action_params and 'height' in action_params:
                content_lines.append((f"    視窗大小: {action_params['width']} x {action_params['height']}", "info"))
            
            if 'x' in action_params and 'y' in action_params:
                if action_type == ActionType.MOVE_WINDOW:
                    content_lines.append((f"    移動位置: ({action_params['x']}, {action_params['y']})", "info"))
                elif action_type in [ActionType.CLICK_ELEMENT, ActionType.TYPE_TEXT]:
                    content_lines.append((f"    操作位置: ({action_params['x']}, {action_params['y']})", "info"))
            
            if 'text' in action_params:
                content_lines.append((f"    輸入文字: \"{action_params['text']}\"", "info"))
            
            if 'keys' in action_params:
                keys_str = " + ".join(action_params['keys'])
                content_lines.append((f"    按鍵組合: {keys_str}", "info"))
            
            if 'command' in action_params:
                content_lines.append((f"    PowerShell命令:", "info"))
                content_lines.append((f"      {action_params['command']}", "info"))
            
            if i < len(action_sequence) - 1:
                content_lines.append(("", "info"))
        
        content_lines.append(("", "info"))
    
    def _add_action_info(self, content_lines: List[tuple], action_type, action_params: Dict[str, Any]):
        """Add single action information to preview (for backward compatibility)."""
        # Convert single action to sequence format
        action_sequence = [{'action_type': action_type, 'action_params': action_params}]
        self._add_action_sequence_info(content_lines, action_sequence)
    
    def _add_options_info(self, content_lines: List[tuple], options: Dict[str, Any]):
        """Add options information to preview."""
        content_lines.append(("執行選項:", "subheader"))
        
        repeat_enabled = options.get('repeat_enabled', False)
        retry_enabled = options.get('retry_enabled', False)
        notification_enabled = options.get('notification_enabled', True)
        logging_enabled = options.get('logging_enabled', True)
        
        content_lines.append((f"  重複執行: {'啟用' if repeat_enabled else '停用'}", "info"))
        content_lines.append((f"  失敗重試: {'啟用' if retry_enabled else '停用'}", "info"))
        content_lines.append((f"  執行通知: {'啟用' if notification_enabled else '停用'}", "info"))
        content_lines.append((f"  日誌記錄: {'啟用' if logging_enabled else '停用'}", "info"))
        content_lines.append(("", "info"))
    
    def _add_execution_timeline(self, content_lines: List[tuple], config: Dict[str, Any]):
        """Add execution timeline to preview."""
        content_lines.append(("執行時間軸:", "subheader"))
        
        try:
            schedule_config = config.get('schedule', {})
            schedule_type = schedule_config.get('schedule_type')
            start_time = schedule_config.get('start_time')
            
            if not start_time:
                content_lines.append(("  無法計算執行時間軸", "warning"))
                content_lines.append(("", "info"))
                return
            
            now = datetime.now()
            
            if schedule_type == ScheduleType.MANUAL.value:
                content_lines.append(("    ⚠️  此排程不會自動執行，需要手動觸發", "warning"))
            elif schedule_type == ScheduleType.ONCE.value:
                if start_time > now:
                    time_diff = start_time - now
                    content_lines.append((f"  下次執行: {start_time.strftime('%Y-%m-%d %H:%M')}", "success"))
                    content_lines.append((f"  距離執行: {self._format_timedelta(time_diff)}", "info"))
                else:
                    content_lines.append(("  執行時間已過", "warning"))
            
            else:
                # Calculate next few executions
                next_executions = self._calculate_next_executions(schedule_config, now, 3)
                
                if next_executions:
                    content_lines.append(("  接下來的執行時間:", "info"))
                    for i, exec_time in enumerate(next_executions):
                        time_diff = exec_time - now
                        status = "success" if i == 0 else "info"
                        content_lines.append((f"    {i+1}. {exec_time.strftime('%Y-%m-%d %H:%M')} "
                                           f"({self._format_timedelta(time_diff)}後)", status))
                else:
                    content_lines.append(("  無法計算下次執行時間", "warning"))
        
        except Exception:
            content_lines.append(("  執行時間軸計算錯誤", "error"))
        
        content_lines.append(("", "info"))
    
    def _add_warnings_and_notes(self, content_lines: List[tuple], config: Dict[str, Any]):
        """Add warnings and notes to preview."""
        content_lines.append(("注意事項:", "subheader"))
        
        # Check for potential issues
        action_sequence = config.get('action_sequence', [])
        if action_sequence:
            action_type = action_sequence[0].get('action_type')
            action_params = action_sequence[0].get('action_params', {})
        else:
            action_type = None
            action_params = {}
        
        # Handle both enum and string values for action_type
        if hasattr(action_type, 'value'):
            action_type_value = action_type.value
        else:
            action_type_value = action_type
        
        if action_type_value == ActionType.CUSTOM_COMMAND.value:
            content_lines.append(("  ⚠️ 自訂命令可能對系統造成影響，請謹慎使用", "warning"))
        
        # Check target app from config
        target_app = config.get('target_app', '')
        if target_app.lower() in ['cmd', 'powershell', 'regedit']:
            content_lines.append(("  ⚠️ 操作系統關鍵應用程式，請確保操作安全", "warning"))
        
        # Also check app_name in action_params
        if 'app_name' in action_params:
            app_name = action_params['app_name']
            if app_name.lower() in ['cmd', 'powershell', 'regedit']:
                content_lines.append(("  ⚠️ 操作系統關鍵應用程式，請確保操作安全", "warning"))
        
        conditional_trigger = config.get('conditional_trigger')
        if conditional_trigger:
            content_lines.append(("  ℹ️ 條件觸發啟用，實際執行時間可能與預期不同", "info"))
        
        schedule_config = config.get('schedule', {})
        if schedule_config.get('schedule_type') == ScheduleType.CUSTOM.value:
            interval = schedule_config.get('interval')
            if interval and interval.total_seconds() < 60:
                content_lines.append(("  ⚠️ 執行間隔過短可能影響系統效能", "warning"))
        
        content_lines.append(("", "info"))
        content_lines.append(("  ✓ 這是預覽模式，實際執行前請先測試", "success"))
    
    def _format_timedelta(self, td: timedelta) -> str:
        """Format timedelta for display."""
        total_seconds = int(td.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if seconds == 0:
                return f"{minutes}分鐘"
            else:
                return f"{minutes}分鐘{seconds}秒"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes == 0:
                return f"{hours}小時"
            else:
                return f"{hours}小時{minutes}分鐘"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if hours == 0:
                return f"{days}天"
            else:
                return f"{days}天{hours}小時"
    
    def _calculate_next_executions(self, schedule_config: Dict[str, Any], 
                                 from_time: datetime, count: int) -> List[datetime]:
        """Calculate next execution times."""
        try:
            from src.models.schedule import Schedule, ScheduleType
            
            # Create a temporary schedule object
            schedule_type = ScheduleType(schedule_config['schedule_type'])
            start_time = schedule_config['start_time']
            end_time = schedule_config.get('end_time')
            interval = schedule_config.get('interval')
            days_of_week = schedule_config.get('days_of_week')
            
            schedule = Schedule(
                schedule_type=schedule_type,
                start_time=start_time,
                end_time=end_time,
                interval=interval,
                days_of_week=days_of_week,
                repeat_enabled=True
            )
            
            executions = []
            current_time = from_time
            
            for _ in range(count):
                next_exec = schedule.get_next_execution(current_time)
                if next_exec is None:
                    break
                executions.append(next_exec)
                current_time = next_exec + timedelta(seconds=1)
            
            return executions
        
        except Exception:
            return []