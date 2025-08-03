"""
Task Storage implementation for JSON-based task persistence.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import threading

from ..core.interfaces import ITaskStorage
from ..models.task import Task


class TaskStorage(ITaskStorage):
    """
    Task storage implementation that provides JSON-based persistence for tasks.
    
    This class handles task CRUD operations, backup and restore functionality
    according to the design specifications.
    """
    
    def __init__(self, storage_path: str = "data/tasks.json", backup_dir: str = "data/backups"):
        """
        Initialize the task storage.
        
        Args:
            storage_path: Path to the main tasks JSON file
            backup_dir: Directory for backup files
        """
        self.storage_path = Path(storage_path)
        self.backup_dir = Path(backup_dir)
        self._lock = threading.RLock()  # Thread-safe operations
        
        # Ensure directories exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty file if it doesn't exist
        if not self.storage_path.exists():
            self._write_tasks_file({})
    
    def save_task(self, task: Task) -> bool:
        """
        Save a task to storage.
        
        Args:
            task: Task instance to save
            
        Returns:
            bool: True if task was saved successfully
        """
        try:
            with self._lock:
                # Load existing tasks
                tasks_data = self._read_tasks_file()
                
                # Update or add the task
                tasks_data[task.id] = task.to_dict()
                
                # Write back to file
                self._write_tasks_file(tasks_data)
                
                return True
                
        except Exception as e:
            print(f"Error saving task {task.id}: {e}")
            return False
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """
        Load a task by ID.
        
        Args:
            task_id: ID of the task to load
            
        Returns:
            Optional[Task]: Task instance or None if not found
        """
        try:
            with self._lock:
                tasks_data = self._read_tasks_file()
                
                if task_id in tasks_data:
                    return Task.from_dict(tasks_data[task_id])
                
                return None
                
        except Exception as e:
            print(f"Error loading task {task_id}: {e}")
            return None
    
    def load_all_tasks(self) -> List[Task]:
        """
        Load all tasks.
        
        Returns:
            List[Task]: List of all tasks
        """
        try:
            with self._lock:
                tasks_data = self._read_tasks_file()
                
                tasks = []
                for task_data in tasks_data.values():
                    try:
                        task = Task.from_dict(task_data)
                        tasks.append(task)
                    except Exception as e:
                        print(f"Error loading task from data: {e}")
                        continue
                
                return tasks
                
        except Exception as e:
            print(f"Error loading all tasks: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            bool: True if task was deleted successfully
        """
        try:
            with self._lock:
                tasks_data = self._read_tasks_file()
                
                if task_id in tasks_data:
                    del tasks_data[task_id]
                    self._write_tasks_file(tasks_data)
                    return True
                
                return False
                
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False
    
    def backup_tasks(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of all tasks.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            str: Path to the backup file
        """
        try:
            with self._lock:
                if backup_name is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"tasks_backup_{timestamp}.json"
                
                backup_path = self.backup_dir / backup_name
                
                # Copy current tasks file to backup location
                if self.storage_path.exists():
                    shutil.copy2(self.storage_path, backup_path)
                else:
                    # Create empty backup if no tasks file exists
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                
                return str(backup_path)
                
        except Exception as e:
            print(f"Error creating backup: {e}")
            raise
    
    def restore_tasks(self, backup_file: str) -> bool:
        """
        Restore tasks from a backup file.
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            bool: True if tasks were restored successfully
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                print(f"Backup file not found: {backup_file}")
                return False
            
            with self._lock:
                # Validate backup file format
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if not isinstance(backup_data, dict):
                    print("Invalid backup file format")
                    return False
                
                # Create a backup of current data before restore
                current_backup = self.backup_tasks(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                print(f"Current data backed up to: {current_backup}")
                
                # Restore from backup
                shutil.copy2(backup_path, self.storage_path)
                
                return True
                
        except Exception as e:
            print(f"Error restoring from backup {backup_file}: {e}")
            return False
    
    def get_task_count(self) -> int:
        """
        Get the total number of tasks in storage.
        
        Returns:
            int: Number of tasks
        """
        try:
            with self._lock:
                tasks_data = self._read_tasks_file()
                return len(tasks_data)
                
        except Exception as e:
            print(f"Error getting task count: {e}")
            return 0
    
    def clear_all_tasks(self) -> bool:
        """
        Clear all tasks from storage.
        
        Returns:
            bool: True if all tasks were cleared successfully
        """
        try:
            with self._lock:
                # Create backup before clearing
                backup_path = self.backup_tasks(f"pre_clear_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                print(f"Data backed up to: {backup_path}")
                
                # Clear all tasks
                self._write_tasks_file({})
                
                return True
                
        except Exception as e:
            print(f"Error clearing all tasks: {e}")
            return False
    
    def export_tasks(self, export_path: str) -> bool:
        """
        Export all tasks to a specified file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            bool: True if export was successful
        """
        try:
            with self._lock:
                tasks_data = self._read_tasks_file()
                
                export_file = Path(export_path)
                export_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks_data, f, ensure_ascii=False, indent=2)
                
                return True
                
        except Exception as e:
            print(f"Error exporting tasks to {export_path}: {e}")
            return False
    
    def import_tasks(self, import_path: str, merge: bool = True) -> int:
        """
        Import tasks from a specified file.
        
        Args:
            import_path: Path to import file
            merge: If True, merge with existing tasks; if False, replace all tasks
            
        Returns:
            int: Number of tasks imported successfully
        """
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                print(f"Import file not found: {import_path}")
                return 0
            
            with self._lock:
                # Load import data
                with open(import_file, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                if not isinstance(import_data, dict):
                    print("Invalid import file format")
                    return 0
                
                # Validate imported tasks
                valid_tasks = {}
                for task_id, task_data in import_data.items():
                    try:
                        # Validate by creating Task instance
                        task = Task.from_dict(task_data)
                        valid_tasks[task_id] = task_data
                    except Exception as e:
                        print(f"Skipping invalid task {task_id}: {e}")
                        continue
                
                if merge:
                    # Merge with existing tasks
                    existing_tasks = self._read_tasks_file()
                    existing_tasks.update(valid_tasks)
                    self._write_tasks_file(existing_tasks)
                else:
                    # Replace all tasks
                    self._write_tasks_file(valid_tasks)
                
                return len(valid_tasks)
                
        except Exception as e:
            print(f"Error importing tasks from {import_path}: {e}")
            return 0
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage.
        
        Returns:
            Dict[str, Any]: Storage information
        """
        try:
            with self._lock:
                info = {
                    'storage_path': str(self.storage_path),
                    'backup_dir': str(self.backup_dir),
                    'file_exists': self.storage_path.exists(),
                    'file_size': self.storage_path.stat().st_size if self.storage_path.exists() else 0,
                    'task_count': self.get_task_count(),
                    'last_modified': datetime.fromtimestamp(
                        self.storage_path.stat().st_mtime
                    ).isoformat() if self.storage_path.exists() else None
                }
                
                # Get backup files info
                backup_files = []
                if self.backup_dir.exists():
                    for backup_file in self.backup_dir.glob("*.json"):
                        backup_files.append({
                            'name': backup_file.name,
                            'path': str(backup_file),
                            'size': backup_file.stat().st_size,
                            'created': datetime.fromtimestamp(
                                backup_file.stat().st_ctime
                            ).isoformat()
                        })
                
                info['backups'] = sorted(backup_files, key=lambda x: x['created'], reverse=True)
                
                return info
                
        except Exception as e:
            print(f"Error getting storage info: {e}")
            return {}
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backup files to keep
            
        Returns:
            int: Number of backup files deleted
        """
        try:
            if not self.backup_dir.exists():
                return 0
            
            backup_files = list(self.backup_dir.glob("*.json"))
            
            if len(backup_files) <= keep_count:
                return 0
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda f: f.stat().st_ctime, reverse=True)
            
            # Delete old backups
            deleted_count = 0
            for backup_file in backup_files[keep_count:]:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting backup {backup_file}: {e}")
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
            return 0
    
    # Implementation of abstract methods from IStorage
    def save(self, data: Any) -> bool:
        """Save data to storage (generic interface)."""
        if isinstance(data, Task):
            return self.save_task(data)
        return False
    
    def load(self) -> Any:
        """Load data from storage (generic interface)."""
        return self.load_all_tasks()
    
    def delete(self, identifier: str) -> bool:
        """Delete data by identifier (generic interface)."""
        return self.delete_task(identifier)
    
    def exists(self, identifier: str) -> bool:
        """Check if data exists (generic interface)."""
        task = self.load_task(identifier)
        return task is not None
    
    # Private helper methods
    def _read_tasks_file(self) -> Dict[str, Dict[str, Any]]:
        """
        Read tasks from the JSON file.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of task data
        """
        try:
            if not self.storage_path.exists():
                return {}
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                print("Invalid tasks file format, initializing empty")
                return {}
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error in tasks file: {e}")
            # Backup corrupted file
            corrupted_backup = self.storage_path.with_suffix('.corrupted.json')
            shutil.copy2(self.storage_path, corrupted_backup)
            print(f"Corrupted file backed up to: {corrupted_backup}")
            return {}
        except Exception as e:
            print(f"Error reading tasks file: {e}")
            return {}
    
    def _write_tasks_file(self, tasks_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Write tasks to the JSON file.
        
        Args:
            tasks_data: Dictionary of task data to write
        """
        try:
            # Write to temporary file first for atomic operation
            temp_path = self.storage_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
            
            # Atomic move to final location
            temp_path.replace(self.storage_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            temp_path = self.storage_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            raise e