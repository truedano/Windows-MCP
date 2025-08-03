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


class SchedulerApp:
    """Main application class for Windows Scheduler GUI."""
    
    def __init__(self):
        """Initialize the scheduler application."""
        self.config: Optional[AppConfig] = None
        self.main_window: Optional[MainWindow] = None
        
        # Initialize application
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the application."""
        try:
            # Load configuration
            self._load_configuration()
            
            # Create main window
            self.main_window = MainWindow(self.config)
            
            # Setup application-specific handlers
            self._setup_handlers()
            
        except Exception as e:
            messagebox.showerror(
                "初始化錯誤", 
                f"應用程式初始化失敗：\n{str(e)}"
            )
            sys.exit(1)
    
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
                    raise ValueError("Invalid configuration values")
                    
            except Exception as e:
                messagebox.showwarning(
                    "配置載入警告",
                    f"無法載入配置文件，使用預設設定：\n{str(e)}"
                )
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
            messagebox.showerror(
                "配置儲存錯誤",
                f"無法儲存配置文件：\n{str(e)}"
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
    
    def run(self):
        """Run the application."""
        if self.main_window:
            try:
                self.main_window.run()
            except KeyboardInterrupt:
                self._save_configuration()
                sys.exit(0)
            except Exception as e:
                messagebox.showerror(
                    "應用程式錯誤",
                    f"應用程式執行時發生錯誤：\n{str(e)}"
                )
                sys.exit(1)
        else:
            messagebox.showerror("錯誤", "主視窗未初始化")
            sys.exit(1)


def main():
    """Main entry point."""
    try:
        # Create and run application
        app = SchedulerApp()
        app.run()
    except Exception as e:
        # Fallback error handling
        root = tk.Tk()
        root.withdraw()  # Hide root window
        messagebox.showerror(
            "嚴重錯誤",
            f"應用程式啟動失敗：\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()