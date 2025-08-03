"""
Factory for creating and validating action parameters.
"""

from typing import Dict, Any, Optional, Type
from .action import (
    ActionType, ActionParams, LaunchAppParams, CloseAppParams,
    ResizeWindowParams, MoveWindowParams, WindowControlParams,
    ClickElementParams, TypeTextParams, SendKeysParams, CustomCommandParams,
    validate_action_params
)


class ActionParamsFactory:
    """Factory for creating typed action parameter objects."""
    
    @staticmethod
    def create_params(action_type: ActionType, params: Dict[str, Any]) -> Optional[ActionParams]:
        """
        Create typed action parameters from a dictionary.
        
        Args:
            action_type: The type of action
            params: Dictionary of parameters
            
        Returns:
            ActionParams object if valid, None otherwise
        """
        if not validate_action_params(action_type, params):
            return None
        
        try:
            if action_type == ActionType.LAUNCH_APP:
                return LaunchAppParams(app_name=params['app_name'])
            
            elif action_type == ActionType.CLOSE_APP:
                return CloseAppParams(app_name=params['app_name'])
            
            elif action_type == ActionType.RESIZE_WINDOW:
                return ResizeWindowParams(
                    app_name=params['app_name'],
                    width=params['width'],
                    height=params['height']
                )
            
            elif action_type == ActionType.MOVE_WINDOW:
                return MoveWindowParams(
                    app_name=params['app_name'],
                    x=params['x'],
                    y=params['y']
                )
            
            elif action_type in [ActionType.MINIMIZE_WINDOW, ActionType.MAXIMIZE_WINDOW,
                               ActionType.RESTORE_WINDOW, ActionType.FOCUS_WINDOW]:
                return WindowControlParams(app_name=params['app_name'])
            
            elif action_type == ActionType.CLICK_ELEMENT:
                return ClickElementParams(
                    app_name=params['app_name'],
                    x=params['x'],
                    y=params['y']
                )
            
            elif action_type == ActionType.TYPE_TEXT:
                return TypeTextParams(
                    app_name=params['app_name'],
                    text=params['text'],
                    x=params['x'],
                    y=params['y']
                )
            
            elif action_type == ActionType.SEND_KEYS:
                return SendKeysParams(keys=params['keys'])
            
            elif action_type == ActionType.CUSTOM_COMMAND:
                return CustomCommandParams(command=params['command'])
            
            else:
                return None
                
        except (KeyError, TypeError, ValueError):
            return None
    
    @staticmethod
    def get_required_params(action_type: ActionType) -> Dict[str, Type]:
        """
        Get the required parameters for an action type.
        
        Args:
            action_type: The type of action
            
        Returns:
            Dictionary mapping parameter names to their expected types
        """
        param_specs = {
            ActionType.LAUNCH_APP: {'app_name': str},
            ActionType.CLOSE_APP: {'app_name': str},
            ActionType.RESIZE_WINDOW: {'app_name': str, 'width': int, 'height': int},
            ActionType.MOVE_WINDOW: {'app_name': str, 'x': int, 'y': int},
            ActionType.MINIMIZE_WINDOW: {'app_name': str},
            ActionType.MAXIMIZE_WINDOW: {'app_name': str},
            ActionType.RESTORE_WINDOW: {'app_name': str},
            ActionType.FOCUS_WINDOW: {'app_name': str},
            ActionType.CLICK_ELEMENT: {'app_name': str, 'x': int, 'y': int},
            ActionType.TYPE_TEXT: {'app_name': str, 'text': str, 'x': int, 'y': int},
            ActionType.SEND_KEYS: {'keys': list},
            ActionType.CUSTOM_COMMAND: {'command': str},
        }
        
        return param_specs.get(action_type, {})
    
    @staticmethod
    def get_param_description(action_type: ActionType) -> Dict[str, str]:
        """
        Get human-readable descriptions for action parameters.
        
        Args:
            action_type: The type of action
            
        Returns:
            Dictionary mapping parameter names to their descriptions
        """
        descriptions = {
            ActionType.LAUNCH_APP: {
                'app_name': '要啟動的應用程式名稱（例如：notepad, calculator）'
            },
            ActionType.CLOSE_APP: {
                'app_name': '要關閉的應用程式名稱'
            },
            ActionType.RESIZE_WINDOW: {
                'app_name': '要調整大小的應用程式名稱',
                'width': '新的視窗寬度（像素）',
                'height': '新的視窗高度（像素）'
            },
            ActionType.MOVE_WINDOW: {
                'app_name': '要移動的應用程式名稱',
                'x': '新的X座標位置',
                'y': '新的Y座標位置'
            },
            ActionType.MINIMIZE_WINDOW: {
                'app_name': '要最小化的應用程式名稱'
            },
            ActionType.MAXIMIZE_WINDOW: {
                'app_name': '要最大化的應用程式名稱'
            },
            ActionType.RESTORE_WINDOW: {
                'app_name': '要還原的應用程式名稱'
            },
            ActionType.FOCUS_WINDOW: {
                'app_name': '要聚焦的應用程式名稱'
            },
            ActionType.CLICK_ELEMENT: {
                'app_name': '目標應用程式名稱',
                'x': '點擊位置的X座標',
                'y': '點擊位置的Y座標'
            },
            ActionType.TYPE_TEXT: {
                'app_name': '目標應用程式名稱',
                'text': '要輸入的文字內容',
                'x': '輸入位置的X座標',
                'y': '輸入位置的Y座標'
            },
            ActionType.SEND_KEYS: {
                'keys': '要發送的按鍵組合列表（例如：["ctrl", "c"]）'
            },
            ActionType.CUSTOM_COMMAND: {
                'command': '要執行的PowerShell命令'
            }
        }
        
        return descriptions.get(action_type, {})
    
    @staticmethod
    def validate_and_create(action_type: ActionType, params: Dict[str, Any]) -> tuple[bool, Optional[ActionParams], str]:
        """
        Validate parameters and create action params object with detailed error message.
        
        Args:
            action_type: The type of action
            params: Dictionary of parameters
            
        Returns:
            Tuple of (is_valid, params_object, error_message)
        """
        # Check if action type is valid
        if not isinstance(action_type, ActionType):
            return False, None, "無效的動作類型"
        
        # Get required parameters
        required_params = ActionParamsFactory.get_required_params(action_type)
        
        # Check for missing parameters
        missing_params = []
        for param_name, param_type in required_params.items():
            if param_name not in params:
                missing_params.append(param_name)
        
        if missing_params:
            return False, None, f"缺少必要參數: {', '.join(missing_params)}"
        
        # Validate parameter types and values
        for param_name, param_type in required_params.items():
            value = params[param_name]
            
            if param_type == str:
                if not isinstance(value, str) or len(value.strip()) == 0:
                    return False, None, f"參數 '{param_name}' 必須是非空字串"
            
            elif param_type == int:
                if not isinstance(value, int):
                    return False, None, f"參數 '{param_name}' 必須是整數"
                
                # Additional validation for specific parameters
                if param_name in ['width', 'height'] and value <= 0:
                    return False, None, f"參數 '{param_name}' 必須大於0"
                
                if param_name in ['x', 'y'] and value < 0:
                    return False, None, f"參數 '{param_name}' 不能為負數"
            
            elif param_type == list:
                if not isinstance(value, list) or len(value) == 0:
                    return False, None, f"參數 '{param_name}' 必須是非空列表"
        
        # Create the params object
        params_obj = ActionParamsFactory.create_params(action_type, params)
        if params_obj is None:
            return False, None, "參數驗證失敗"
        
        return True, params_obj, "驗證成功"


def get_action_type_display_name(action_type: ActionType) -> str:
    """Get display name for action type in Traditional Chinese."""
    display_names = {
        ActionType.LAUNCH_APP: "啟動應用程式",
        ActionType.CLOSE_APP: "關閉應用程式",
        ActionType.RESIZE_WINDOW: "調整視窗大小",
        ActionType.MOVE_WINDOW: "移動視窗",
        ActionType.MINIMIZE_WINDOW: "最小化視窗",
        ActionType.MAXIMIZE_WINDOW: "最大化視窗",
        ActionType.RESTORE_WINDOW: "還原視窗",
        ActionType.FOCUS_WINDOW: "聚焦視窗",
        ActionType.CLICK_ELEMENT: "點擊元素",
        ActionType.TYPE_TEXT: "輸入文字",
        ActionType.SEND_KEYS: "發送按鍵",
        ActionType.CUSTOM_COMMAND: "自訂命令",
    }
    return display_names.get(action_type, action_type.value)