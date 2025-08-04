"""
Main application entry point for Windows Scheduler GUI.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gui.main_window import MainWindow
from src.models.config import AppConfig
from src.utils.constants import APP_NAME, CONFIG_DIR, CONFIG_FILE
from src.core.error_handler import (
    get_global_error_handler, 
    ConfigurationError, 
    SchedulerError,
    ErrorSeverity,
    handle_errors
)


class SchedulerApp:
    """Main application class for Windows Scheduler GUI."""
    
    def __init__(self):
        """Initialize the scheduler application."""
        self.config: Optional[AppConfig] = None
        self.main_window: Optional[MainWindow] = None
        self.error_handler = get_global_error_handler()
        
        # Setup error recovery callbacks
        self._setup_error_recovery()
        
        # Initialize application
        self._initialize_app()
    
    def _setup_error_recovery(self):
        """Setup error recovery callbacks for the application."""
        # Register recovery callback for configuration errors
        self.error_handler.register_recovery_callback(
            "ConfigurationError",
            self._recover_from_config_error
        )
        
        # Register recovery callback for storage errors
        self.error_handler.register_recovery_callback(
            "StorageError", 
            self._recover_from_storage_error
        )
        
        # Register application error callback
        self.error_handler.register_error_callback(self._on_application_error)
    
    def _recover_from_config_error(self) -> bool:
        """Attempt to recover from configuration errors."""
        try:
            # Reset to default configuration
            self.config = AppConfig.get_default()
            self._save_configuration()
            return True
        except Exception:
            return False
    
    def _recover_from_storage_error(self) -> bool:
        """Attempt to recover from storage errors."""
        try:
            # Ensure directories exist
            config_dir = Path(CONFIG_DIR)
            config_dir.mkdir(exist_ok=True)
            return True
        except Exception:
            return False
    
    def _on_application_error(self, error: Exception):
        """Handle application-level errors."""
        # Log application context information
        if hasattr(error, 'details') and isinstance(error.details, dict):
            error.details.update({
                "app_initialized": self.main_window is not None,
                "config_loaded": self.config is not None
            })
    
    @handle_errors(severity=ErrorSeverity.HIGH, show_user_message=True, attempt_recovery=True)
    def _initialize_app(self):
        """Initialize the application."""
        # Load configuration
        self._load_configuration()
        
        # Create main window
        self.main_window = MainWindow(self.config)
        
        # Setup application-specific handlers
        self._setup_handlers()
    
    def _load_configuration(self):
        """Load application configuration."""
        config_path = Path(CONFIG_DIR) / CONFIG_FILE
        
        if config_path.exists():
            try:
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = AppConfig.from_dict(config_data)
                
                # Validate configuration
                if not self.config.validate():
                    raise ConfigurationError("Invalid configuration values")
                    
            except Exception as e:
                # Convert to ConfigurationError for proper handling
                config_error = ConfigurationError(
                    f"Failed to load configuration: {str(e)}",
                    details={"config_path": str(config_path)}
                )
                self.error_handler.handle_error(
                    config_error, 
                    severity=ErrorSeverity.MEDIUM,
                    show_user_message=True,
                    attempt_recovery=True
                )
                # Use default configuration as fallback
                self.config = AppConfig.get_default()
        else:
            # Use default configuration
            self.config = AppConfig.get_default()
            self._save_configuration()
    
    def _save_configuration(self):
        """Save current configuration."""
        try:
            # Ensure config directory exists
            config_dir = Path(CONFIG_DIR)
            config_dir.mkdir(exist_ok=True)
            
            # Save configuration
            config_path = config_dir / CONFIG_FILE
            import json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Convert to ConfigurationError for proper handling
            config_error = ConfigurationError(
                f"Failed to save configuration: {str(e)}",
                details={"config_path": str(config_dir / CONFIG_FILE)}
            )
            self.error_handler.handle_error(
                config_error,
                severity=ErrorSeverity.MEDIUM,
                show_user_message=True,
                attempt_recovery=False
            )
    
    def _setup_handlers(self):
        """Setup application-specific event handlers."""
        if self.main_window:
            # Override the exit handler to save configuration
            original_exit = self.main_window._on_exit
            
            def enhanced_exit():
                self._save_configuration()
                original_exit()
            
            self.main_window._on_exit = enhanced_exit
    
    @handle_errors(severity=ErrorSeverity.CRITICAL, show_user_message=True, attempt_recovery=True)
    def run(self):
        """Run the application."""
        if not self.main_window:
            raise SchedulerError(
                "Main window not initialized",
                error_code="MAIN_WINDOW_NOT_INITIALIZED"
            )
        
        try:
            self.main_window.run()
        except KeyboardInterrupt:
            # Handle graceful shutdown
            self._save_configuration()
            sys.exit(0)
        except Exception as e:
            # Convert to SchedulerError for proper handling
            app_error = SchedulerError(
                f"Application runtime error: {str(e)}",
                error_code="RUNTIME_ERROR",
                details={"error_type": type(e).__name__}
            )
            self.error_handler.handle_critical_error(app_error)
            sys.exit(1)


def main():
    """Main entry point."""
    try:
        # Create and run application
        app = SchedulerApp()
        app.run()
    except Exception as e:
        # Fallback error handling for initialization failures
        try:
            error_handler = get_global_error_handler()
            startup_error = SchedulerError(
                f"Application startup failed: {str(e)}",
                error_code="STARTUP_FAILURE",
                details={"error_type": type(e).__name__}
            )
            error_handler.handle_critical_error(startup_error)
        except Exception:
            # Ultimate fallback if even error handler fails
            root = tk.Tk()
            root.withdraw()  # Hide root window
            messagebox.showerror(
                "嚴重錯誤",
                f"應用程式啟動失敗：\n{str(e)}\n\n錯誤處理系統也無法啟動。"
            )
        finally:
            sys.exit(1)


if __name__ == "__main__":
    main()