"""
Action type definitions for Windows operations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class ActionType(Enum):
    """Enumeration of available Windows control actions."""
    
    # 應用程式控制
    LAUNCH_APP = "launch_app"              # 啟動指定的應用程式
    CLOSE_APP = "close_app"                # 關閉指定的應用程式
    SWITCH_APP = "switch_app"              # 切換到指定應用程式 (等同 FOCUS_WINDOW)
    
    # 視窗操作
    RESIZE_WINDOW = "resize_window"        # 調整視窗大小到指定尺寸
    MOVE_WINDOW = "move_window"            # 移動視窗到指定位置
    MINIMIZE_WINDOW = "minimize_window"    # 最小化視窗
    MAXIMIZE_WINDOW = "maximize_window"    # 最大化視窗
    RESTORE_WINDOW = "restore_window"      # 還原視窗到正常大小
    FOCUS_WINDOW = "focus_window"          # 將視窗帶到前景
    
    # 滑鼠操作
    CLICK_ABS = "click_abs"                # 點擊螢幕絕對座標
    DRAG_ELEMENT = "drag_element"          # 拖拽操作從源座標到目標座標
    MOVE_MOUSE = "move_mouse"              # 移動滑鼠到指定位置
    SCROLL = "scroll"                      # 滾動操作 (垂直/水平)
    
    # 鍵盤操作
    TYPE_TEXT = "type_text"                # 在指定位置輸入文字
    SEND_KEYS = "send_keys"                # 發送鍵盤快捷鍵
    PRESS_KEY = "press_key"                # 按下單一按鍵
    
    # 剪貼簿操作
    CLIPBOARD_COPY = "clipboard_copy"      # 複製文字到剪貼簿
    CLIPBOARD_PASTE = "clipboard_paste"    # 從剪貼簿貼上文字
    
    # 系統操作
    GET_DESKTOP_STATE = "get_desktop_state" # 獲取桌面狀態資訊
    WAIT = "wait"                          # 等待指定時間
    SCRAPE_WEBPAGE = "scrape_webpage"      # 抓取網頁內容
    CUSTOM_COMMAND = "custom_command"      # 執行自訂PowerShell命令


@dataclass
class ActionParams:
    """Base class for action parameters."""
    pass


@dataclass
class LaunchAppParams(ActionParams):
    """Parameters for launching an application."""
    app_name: str


@dataclass
class CloseAppParams(ActionParams):
    """Parameters for closing an application."""
    app_name: str


@dataclass
class ResizeWindowParams(ActionParams):
    """Parameters for resizing a window."""
    app_name: str
    width: int
    height: int


@dataclass
class MoveWindowParams(ActionParams):
    """Parameters for moving a window."""
    app_name: str
    x: int
    y: int


@dataclass
class WindowControlParams(ActionParams):
    """Parameters for basic window control operations."""
    app_name: str


@dataclass
class ClickElementParams(ActionParams):
    """Parameters for clicking an element."""
    x: int
    y: int


@dataclass
class TypeTextParams(ActionParams):
    """Parameters for typing text."""
    app_name: str
    text: str
    x: int
    y: int


@dataclass
class SendKeysParams(ActionParams):
    """Parameters for sending keyboard shortcuts."""
    keys: List[str]


@dataclass
class CustomCommandParams(ActionParams):
    """Parameters for custom PowerShell commands."""
    command: str


@dataclass
class DragElementParams(ActionParams):
    """Parameters for drag and drop operations."""
    app_name: str
    from_x: int
    from_y: int
    to_x: int
    to_y: int


@dataclass
class MoveMouseParams(ActionParams):
    """Parameters for mouse movement."""
    x: int
    y: int


@dataclass
class ScrollParams(ActionParams):
    """Parameters for scroll operations."""
    app_name: str
    x: int = 0
    y: int = 0
    direction: str = "down"  # up, down, left, right
    scroll_type: str = "vertical"  # vertical, horizontal
    wheel_times: int = 1


@dataclass
class PressKeyParams(ActionParams):
    """Parameters for single key press."""
    key: str


@dataclass
class ClipboardCopyParams(ActionParams):
    """Parameters for clipboard copy operation."""
    text: str


@dataclass
class ClipboardPasteParams(ActionParams):
    """Parameters for clipboard paste operation."""
    app_name: str
    x: int = 0
    y: int = 0


@dataclass
class GetDesktopStateParams(ActionParams):
    """Parameters for getting desktop state."""
    use_vision: bool = False


@dataclass
class WaitParams(ActionParams):
    """Parameters for wait operation."""
    duration: int  # seconds


@dataclass
class ScrapeWebpageParams(ActionParams):
    """Parameters for webpage scraping."""
    url: str


def validate_action_params(action_type: ActionType, params: Dict[str, Any]) -> bool:
    """
    Validate action parameters for the given action type.
    
    Args:
        action_type: The type of action to validate
        params: Dictionary of parameters to validate
        
    Returns:
        bool: True if parameters are valid, False otherwise
    """
    try:
        if action_type == ActionType.LAUNCH_APP:
            return _validate_launch_app_params(params)
        elif action_type == ActionType.CLOSE_APP:
            return _validate_close_app_params(params)
        elif action_type == ActionType.RESIZE_WINDOW:
            return _validate_resize_window_params(params)
        elif action_type == ActionType.MOVE_WINDOW:
            return _validate_move_window_params(params)
        elif action_type in [ActionType.MINIMIZE_WINDOW, ActionType.MAXIMIZE_WINDOW,
                           ActionType.RESTORE_WINDOW, ActionType.FOCUS_WINDOW]:
            return _validate_window_control_params(params)
        elif action_type == ActionType.CLICK_ABS:
            return _validate_click_element_params(params)
        elif action_type == ActionType.TYPE_TEXT:
            return _validate_type_text_params(params)
        elif action_type == ActionType.SEND_KEYS:
            return _validate_send_keys_params(params)
        elif action_type == ActionType.CUSTOM_COMMAND:
            return _validate_custom_command_params(params)
        elif action_type == ActionType.DRAG_ELEMENT:
            return _validate_drag_element_params(params)
        elif action_type == ActionType.MOVE_MOUSE:
            return _validate_move_mouse_params(params)
        elif action_type == ActionType.SCROLL:
            return _validate_scroll_params(params)
        elif action_type == ActionType.PRESS_KEY:
            return _validate_press_key_params(params)
        elif action_type == ActionType.CLIPBOARD_COPY:
            return _validate_clipboard_copy_params(params)
        elif action_type == ActionType.CLIPBOARD_PASTE:
            return _validate_clipboard_paste_params(params)
        elif action_type == ActionType.GET_DESKTOP_STATE:
            return _validate_get_desktop_state_params(params)
        elif action_type == ActionType.WAIT:
            return _validate_wait_params(params)
        elif action_type == ActionType.SCRAPE_WEBPAGE:
            return _validate_scrape_webpage_params(params)
        elif action_type == ActionType.SWITCH_APP:
            return _validate_close_app_params(params)  # Same as close_app validation
        else:
            return False
    except (KeyError, TypeError, ValueError):
        return False


def _validate_launch_app_params(params: Dict[str, Any]) -> bool:
    """Validate launch app parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_close_app_params(params: Dict[str, Any]) -> bool:
    """Validate close app parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_resize_window_params(params: Dict[str, Any]) -> bool:
    """Validate resize window parameters."""
    return (
        'app_name' in params and
        'width' in params and
        'height' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['width'], int) and
        isinstance(params['height'], int) and
        len(params['app_name'].strip()) > 0 and
        params['width'] > 0 and
        params['height'] > 0
    )


def _validate_move_window_params(params: Dict[str, Any]) -> bool:
    """Validate move window parameters."""
    return (
        'app_name' in params and
        'x' in params and
        'y' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        len(params['app_name'].strip()) > 0 and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_window_control_params(params: Dict[str, Any]) -> bool:
    """Validate basic window control parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_click_element_params(params: Dict[str, Any]) -> bool:
    """Validate click element parameters."""
    return (
        'x' in params and
        'y' in params and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_type_text_params(params: Dict[str, Any]) -> bool:
    """Validate type text parameters."""
    return (
        'app_name' in params and
        'text' in params and
        'x' in params and
        'y' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['text'], str) and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        len(params['app_name'].strip()) > 0 and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_send_keys_params(params: Dict[str, Any]) -> bool:
    """Validate send keys parameters."""
    if not ('keys' in params and isinstance(params['keys'], list) and len(params['keys']) > 0):
        return False
    
    # Valid key names for Windows
    valid_keys = {
        'ctrl', 'alt', 'shift', 'win', 'tab', 'enter', 'space', 'backspace',
        'delete', 'home', 'end', 'pageup', 'pagedown', 'insert', 'escape',
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        'up', 'down', 'left', 'right', 'numlock', 'capslock', 'scrolllock',
        'printscreen', 'pause', 'menu'
    }
    
    # Also allow single characters and numbers
    for key in params['keys']:
        if not isinstance(key, str) or len(key.strip()) == 0:
            return False
        
        key_lower = key.lower().strip()
        
        # Check if it's a valid special key
        if key_lower in valid_keys:
            continue
        
        # Check if it's a single character (a-z, 0-9)
        if len(key_lower) == 1 and (key_lower.isalnum() or key_lower in '`-=[]\\;\',./'):
            continue
        
        # Invalid key
        return False
    
    return True


def _validate_custom_command_params(params: Dict[str, Any]) -> bool:
    """Validate custom command parameters."""
    return (
        'command' in params and
        isinstance(params['command'], str) and
        len(params['command'].strip()) > 0
    )


def _validate_drag_element_params(params: Dict[str, Any]) -> bool:
    """Validate drag element parameters."""
    required_fields = ['app_name', 'from_x', 'from_y', 'to_x', 'to_y']
    return (
        all(field in params for field in required_fields) and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0 and
        all(isinstance(params[field], int) for field in ['from_x', 'from_y', 'to_x', 'to_y'])
    )


def _validate_move_mouse_params(params: Dict[str, Any]) -> bool:
    """Validate move mouse parameters."""
    return (
        'x' in params and 'y' in params and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        params['x'] >= 0 and params['y'] >= 0
    )


def _validate_scroll_params(params: Dict[str, Any]) -> bool:
    """Validate scroll parameters."""
    valid_directions = ['up', 'down', 'left', 'right']
    valid_types = ['vertical', 'horizontal']
    
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0 and
        params.get('direction', 'down') in valid_directions and
        params.get('scroll_type', 'vertical') in valid_types and
        isinstance(params.get('wheel_times', 1), int) and
        params.get('wheel_times', 1) > 0
    )


