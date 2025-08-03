"""
Application configuration model.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AppConfig:
    """Application configuration settings."""
    schedule_check_frequency: int = 1  # seconds
    notifications_enabled: bool = True
    log_recording_enabled: bool = True
    log_retention_days: int = 30
    max_retry_attempts: int = 3
    ui_theme: str = "default"
    language: str = "zh-TW"
    window_width: int = 1024
    window_height: int = 768
    auto_start_scheduler: bool = True
    minimize_to_tray: bool = True
    show_splash_screen: bool = True
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'schedule_check_frequency': self.schedule_check_frequency,
            'notifications_enabled': self.notifications_enabled,
            'log_recording_enabled': self.log_recording_enabled,
            'log_retention_days': self.log_retention_days,
            'max_retry_attempts': self.max_retry_attempts,
            'ui_theme': self.ui_theme,
            'language': self.language,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'auto_start_scheduler': self.auto_start_scheduler,
            'minimize_to_tray': self.minimize_to_tray,
            'show_splash_screen': self.show_splash_screen,
            'debug_mode': self.debug_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary."""
        return cls(
            schedule_check_frequency=data.get('schedule_check_frequency', 1),
            notifications_enabled=data.get('notifications_enabled', True),
            log_recording_enabled=data.get('log_recording_enabled', True),
            log_retention_days=data.get('log_retention_days', 30),
            max_retry_attempts=data.get('max_retry_attempts', 3),
            ui_theme=data.get('ui_theme', 'default'),
            language=data.get('language', 'zh-TW'),
            window_width=data.get('window_width', 1024),
            window_height=data.get('window_height', 768),
            auto_start_scheduler=data.get('auto_start_scheduler', True),
            minimize_to_tray=data.get('minimize_to_tray', True),
            show_splash_screen=data.get('show_splash_screen', True),
            debug_mode=data.get('debug_mode', False)
        )
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        """Get default configuration."""
        return cls()
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            bool: True if configuration is valid
        """
        # Check schedule frequency is positive
        if self.schedule_check_frequency <= 0:
            return False
            
        # Check log retention is reasonable
        if self.log_retention_days < 1 or self.log_retention_days > 365:
            return False
            
        # Check retry attempts is reasonable
        if self.max_retry_attempts < 0 or self.max_retry_attempts > 10:
            return False
            
        # Check window dimensions are reasonable
        if self.window_width < 800 or self.window_width > 3840:
            return False
        if self.window_height < 600 or self.window_height > 2160:
            return False
            
        # Check theme is valid
        valid_themes = ['default', 'dark', 'light']
        if self.ui_theme not in valid_themes:
            return False
            
        # Check language is valid
        valid_languages = ['zh-TW', 'zh-CN', 'en-US']
        if self.language not in valid_languages:
            return False
            
        return True
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)