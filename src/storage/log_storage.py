"""
Log storage implementation for Windows Scheduler GUI.
"""

import json
import gzip
import csv
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from src.models.execution import ExecutionLog, ExecutionResult
from src.core.interfaces import ILogStorage
from src.utils.constants import LOGS_DIR, LOGS_FILE, MAX_LOG_FILE_SIZE, MAX_LOGS_IN_MEMORY


class LogIndex:
    """Index for fast log searching and filtering."""
    
    def __init__(self):
        """Initialize log index."""
        self.by_date: Dict[str, List[str]] = defaultdict(list)  # date -> log_ids
        self.by_schedule: Dict[str, List[str]] = defaultdict(list)  # schedule_name -> log_ids
        self.by_status: Dict[bool, List[str]] = defaultdict(list)  # success -> log_ids
        self.by_operation: Dict[str, List[str]] = defaultdict(list)  # operation -> log_ids
        self.text_index: Dict[str, List[str]] = defaultdict(list)  # word -> log_ids
        self._lock = threading.RLock()
    
    def add_log(self, log: ExecutionLog) -> None:
        """Add a log to the index."""
        with self._lock:
            log_id = log.id
            date_key = log.execution_time.date().isoformat()
            
            # Index by date
            self.by_date[date_key].append(log_id)
            
            # Index by schedule name
            self.by_schedule[log.schedule_name].append(log_id)
            
            # Index by success status
            self.by_status[log.result.success].append(log_id)
            
            # Index by operation
            self.by_operation[log.result.operation].append(log_id)
            
            # Index by text content
            text_content = f"{log.schedule_name} {log.result.operation} {log.result.target} {log.result.message}".lower()
            words = text_content.split()
            for word in words:
                if len(word) > 2:  # Only index words longer than 2 characters
                    self.text_index[word].append(log_id)
    
    def remove_log(self, log: ExecutionLog) -> None:
        """Remove a log from the index."""
        with self._lock:
            log_id = log.id
            date_key = log.execution_time.date().isoformat()
            
            # Remove from all indexes
            if log_id in self.by_date[date_key]:
                self.by_date[date_key].remove(log_id)
            
            if log_id in self.by_schedule[log.schedule_name]:
                self.by_schedule[log.schedule_name].remove(log_id)
            
            if log_id in self.by_status[log.result.success]:
                self.by_status[log.result.success].remove(log_id)
            
            if log_id in self.by_operation[log.result.operation]:
                self.by_operation[log.result.operation].remove(log_id)
            
            # Remove from text index
            text_content = f"{log.schedule_name} {log.result.operation} {log.result.target} {log.result.message}".lower()
            words = text_content.split()
            for word in words:
                if len(word) > 2 and log_id in self.text_index[word]:
                    self.text_index[word].remove(log_id)
    
    def search(self, filters: Dict[str, Any]) -> List[str]:
        """Search logs using filters and return log IDs."""
        with self._lock:
            result_sets = []
            
            # Filter by date range
            if 'start_date' in filters or 'end_date' in filters:
                start_date = filters.get('start_date')
                end_date = filters.get('end_date')
                date_ids = set()
                
                for date_str, log_ids in self.by_date.items():
                    date_obj = datetime.fromisoformat(date_str).date()
                    
                    if start_date and date_obj < start_date:
                        continue
                    if end_date and date_obj > end_date:
                        continue
                    
                    date_ids.update(log_ids)
                
                result_sets.append(date_ids)
            
            # Filter by schedule name
            if 'schedule_name' in filters:
                schedule_name = filters['schedule_name']
                if schedule_name in self.by_schedule:
                    result_sets.append(set(self.by_schedule[schedule_name]))
                else:
                    return []  # No logs for this schedule
            
            # Filter by success status
            if 'success' in filters:
                success = filters['success']
                if success in self.by_status:
                    result_sets.append(set(self.by_status[success]))
                else:
                    return []  # No logs with this status
            
            # Filter by operation
            if 'operation' in filters:
                operation = filters['operation']
                if operation in self.by_operation:
                    result_sets.append(set(self.by_operation[operation]))
                else:
                    return []  # No logs with this operation
            
            # Text search
            if 'query' in filters:
                query = filters['query'].lower()
                words = query.split()
                query_ids = set()
                
                for word in words:
                    if word in self.text_index:
                        if not query_ids:
                            query_ids = set(self.text_index[word])
                        else:
                            query_ids &= set(self.text_index[word])
                
                if words:  # Only add if there were search terms
                    result_sets.append(query_ids)
            
            # Intersect all result sets
            if result_sets:
                final_result = result_sets[0]
                for result_set in result_sets[1:]:
                    final_result &= result_set
                return list(final_result)
            
            # If no filters, return all log IDs
            all_ids = set()
            for log_ids in self.by_date.values():
                all_ids.update(log_ids)
            return list(all_ids)
    
    def clear(self) -> None:
        """Clear the entire index."""
        with self._lock:
            self.by_date.clear()
            self.by_schedule.clear()
            self.by_status.clear()
            self.by_operation.clear()
            self.text_index.clear()


