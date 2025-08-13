"""
Action sequence widget for configuring multiple actions in a task.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Callable, List
import uuid

from src.models.action import ActionType, validate_action_params
from src.models.action_step import ActionStep
from src.gui.widgets.action_type_widget import ActionTypeWidget


class ActionSequenceWidget(ttk.Frame):
    """Widget for configuring action sequences with multiple actions."""
    
    def __init__(self, parent: tk.Widget, on_change: Optional[Callable[[], None]] = None):
        """
        Initialize the action sequence widget.
        
        Args:
            parent: Parent widget
            on_change: Callback function when configuration changes
        """
        super().__init__(parent)
        self.on_change = on_change
        self.action_widgets: List[ActionTypeWidget] = []
        self.comment_vars: List[tk.StringVar] = []
        
        # Create UI
        self._create_ui()
        
        # Add initial action
        self._add_action()
    
    def _create_ui(self):
        """Create the widget UI."""
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(header_frame, text="動作序列", font=("", 12, "bold")).pack(side=tk.LEFT)
        
        # Add action button
        add_btn = ttk.Button(header_frame, text="+ 新增動作", command=self._add_action)
        add_btn.pack(side=tk.RIGHT)

        # Add a separator to define the end of header row in grid
        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Scrollable frame for actions (maximize scrollbar by letting container consume full height)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Use grid to allow scrollbar to stretch fully
        self.canvas.grid(row=2, column=0, sticky="nsew")
        self.scrollbar.grid(row=2, column=1, sticky="ns")
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _add_action(self, config: Optional[Dict[str, Any]] = None, comment: str = ""):
        """Add a new action to the sequence."""
        action_widget = ActionTypeWidget(None, on_change=self._on_action_change)
        if config:
            action_widget.set_action(config['action_type'], config['action_params'])

        self.action_widgets.append(action_widget)
        self.comment_vars.append(tk.StringVar(value=comment))

        self._rebuild_ui()
        self._on_action_change()
    
    def _remove_action(self, index: int):
        """Remove an action from the sequence."""
        if index < len(self.action_widgets) and len(self.action_widgets) > 1:
            # Remove widget and comment var from lists
            self.action_widgets.pop(index)
            self.comment_vars.pop(index)
            
            # Rebuild the UI to update indices
            self._rebuild_ui()
            
            # Notify change
            self._on_action_change()
    
    def _move_action_up(self, index: int):
        """Move an action up in the sequence."""
        if index > 0 and index < len(self.action_widgets):
            # Swap widgets
            self.action_widgets[index], self.action_widgets[index - 1] = \
                self.action_widgets[index - 1], self.action_widgets[index]
            self.comment_vars[index], self.comment_vars[index - 1] = \
                self.comment_vars[index - 1], self.comment_vars[index]
            
            # Rebuild UI
            self._rebuild_ui()
            
            # Notify change
            self._on_action_change()
    
    def _move_action_down(self, index: int):
        """Move an action down in the sequence."""
        if index >= 0 and index < len(self.action_widgets) - 1:
            # Swap widgets
            self.action_widgets[index], self.action_widgets[index + 1] = \
                self.action_widgets[index + 1], self.action_widgets[index]
            self.comment_vars[index], self.comment_vars[index + 1] = \
                self.comment_vars[index + 1], self.comment_vars[index]
            
            # Rebuild UI
            self._rebuild_ui()
            
            # Notify change
            self._on_action_change()
    
    def _insert_action_below(self, index: int):
        """Insert a new action below the specified index."""
        new_action_widget = ActionTypeWidget(None, on_change=self._on_action_change)
        self.action_widgets.insert(index + 1, new_action_widget)
        self.comment_vars.insert(index + 1, tk.StringVar())
        self._rebuild_ui()
        self._on_action_change()

    def _rebuild_ui(self):
        """Rebuild the UI with current action widgets."""
        # Store current configurations before rebuilding
        saved_states = []
        for i, widget in enumerate(self.action_widgets):
            config = widget.get_action_config()
            comment = self.comment_vars[i].get() if i < len(self.comment_vars) else ""
            saved_states.append({'config': config, 'comment': comment})

        # Clear the scrollable frame and widget lists
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.action_widgets.clear()
        self.comment_vars.clear()

        # Recreate action frames and widgets
        for i, state in enumerate(saved_states):
            action_frame = ttk.LabelFrame(self.scrollable_frame,
                                          text=f"動作 {i + 1}",
                                          padding=10)
            action_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

            # Action controls frame
            controls_frame = ttk.Frame(action_frame)
            controls_frame.pack(fill=tk.X, pady=(0, 10))

            # Remove button
            remove_btn = ttk.Button(controls_frame, text="移除",
                                    command=self._create_remove_command(i))
            if len(saved_states) > 1:
                remove_btn.pack(side=tk.RIGHT)

            # Insert button
            insert_btn = ttk.Button(controls_frame, text="往下插入",
                                      command=self._create_insert_command(i))
            insert_btn.pack(side=tk.RIGHT, padx=(0, 5))

            # Move buttons
            if i < len(saved_states) - 1:
                down_btn = ttk.Button(controls_frame, text="↓", width=3,
                                      command=self._create_move_down_command(i))
                down_btn.pack(side=tk.RIGHT, padx=(0, 5))

            if i > 0:
                up_btn = ttk.Button(controls_frame, text="↑", width=3,
                                    command=self._create_move_up_command(i))
                up_btn.pack(side=tk.RIGHT, padx=(0, 5))

            # Create new action widget and restore its state
            action_widget = ActionTypeWidget(action_frame, on_change=self._on_action_change)
            if state['config']:
                action_widget.set_action(state['config']['action_type'], state['config']['action_params'])
            action_widget.pack(fill=tk.X)
            self.action_widgets.append(action_widget)

            # Comment field
            comment_frame = ttk.Frame(action_frame)
            comment_frame.pack(fill=tk.X, pady=(5, 0))
            ttk.Label(comment_frame, text="註解:").pack(side=tk.LEFT, anchor='nw', padx=(0, 5))
            comment_var = tk.StringVar(value=state['comment'])
            comment_entry = ttk.Entry(comment_frame, textvariable=comment_var)
            comment_entry.pack(fill=tk.X, expand=True)
            self.comment_vars.append(comment_var)

        # Update canvas scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _create_remove_command(self, index: int):
        """Create a remove command function with proper index capture."""
        def remove_command():
            self._remove_action(index)
        return remove_command
    
    def _create_move_up_command(self, index: int):
        """Create a move up command function with proper index capture."""
        def move_up_command():
            self._move_action_up(index)
        return move_up_command
    
    def _create_move_down_command(self, index: int):
        """Create a move down command function with proper index capture."""
        def move_down_command():
            self._move_action_down(index)
        return move_down_command

    def _create_insert_command(self, index: int):
        """Create an insert command function with proper index capture."""
        def insert_command():
            self._insert_action_below(index)
        return insert_command
    
    def _update_remove_buttons(self):
        """Update visibility of remove buttons."""
        # This is handled in _rebuild_ui now
        pass
    
    def _on_action_change(self):
        """Handle action change."""
        if self.on_change:
            self.on_change()
    
    def get_action_sequence_config(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the current action sequence configuration.
        
        Returns:
            List of action configurations, or None if invalid
        """
        sequence_config = []
        
        for i, widget in enumerate(self.action_widgets):
            action_config = widget.get_action_config()
            if not action_config:
                return None
            
            # Add sequence information
            action_config['sequence_order'] = i
            sequence_config.append(action_config)
        
        return sequence_config if sequence_config else None
    
    def get_action_steps(self) -> Optional[List[ActionStep]]:
        """
        Get ActionStep objects from the current configuration.
        
        Returns:
            List of ActionStep objects, or None if invalid
        """
        sequence_config = self.get_action_sequence_config()
        if not sequence_config:
            return None
        
        action_steps = []
        for i, config in enumerate(sequence_config):
            comment = self.comment_vars[i].get().strip() if i < len(self.comment_vars) else ""
            step = ActionStep.create(
                action_type=config['action_type'],
                action_params=config['action_params'],
                description=f"{config['action_type'].value} (Step {config['sequence_order'] + 1})",
                comment=comment if comment else None
            )
            action_steps.append(step)
        
        return action_steps
    
    def set_action_sequence(self, action_steps: List[ActionStep]):
        """
        Set the widget values from action steps.
        
        Args:
            action_steps: List of ActionStep objects
        """
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.action_widgets.clear()
        self.comment_vars.clear()

        if not action_steps:
            self._add_action()
            return

        # Create widgets and vars from steps
        for step in action_steps:
            action_widget = ActionTypeWidget(None, on_change=self._on_action_change)
            action_widget.set_action(step.action_type, step.action_params)
            self.action_widgets.append(action_widget)
            self.comment_vars.append(tk.StringVar(value=step.comment or ""))
        
        self._rebuild_ui()
    
    def validate(self) -> bool:
        """
        Validate the current action sequence configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.action_widgets:
            return False
        
        for widget in self.action_widgets:
            if not widget.validate():
                return False
        
        return True