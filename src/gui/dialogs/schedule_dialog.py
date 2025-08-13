"""
Schedule creation and editing dialog.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
import uuid

from src.models.task import Task, TaskStatus
from src.models.schedule import Schedule, ScheduleType, ConditionalTrigger, ConditionType
from src.models.action import ActionType, validate_action_params
from src.gui.widgets.trigger_time_widget import TriggerTimeWidget
from src.gui.widgets.conditional_trigger_widget import ConditionalTriggerWidget
from src.gui.widgets.action_type_widget import ActionTypeWidget
from src.gui.widgets.action_sequence_widget import ActionSequenceWidget
from src.gui.widgets.execution_preview_widget import ExecutionPreviewWidget


class ScheduleDialog:
    """Dialog for creating and editing schedules."""
    
    def __init__(self, parent: tk.Widget, task: Optional[Task] = None, 
                 on_save: Optional[Callable[[Task], None]] = None):
        """
        Initialize the schedule dialog.
        
        Args:
            parent: Parent widget
            task: Task to edit (None for new task)
            on_save: Callback function when task is saved
        """
        self.parent = parent
        self.task = task
        self.on_save = on_save
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("建立排程" if task is None else "編輯排程")
        self.dialog.geometry("1000x800")
        self.dialog.minsize(900, 700)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self._center_dialog()
        
        # Initialize widgets
        self.schedule_name_var = tk.StringVar()
        
        # Widget references
        self.trigger_time_widget: Optional[TriggerTimeWidget] = None
        self.conditional_trigger_widget: Optional[ConditionalTriggerWidget] = None
        self.action_type_widget: Optional[ActionTypeWidget] = None
        self.action_sequence_widget: Optional[ActionSequenceWidget] = None
        self.execution_preview_widget: Optional[ExecutionPreviewWidget] = None
        
        # Options variables
        self.repeat_enabled_var = tk.BooleanVar()
        self.retry_enabled_var = tk.BooleanVar()
        self.notification_enabled_var = tk.BooleanVar(value=True)
        self.logging_enabled_var = tk.BooleanVar(value=True)
        
        # Create UI
        self._create_ui()
        
        # Load task data if editing
        if self.task:
            self._load_task_data()
        
        # Bind events
        self._bind_events()
        
        # Update preview initially
        self._update_preview()
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # Get dialog dimensions
        dialog_width = 1000
        dialog_height = 800
        
        # Calculate center position on screen
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        # Ensure dialog is not positioned off-screen
        x = max(0, x)
        y = max(0, y)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _create_ui(self):
        """Create the dialog UI."""
        # Main container with scrollable frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for organized sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic Information Tab
        self._create_basic_info_tab()
        
        # Schedule Settings Tab
        self._create_schedule_tab()
        
        # Action Settings Tab
        self._create_action_tab()
        
        # Options Tab
        self._create_options_tab()
        
        # Preview Tab
        self._create_preview_tab()
        
        # Button frame
        self._create_button_frame(main_frame)
    
    def _create_basic_info_tab(self):
        """Create the basic information tab."""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="基本資訊")
        
        # Schedule name
        name_frame = ttk.LabelFrame(basic_frame, text="排程名稱", padding=10)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="名稱:").pack(anchor=tk.W)
        name_entry = ttk.Entry(name_frame, textvariable=self.schedule_name_var, font=("", 10))
        name_entry.pack(fill=tk.X, pady=(5, 0))
    
    def _create_schedule_tab(self):
        """Create the schedule settings tab."""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="排程設定")
        
        # Create scrollable frame for schedule tab
        canvas = tk.Canvas(schedule_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(schedule_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Trigger time widget
        trigger_frame = ttk.LabelFrame(scrollable_frame, text="觸發時間", padding=10)
        trigger_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        self.trigger_time_widget = TriggerTimeWidget(trigger_frame, 
                                                   on_change=self._update_preview)
        self.trigger_time_widget.pack(fill=tk.X)
        
        # Conditional trigger widget
        condition_frame = ttk.LabelFrame(scrollable_frame, text="條件觸發", padding=10)
        condition_frame.pack(fill=tk.X, padx=10)
        
        self.conditional_trigger_widget = ConditionalTriggerWidget(condition_frame,
                                                                 on_change=self._update_preview)
        self.conditional_trigger_widget.pack(fill=tk.X)
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _create_action_tab(self):
        """Create the action settings tab."""
        action_frame = ttk.Frame(self.notebook)
        self.notebook.add(action_frame, text="動作設定")
        
        # Place action sequence widget directly and let it manage its own scroll to maximize available space
        self.action_sequence_widget = ActionSequenceWidget(action_frame, 
                                                          on_change=self._update_preview)
        self.action_sequence_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_options_tab(self):
        """Create the options tab."""
        options_frame = ttk.Frame(self.notebook)
        self.notebook.add(options_frame, text="選項")
        
        # Repeat options
        repeat_frame = ttk.LabelFrame(options_frame, text="重複選項", padding=10)
        repeat_frame.pack(fill=tk.X, pady=(0, 10))
        
        repeat_check = ttk.Checkbutton(repeat_frame, text="啟用重複執行", 
                                     variable=self.repeat_enabled_var,
                                     command=self._update_preview)
        repeat_check.pack(anchor=tk.W)
        
        # Retry options
        retry_frame = ttk.LabelFrame(options_frame, text="重試選項", padding=10)
        retry_frame.pack(fill=tk.X, pady=(0, 10))
        
        retry_check = ttk.Checkbutton(retry_frame, text="失敗時自動重試", 
                                    variable=self.retry_enabled_var,
                                    command=self._update_preview)
        retry_check.pack(anchor=tk.W)
        
        # Notification options
        notification_frame = ttk.LabelFrame(options_frame, text="通知選項", padding=10)
        notification_frame.pack(fill=tk.X, pady=(0, 10))
        
        notification_check = ttk.Checkbutton(notification_frame, text="顯示執行通知", 
                                           variable=self.notification_enabled_var,
                                           command=self._update_preview)
        notification_check.pack(anchor=tk.W)
        
        # Logging options
        logging_frame = ttk.LabelFrame(options_frame, text="日誌選項", padding=10)
        logging_frame.pack(fill=tk.X)
        
        logging_check = ttk.Checkbutton(logging_frame, text="記錄執行日誌", 
                                      variable=self.logging_enabled_var,
                                      command=self._update_preview)
        logging_check.pack(anchor=tk.W)
    
    def _create_preview_tab(self):
        """Create the preview tab."""
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="執行預覽")
        
        # Execution preview widget
        self.execution_preview_widget = ExecutionPreviewWidget(preview_frame)
        self.execution_preview_widget.pack(fill=tk.BOTH, expand=True)
    
    def _create_button_frame(self, parent: tk.Widget):
        """Create the button frame."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="取消", command=self._on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Save button
        save_btn = ttk.Button(button_frame, text="儲存", command=self._on_save)
        save_btn.pack(side=tk.RIGHT)
        
        # Test button
        test_btn = ttk.Button(button_frame, text="測試", command=self._on_test)
        test_btn.pack(side=tk.RIGHT, padx=(0, 5))
    
    def _bind_events(self):
        """Bind dialog events."""
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Bind variable changes to update preview
        self.schedule_name_var.trace_add("write", lambda *args: self._update_preview())
    
    def _load_task_data(self):
        """Load task data into the dialog."""
        if not self.task:
            return
        
        # Load basic info
        self.schedule_name_var.set(self.task.name)
        
        # Load schedule settings
        if self.trigger_time_widget:
            self.trigger_time_widget.set_schedule(self.task.schedule)
        
        if self.conditional_trigger_widget and self.task.schedule.conditional_trigger:
            self.conditional_trigger_widget.set_trigger(self.task.schedule.conditional_trigger)
        
        # Load action settings
        if self.action_sequence_widget:
            # Load action sequence
            if hasattr(self.task, 'action_sequence') and self.task.action_sequence:
                self.action_sequence_widget.set_action_sequence(self.task.action_sequence)
            elif hasattr(self.task, 'action_type'):
                # Old format - convert to action sequence
                from src.models.action_step import ActionStep
                action_step = ActionStep.create(
                    action_type=self.task.action_type,
                    action_params=getattr(self.task, 'action_params', {}),
                    description=f"{self.task.action_type.value} on {self.task.target_app}"
                )
                self.action_sequence_widget.set_action_sequence([action_step])
        
        # Load options
        self.repeat_enabled_var.set(self.task.schedule.repeat_enabled)
        # Note: retry, notification, and logging options would need to be stored in task model
    
    def _update_preview(self):
        """Update the execution preview."""
        if not self.execution_preview_widget:
            return
        
        try:
            # Get current configuration
            config = self._get_schedule_config()
            if config:
                self.execution_preview_widget.update_preview(config)
        except Exception as e:
            # Handle preview update errors silently
            pass
    
    def _get_schedule_config(self) -> Optional[Dict[str, Any]]:
        """Get the current schedule configuration."""
        try:
            # Basic info
            name = self.schedule_name_var.get().strip()
            
            if not name:
                return None
            
            # Schedule settings
            schedule_config = None
            if self.trigger_time_widget:
                schedule_config = self.trigger_time_widget.get_schedule_config()
            
            if not schedule_config:
                return None
            
            # Conditional trigger
            conditional_trigger = None
            if self.conditional_trigger_widget:
                conditional_trigger = self.conditional_trigger_widget.get_trigger_config()
            
            # Action settings
            action_sequence_config = None
            if self.action_sequence_widget:
                action_sequence_config = self.action_sequence_widget.get_action_sequence_config()
            
            if not action_sequence_config:
                return None
            
            # Get target app from first action that has app_name parameter
            target_app = "未指定"
            for action_config in action_sequence_config:
                if 'app_name' in action_config.get('action_params', {}):
                    target_app = action_config['action_params']['app_name']
                    break
            
            return {
                'name': name,
                'target_app': target_app,
                'schedule': schedule_config,
                'conditional_trigger': conditional_trigger,
                'action_sequence': action_sequence_config,
                'options': {
                    'repeat_enabled': self.repeat_enabled_var.get(),
                    'retry_enabled': self.retry_enabled_var.get(),
                    'notification_enabled': self.notification_enabled_var.get(),
                    'logging_enabled': self.logging_enabled_var.get()
                }
            }
        except Exception:
            return None
    
    def _validate_schedule(self) -> bool:
        """Validate the schedule configuration."""
        config = self._get_schedule_config()
        if not config:
            messagebox.showerror("驗證錯誤", "請填寫所有必要欄位")
            return False
        
        # Validate action sequence
        for action_config in config['action_sequence']:
            if not validate_action_params(action_config['action_type'], action_config['action_params']):
                messagebox.showerror("驗證錯誤", f"動作參數無效: {action_config['action_type'].value}")
                return False
        
        return True
    
    def _create_task_from_config(self) -> Optional[Task]:
        """Create a Task object from the current configuration."""
        config = self._get_schedule_config()
        if not config:
            return None
        
        try:
            # Create schedule
            schedule_config = config['schedule']
            schedule = Schedule(
                schedule_type=ScheduleType(schedule_config['schedule_type']),
                start_time=schedule_config['start_time'],
                end_time=schedule_config.get('end_time'),
                interval=schedule_config.get('interval'),
                days_of_week=schedule_config.get('days_of_week'),
                repeat_enabled=config['options']['repeat_enabled'],
                conditional_trigger=config.get('conditional_trigger')
            )
            
            # Create action sequence from config
            from src.models.action_step import ActionStep, ExecutionOptions
            
            action_steps = []
            for action_config in config['action_sequence']:
                action_step = ActionStep.create(
                    action_type=action_config['action_type'],
                    action_params=action_config['action_params'],
                    description=f"{action_config['action_type'].value} on {config['target_app']}"
                )
                action_steps.append(action_step)
            
            # Create or update task
            if self.task:
                # Update existing task
                self.task.name = config['name']
                self.task.target_app = config['target_app']
                self.task.action_sequence = action_steps
                if not hasattr(self.task, 'execution_options'):
                    self.task.execution_options = ExecutionOptions.get_default()
                self.task.schedule = schedule
                task = self.task
            else:
                # Create new task
                task = Task(
                    id=str(uuid.uuid4()),
                    name=config['name'],
                    target_app=config['target_app'],
                    action_sequence=action_steps,
                    schedule=schedule,
                    status=TaskStatus.PENDING,
                    execution_options=ExecutionOptions.get_default(),
                    created_at=datetime.now()
                )
            
            # Update next execution time
            task.update_next_execution()
            
            return task
        except Exception as e:
            messagebox.showerror("建立任務錯誤", f"無法建立任務: {str(e)}")
            return None
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate_schedule():
            return
        
        task = self._create_task_from_config()
        if not task:
            return
        
        self.result = task
        
        # Call save callback if provided
        if self.on_save:
            try:
                self.on_save(task)
            except Exception as e:
                messagebox.showerror("儲存錯誤", f"儲存任務時發生錯誤: {str(e)}")
                return
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.dialog.destroy()
    
    def _on_test(self):
        """Handle test button click."""
        if not self._validate_schedule():
            return
        
        config = self._get_schedule_config()
        if config:
            # Show test information
            action_info = []
            for i, action_config in enumerate(config['action_sequence']):
                action_info.append(f"動作 {i+1}: {action_config['action_type'].value}")
                action_info.append(f"  參數: {action_config['action_params']}")
            
            test_info = f"""
測試配置:
排程名稱: {config['name']}
目標應用程式: {config['target_app']}
動作序列:
{chr(10).join(action_info)}

注意: 這是測試模式，不會實際執行動作。
            """
            messagebox.showinfo("測試配置", test_info.strip())
    
    def show(self) -> Optional[Task]:
        """
        Show the dialog and return the result.
        
        Returns:
            Task object if saved, None if cancelled
        """
        self.dialog.wait_window()
        return self.result