class LogStorage(ILogStorage):
    """High-performance log storage with indexing and compression."""
    
    def __init__(self, logs_dir: str = LOGS_DIR, logs_file: str = LOGS_FILE):
        """
        Initialize log storage.
        
        Args:
            logs_dir: Directory for log files
            logs_file: Main log file name
        """
        self.logs_dir = Path(logs_dir)
        self.logs_file = logs_file
        self.current_log_path = self.logs_dir / logs_file
        self.index_path = self.logs_dir / "log_index.json"
        self.max_file_size = MAX_LOG_FILE_SIZE
        self.max_logs_in_memory = MAX_LOGS_IN_MEMORY
        
        # In-memory cache and index
        self._log_cache: Dict[str, ExecutionLog] = {}
        self._index = LogIndex()
        self._lock = threading.RLock()
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load existing logs and rebuild index
        self._load_initial_data()
    
    def _ensure_directories(self) -> None:
        """Ensure log directories exist."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create archive directory for rotated logs
        archive_dir = self.logs_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
    
    def _load_initial_data(self) -> None:
        """Load existing logs and rebuild index."""
        try:
            # Load current log file
            if self.current_log_path.exists():
                self._load_log_file(self.current_log_path)
            
            # Load archived log files
            archive_dir = self.logs_dir / "archive"
            if archive_dir.exists():
                for archive_file in archive_dir.glob("*.json"):
                    self._load_log_file(archive_file)
                
                # Load compressed archives
                for archive_file in archive_dir.glob("*.json.gz"):
                    self._load_compressed_log_file(archive_file)
            
            self.logger.info(f"Loaded {len(self._log_cache)} logs into cache")
            
        except Exception as e:
            self.logger.error(f"Error loading initial log data: {e}")
    
    def _load_log_file(self, file_path: Path) -> None:
        """Load logs from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        log_data = json.loads(line)
                        log = ExecutionLog.from_dict(log_data)
                        self._log_cache[log.id] = log
                        self._index.add_log(log)
                        
        except Exception as e:
            self.logger.error(f"Error loading log file {file_path}: {e}")
    
    def _load_compressed_log_file(self, file_path: Path) -> None:
        """Load logs from a compressed JSON file."""
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        log_data = json.loads(line)
                        log = ExecutionLog.from_dict(log_data)
                        self._log_cache[log.id] = log
                        self._index.add_log(log)
                        
        except Exception as e:
            self.logger.error(f"Error loading compressed log file {file_path}: {e}")
    
    def save_log(self, log: ExecutionLog) -> bool:
        """
        Save an execution log.
        
        Args:
            log: ExecutionLog to save
            
        Returns:
            True if save was successful
        """
        with self._lock:
            try:
                # Add to cache and index
                self._log_cache[log.id] = log
                self._index.add_log(log)
                
                # Append to current log file
                log_data = log.to_dict()
                with open(self.current_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                
                # Check if rotation is needed
                if self._should_rotate_log():
                    self._rotate_log_files()
                
                # Manage memory usage
                self._manage_memory_cache()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving log: {e}")
                return False
    
    def load_logs(self, page: int, page_size: int, filters: Dict[str, Any]) -> List[ExecutionLog]:
        """
        Load logs with pagination and filtering.
        
        Args:
            page: Page number (0-based)
            page_size: Number of logs per page
            filters: Filter criteria
            
        Returns:
            List of ExecutionLog objects
        """
        with self._lock:
            try:
                # Get filtered log IDs
                log_ids = self._index.search(filters)
                
                # Sort by execution time (newest first)
                logs = [self._log_cache[log_id] for log_id in log_ids if log_id in self._log_cache]
                logs.sort(key=lambda x: x.execution_time, reverse=True)
                
                # Apply pagination
                start_idx = page * page_size
                end_idx = start_idx + page_size
                
                return logs[start_idx:end_idx]
                
            except Exception as e:
                self.logger.error(f"Error loading logs: {e}")
                return []
    
    def search_logs(self, query: str) -> List[ExecutionLog]:
        """
        Search logs by query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching ExecutionLog objects
        """
        filters = {'query': query}
        return self.load_logs(0, 1000, filters)  # Return up to 1000 results
    
    def delete_logs(self, before_date: datetime) -> bool:
        """
        Delete logs before a specific date.
        
        Args:
            before_date: Delete logs before this date
            
        Returns:
            True if deletion was successful
        """
        with self._lock:
            try:
                deleted_count = 0
                logs_to_delete = []
                
                # Find logs to delete
                for log in self._log_cache.values():
                    if log.execution_time < before_date:
                        logs_to_delete.append(log)
                
                # Remove from cache and index
                for log in logs_to_delete:
                    del self._log_cache[log.id]
                    self._index.remove_log(log)
                    deleted_count += 1
                
                # Rewrite log files without deleted logs
                self._rewrite_log_files()
                
                self.logger.info(f"Deleted {deleted_count} logs before {before_date}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error deleting logs: {e}")
                return False
    
    def export_logs(self, logs: List[ExecutionLog], format: str, file_path: str) -> bool:
        """
        Export logs to different formats.
        
        Args:
            logs: List of logs to export
            format: Export format ('json', 'csv', 'txt')
            file_path: Output file path
            
        Returns:
            True if export was successful
        """
        try:
            if format.lower() == 'json':
                return self._export_json(logs, file_path)
            elif format.lower() == 'csv':
                return self._export_csv(logs, file_path)
            elif format.lower() == 'txt':
                return self._export_txt(logs, file_path)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return False
    
    def _export_json(self, logs: List[ExecutionLog], file_path: str) -> bool:
        """Export logs to JSON format."""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_logs': len(logs),
                'logs': [log.to_dict() for log in logs]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def _export_csv(self, logs: List[ExecutionLog], file_path: str) -> bool:
        """Export logs to CSV format."""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'ID', 'Schedule Name', 'Execution Time', 'Success', 
                    'Operation', 'Target', 'Message', 'Duration (seconds)', 'Retry Count'
                ])
                
                # Write data
                for log in logs:
                    writer.writerow([
                        log.id,
                        log.schedule_name,
                        log.execution_time.isoformat(),
                        log.result.success,
                        log.result.operation,
                        log.result.target,
                        log.result.message,
                        log.duration.total_seconds(),
                        log.retry_count
                    ])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def _export_txt(self, logs: List[ExecutionLog], file_path: str) -> bool:
        """Export logs to text format."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Execution Logs Export\n")
                f.write(f"Exported at: {datetime.now().isoformat()}\n")
                f.write(f"Total logs: {len(logs)}\n")
                f.write("=" * 80 + "\n\n")
                
                for log in logs:
                    f.write(f"Log ID: {log.id}\n")
                    f.write(f"Schedule: {log.schedule_name}\n")
                    f.write(f"Execution Time: {log.execution_time.isoformat()}\n")
                    f.write(f"Success: {'Yes' if log.result.success else 'No'}\n")
                    f.write(f"Operation: {log.result.operation}\n")
                    f.write(f"Target: {log.result.target}\n")
                    f.write(f"Message: {log.result.message}\n")
                    f.write(f"Duration: {log.duration.total_seconds():.2f} seconds\n")
                    f.write(f"Retry Count: {log.retry_count}\n")
                    
                    if log.result.details:
                        f.write(f"Details: {json.dumps(log.result.details, indent=2)}\n")
                    
                    f.write("-" * 80 + "\n\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to TXT: {e}")
            return False
    
    def rotate_log_files(self) -> bool:
        """
        Manually trigger log file rotation.
        
        Returns:
            True if rotation was successful
        """
        with self._lock:
            return self._rotate_log_files()
    
    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated."""
        try:
            if not self.current_log_path.exists():
                return False
            
            file_size = self.current_log_path.stat().st_size
            return file_size >= self.max_file_size
            
        except Exception:
            return False
    
    def _rotate_log_files(self) -> bool:
        """Rotate log files and compress old ones."""
        try:
            if not self.current_log_path.exists():
                return True
            
            # Create archive directory
            archive_dir = self.logs_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"logs_{timestamp}.json"
            archive_path = archive_dir / archive_name
            
            # Move current log to archive
            self.current_log_path.rename(archive_path)
            
            # Compress the archived file
            compressed_path = archive_path.with_suffix('.json.gz')
            with open(archive_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove uncompressed archive
            archive_path.unlink()
            
            # Clean old archives (keep last 10)
            self._clean_old_archives()
            
            self.logger.info(f"Log file rotated and compressed to {compressed_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating log files: {e}")
            return False
    
    def _clean_old_archives(self, max_archives: int = 10) -> None:
        """Clean old archive files, keeping only the most recent ones."""
        try:
            archive_dir = self.logs_dir / "archive"
            if not archive_dir.exists():
                return
            
            # Get all archive files
            archive_files = list(archive_dir.glob("*.json.gz"))
            
            if len(archive_files) <= max_archives:
                return
            
            # Sort by modification time (newest first)
            archive_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove old archives
            for old_archive in archive_files[max_archives:]:
                old_archive.unlink()
                self.logger.info(f"Removed old archive: {old_archive}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning old archives: {e}")
    
    def _manage_memory_cache(self) -> None:
        """Manage memory usage by removing old logs from cache."""
        if len(self._log_cache) <= self.max_logs_in_memory:
            return
        
        try:
            # Sort logs by execution time (oldest first)
            logs_by_time = sorted(
                self._log_cache.values(),
                key=lambda x: x.execution_time
            )
            
            # Remove oldest logs from cache (but keep in index)
            logs_to_remove = logs_by_time[:len(self._log_cache) - self.max_logs_in_memory]
            
            for log in logs_to_remove:
                del self._log_cache[log.id]
            
            self.logger.debug(f"Removed {len(logs_to_remove)} logs from memory cache")
            
        except Exception as e:
            self.logger.error(f"Error managing memory cache: {e}")
    
    def _rewrite_log_files(self) -> None:
        """Rewrite log files with current cache contents."""
        try:
            # Backup current file
            if self.current_log_path.exists():
                backup_path = self.current_log_path.with_suffix('.bak')
                self.current_log_path.rename(backup_path)
            
            # Write current logs
            with open(self.current_log_path, 'w', encoding='utf-8') as f:
                for log in self._log_cache.values():
                    log_data = log.to_dict()
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            
            # Remove backup if successful
            backup_path = self.current_log_path.with_suffix('.bak')
            if backup_path.exists():
                backup_path.unlink()
                
        except Exception as e:
            self.logger.error(f"Error rewriting log files: {e}")
            # Restore backup if it exists
            backup_path = self.current_log_path.with_suffix('.bak')
            if backup_path.exists():
                backup_path.rename(self.current_log_path)
    
    def rebuild_index(self) -> bool:
        """
        Rebuild the search index from all logs.
        
        Returns:
            True if rebuild was successful
        """
        with self._lock:
            try:
                self._index.clear()
                
                for log in self._log_cache.values():
                    self._index.add_log(log)
                
                self.logger.info("Log index rebuilt successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error rebuilding index: {e}")
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get log storage statistics.
        
        Returns:
            Dictionary containing storage statistics
        """
        with self._lock:
            try:
                total_logs = len(self._log_cache)
                successful_logs = sum(1 for log in self._log_cache.values() if log.result.success)
                failed_logs = total_logs - successful_logs
                
                # Calculate file sizes
                current_size = self.current_log_path.stat().st_size if self.current_log_path.exists() else 0
                
                archive_dir = self.logs_dir / "archive"
                archive_size = 0
                archive_count = 0
                
                if archive_dir.exists():
                    for archive_file in archive_dir.glob("*.json.gz"):
                        archive_size += archive_file.stat().st_size
                        archive_count += 1
                
                return {
                    'total_logs': total_logs,
                    'successful_logs': successful_logs,
                    'failed_logs': failed_logs,
                    'success_rate': (successful_logs / total_logs * 100) if total_logs > 0 else 0,
                    'current_file_size': current_size,
                    'archive_size': archive_size,
                    'archive_count': archive_count,
                    'total_size': current_size + archive_size,
                    'cache_size': len(self._log_cache)
                }
                
            except Exception as e:
                self.logger.error(f"Error getting statistics: {e}")
                return {}
    
    # IStorage interface methods
    def save(self, data: Any) -> bool:
        """Save data to storage (IStorage interface)."""
        if isinstance(data, ExecutionLog):
            return self.save_log(data)
        return False
    
    def load(self) -> Any:
        """Load data from storage (IStorage interface)."""
        return self.load_logs(0, 100, {})  # Return first 100 logs
    
    def delete(self, identifier: str) -> bool:
        """Delete data by identifier (IStorage interface)."""
        with self._lock:
            if identifier in self._log_cache:
                log = self._log_cache[identifier]
                del self._log_cache[identifier]
                self._index.remove_log(log)
                return True
            return False
    
    def exists(self, identifier: str) -> bool:
        """Check if data exists (IStorage interface)."""
        return identifier in self._log_cache


# Global log storage instance
_log_storage: Optional[LogStorage] = None


def get_log_storage() -> LogStorage:
    """
    Get the global log storage instance.
    
    Returns:
        LogStorage instance
    """
    global _log_storage
    if _log_storage is None:
        _log_storage = LogStorage()
    return _log_storage


def initialize_log_storage(logs_dir: Optional[str] = None, logs_file: Optional[str] = None) -> LogStorage:
    """
    Initialize the global log storage.
    
    Args:
        logs_dir: Optional custom logs directory
        logs_file: Optional custom logs file name
        
    Returns:
        LogStorage instance
    """
    global _log_storage
    if logs_dir or logs_file:
        _log_storage = LogStorage(
            logs_dir=logs_dir or LOGS_DIR,
            logs_file=logs_file or LOGS_FILE
        )
    else:
        _log_storage = LogStorage()
    return _log_storage