"""
Data validation utilities for ensuring data integrity.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re


def validate_task_name(name: str) -> bool:
    """
    Validate task name.
    
    Args:
        name: Task name to validate
        
    Returns:
        bool: True if valid
    """
    if not isinstance(name, str):
        return False
    
    name = name.strip()
    if len(name) == 0 or len(name) > 100:
        return False
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    return not any(char in name for char in invalid_chars)


def validate_app_name(app_name: str) -> bool:
    """
    Validate application name.
    
    Args:
        app_name: Application name to validate
        
    Returns:
        bool: True if valid
    """
    if not isinstance(app_name, str):
        return False
    
    app_name = app_name.strip()
    return len(app_name) > 0 and len(app_name) <= 255


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format
    """
    if not isinstance(email, str):
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid URL format
    """
    if not isinstance(url, str):
        return False
    
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(url_pattern, url) is not None


def validate_time_range(start_time: datetime, end_time: Optional[datetime] = None) -> bool:
    """
    Validate time range.
    
    Args:
        start_time: Start time
        end_time: Optional end time
        
    Returns:
        bool: True if valid time range
    """
    if not isinstance(start_time, datetime):
        return False
    
    if end_time is not None:
        if not isinstance(end_time, datetime):
            return False
        return start_time < end_time
    
    return True


def validate_positive_integer(value: Any, min_value: int = 1, max_value: Optional[int] = None) -> bool:
    """
    Validate positive integer within range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value (optional)
        
    Returns:
        bool: True if valid
    """
    if not isinstance(value, int):
        return False
    
    if value < min_value:
        return False
    
    if max_value is not None and value > max_value:
        return False
    
    return True


def validate_percentage(value: Any) -> bool:
    """
    Validate percentage value (0-100).
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if valid percentage
    """
    if not isinstance(value, (int, float)):
        return False
    
    return 0.0 <= value <= 100.0


def validate_coordinates(x: Any, y: Any) -> bool:
    """
    Validate screen coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        bool: True if valid coordinates
    """
    return (
        isinstance(x, int) and isinstance(y, int) and
        x >= 0 and y >= 0 and
        x <= 10000 and y <= 10000  # Reasonable screen size limits
    )


def validate_window_dimensions(width: Any, height: Any) -> bool:
    """
    Validate window dimensions.
    
    Args:
        width: Window width
        height: Window height
        
    Returns:
        bool: True if valid dimensions
    """
    return (
        isinstance(width, int) and isinstance(height, int) and
        width > 0 and height > 0 and
        width <= 10000 and height <= 10000  # Reasonable size limits
    )


def validate_keyboard_keys(keys: List[str]) -> bool:
    """
    Validate keyboard key combinations.
    
    Args:
        keys: List of key names
        
    Returns:
        bool: True if valid key combination
    """
    if not isinstance(keys, list) or len(keys) == 0:
        return False
    
    valid_keys = {
        # Modifier keys
        'ctrl', 'alt', 'shift', 'win', 'cmd',
        # Function keys
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        # Special keys
        'enter', 'return', 'space', 'tab', 'escape', 'esc', 'backspace', 'delete', 'del',
        'home', 'end', 'pageup', 'pagedown', 'up', 'down', 'left', 'right',
        'insert', 'pause', 'printscreen', 'scrolllock', 'numlock', 'capslock',
        # Number keys
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        # Letter keys (will be checked separately)
    }
    
    for key in keys:
        if not isinstance(key, str):
            return False
        
        key_lower = key.lower().strip()
        if not key_lower:
            return False
        
        # Check if it's a valid key or a single letter
        if key_lower not in valid_keys and not (len(key_lower) == 1 and key_lower.isalpha()):
            return False
    
    return True


def validate_json_serializable(data: Any) -> bool:
    """
    Check if data is JSON serializable.
    
    Args:
        data: Data to check
        
    Returns:
        bool: True if JSON serializable
    """
    import json
    
    try:
        json.dumps(data, default=str)
        return True
    except (TypeError, ValueError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not isinstance(filename, str):
        return "untitled"
    
    # Remove invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    sanitized = filename
    
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def validate_log_retention_days(days: Any) -> bool:
    """
    Validate log retention period.
    
    Args:
        days: Number of days to validate
        
    Returns:
        bool: True if valid retention period
    """
    return validate_positive_integer(days, min_value=1, max_value=365)


def validate_retry_attempts(attempts: Any) -> bool:
    """
    Validate retry attempts count.
    
    Args:
        attempts: Number of retry attempts
        
    Returns:
        bool: True if valid retry count
    """
    return isinstance(attempts, int) and 0 <= attempts <= 10