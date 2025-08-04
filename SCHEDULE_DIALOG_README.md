# Schedule Dialog Implementation

This document describes the implementation of the Schedule Dialog (task 8.2) for the Windows Scheduler GUI.

## Overview

The Schedule Dialog provides a comprehensive interface for creating and editing scheduled tasks. It includes all necessary input fields and supports multiple trigger time types, conditional triggers, and dynamic action type selection.

## Components Implemented

### 1. ScheduleDialog (src/gui/dialogs/schedule_dialog.py)
Main dialog class that orchestrates all the components:
- **Tabbed interface** with 5 tabs: Basic Info, Schedule Settings, Action Settings, Options, Preview
- **Validation** of all input fields
- **Preview generation** showing execution details
- **Save/Cancel/Test** functionality

### 2. TriggerTimeWidget (src/gui/widgets/trigger_time_widget.py)
Supports multiple trigger time types:
- **Once**: Single execution at specified date/time
- **Daily**: Repeat every day at specified time
- **Weekly**: Repeat on selected days of the week
- **Custom**: Repeat at custom intervals (minutes/hours/days)
- **End time** configuration (optional)

### 3. ConditionalTriggerWidget (src/gui/widgets/conditional_trigger_widget.py)
Supports conditional execution based on:
- **Window title contains**: Execute when any window title contains specified text
- **Window title equals**: Execute when window title exactly matches
- **Window exists**: Execute when specified application window exists
- **Process running**: Execute when specified process is running
- **Time range**: Execute only within specified time range (HH:MM-HH:MM)
- **System idle**: Execute when system has been idle for specified minutes

### 4. ActionTypeWidget (src/gui/widgets/action_type_widget.py)
Dynamic interface for all action types:
- **Launch/Close App**: Application name input
- **Resize Window**: Width and height parameters
- **Move Window**: X and Y coordinates
- **Window Controls**: Minimize, maximize, restore, focus
- **Click Element**: Application name and click coordinates
- **Type Text**: Application name, text input, and position
- **Send Keys**: Comma-separated key combinations
- **Custom Command**: PowerShell command input

### 5. ExecutionPreviewWidget (src/gui/widgets/execution_preview_widget.py)
Real-time preview showing:
- **Basic information**: Schedule name and target application
- **Schedule details**: Type, timing, and repetition settings
- **Conditional triggers**: If enabled, shows condition details
- **Action details**: Action type and all parameters
- **Execution options**: Repeat, retry, notifications, logging
- **Timeline**: Next execution times and intervals
- **Warnings**: Potential issues and safety notes

## Integration Points

### Control Buttons Widget
Updated `src/gui/widgets/control_buttons_widget.py`:
- **New Task** button now opens ScheduleDialog for creation
- **Edit Task** button now opens ScheduleDialog for editing
- Added `_on_task_saved()` method to handle task persistence

### Schedules Page
Updated `src/gui/pages/schedules_page.py`:
- **Edit from detail** functionality now uses ScheduleDialog
- Added task saving integration with TaskManager

## Usage Examples

### Creating a New Task
```python
from src.gui.dialogs.schedule_dialog import ScheduleDialog

def create_task():
    dialog = ScheduleDialog(parent_widget, on_save=handle_task_save)
    result = dialog.show()
    if result:
        print(f"Created task: {result.name}")

def handle_task_save(task):
    task_manager.create_task(task)
```

### Editing an Existing Task
```python
def edit_task(existing_task):
    dialog = ScheduleDialog(parent_widget, task=existing_task, on_save=handle_task_save)
    result = dialog.show()
    if result:
        print(f"Updated task: {result.name}")

def handle_task_save(task):
    task_manager.update_task(task.id, task)
```

## Features

### Validation
- **Real-time validation** of all input fields
- **Parameter validation** using existing ActionType validation
- **Schedule validation** ensuring valid dates and times
- **Conditional trigger validation** with format checking

### User Experience
- **Tabbed interface** for organized input
- **Real-time preview** updates as user types
- **Help text** and tooltips for guidance
- **Test functionality** to preview without saving
- **Responsive layout** that adapts to window size

### Error Handling
- **Graceful error handling** with user-friendly messages
- **Validation feedback** before allowing save
- **Exception handling** in all operations

## Requirements Satisfied

This implementation satisfies the following requirements from the task:

✅ **3.1**: Task creation and editing interface
✅ **3.2**: Schedule configuration with multiple types
✅ **3.3**: Action type selection and parameter input
✅ **3.4**: Task validation and confirmation
✅ **3.5**: User-friendly interface with clear feedback

## Testing

A minimal test script is provided (`test_dialog_minimal.py`) to verify:
- All imports work correctly
- Components can be instantiated
- Basic functionality is available

## Future Enhancements

Potential improvements for future versions:
- **Date/time pickers** instead of text input
- **Application browser** to select target applications
- **Drag-and-drop** for click coordinates
- **Schedule templates** for common patterns
- **Import/export** of task configurations