def _validate_press_key_params(params: Dict[str, Any]) -> bool:
    """Validate press key parameters."""
    if 'key' not in params or not isinstance(params['key'], str):
        return False
    
    key = params['key'].strip().lower()
    if len(key) == 0:
        return False
    
    # Valid special keys
    valid_keys = {
        'enter', 'space', 'tab', 'escape', 'backspace', 'delete',
        'home', 'end', 'pageup', 'pagedown', 'insert',
        'up', 'down', 'left', 'right',
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        'numlock', 'capslock', 'scrolllock', 'printscreen', 'pause'
    }
    
    # Allow single characters or valid special keys
    return len(key) == 1 or key in valid_keys


def _validate_clipboard_copy_params(params: Dict[str, Any]) -> bool:
    """Validate clipboard copy parameters."""
    return (
        'text' in params and
        isinstance(params['text'], str)
    )


def _validate_clipboard_paste_params(params: Dict[str, Any]) -> bool:
    """Validate clipboard paste parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_get_desktop_state_params(params: Dict[str, Any]) -> bool:
    """Validate get desktop state parameters."""
    # use_vision is optional, defaults to False
    return isinstance(params.get('use_vision', False), bool)


def _validate_wait_params(params: Dict[str, Any]) -> bool:
    """Validate wait parameters."""
    return (
        'duration' in params and
        isinstance(params['duration'], int) and
        params['duration'] > 0
    )


def _validate_scrape_webpage_params(params: Dict[str, Any]) -> bool:
    """Validate scrape webpage parameters."""
    if 'url' not in params or not isinstance(params['url'], str):
        return False
    
    url = params['url'].strip()
    return len(url) > 0 and (url.startswith('http://') or url.startswith('https://'))