"""
Constants and configuration values for the Windows Scheduler GUI application.
"""

# Application Information
APP_NAME = "Windows Scheduler GUI"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Windows應用程式排程控制GUI"

# File Paths
CONFIG_DIR = ".config"
DATA_DIR = "data"
LOGS_DIR = "logs"
BACKUP_DIR = "backups"

# File Names
TASKS_FILE = "tasks.json"
CONFIG_FILE = "config.json"
LOGS_FILE = "execution_logs.json"
HELP_CONTENT_FILE = "help_content.json"

# Default Settings
DEFAULT_SCHEDULE_CHECK_FREQUENCY = 1  # seconds
DEFAULT_LOG_RETENTION_DAYS = 30
DEFAULT_MAX_RETRY_ATTEMPTS = 3
DEFAULT_UI_THEME = "default"
DEFAULT_LANGUAGE = "zh-TW"

# GUI Settings
MAIN_WINDOW_MIN_WIDTH = 800
MAIN_WINDOW_MIN_HEIGHT = 600
MAIN_WINDOW_DEFAULT_WIDTH = 1024
MAIN_WINDOW_DEFAULT_HEIGHT = 768

# Logging Settings
MAX_LOG_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_LOGS_IN_MEMORY = 10000

# Task Execution Settings
MAX_CONCURRENT_TASKS = 5
TASK_TIMEOUT_SECONDS = 300  # 5 minutes
