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
        """Search logs using filters and return log IDs with advanced search capabilities."""
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
            
            # Filter by schedule name (supports partial matching)
            if 'schedule_name' in filters:
                schedule_name = filters['schedule_name'].lower()
                schedule_ids = set()
                
                for indexed_schedule, log_ids in self.by_schedule.items():
                    if schedule_name in indexed_schedule.lower():
                        schedule_ids.update(log_ids)
                
                if schedule_ids:
                    result_sets.append(schedule_ids)
                else:
                    return []  # No logs for this schedule pattern
            
            # Filter by success status
            if 'success' in filters:
                success = filters['success']
                if success in self.by_status:
                    result_sets.append(set(self.by_status[success]))
                else:
                    return []  # No logs with this status
            
            # Filter by operation (supports partial matching)
            if 'operation' in filters:
                operation = filters['operation'].lower()
                operation_ids = set()
                
                for indexed_operation, log_ids in self.by_operation.items():
                    if operation in indexed_operation.lower():
                        operation_ids.update(log_ids)
                
                if operation_ids:
                    result_sets.append(operation_ids)
                else:
                    return []  # No logs with this operation pattern
            
            # Advanced text search with phrase support and fuzzy matching
            if 'query' in filters:
                query = filters['query'].strip()
                if query:
                    query_ids = self._advanced_text_search(query)
                    if query_ids is not None:
                        result_sets.append(query_ids)
            
            # Filter by retry count
            if 'min_retry_count' in filters:
                min_retry = filters['min_retry_count']
                retry_ids = set()
                for log_id in self._get_all_log_ids():
                    # This would need to be implemented with retry count indexing
                    pass  # Placeholder for retry count filtering
            
            # Filter by duration range
            if 'min_duration' in filters or 'max_duration' in filters:
                min_duration = filters.get('min_duration', 0)
                max_duration = filters.get('max_duration', float('inf'))
                duration_ids = set()
                for log_id in self._get_all_log_ids():
                    # This would need to be implemented with duration indexing
                    pass  # Placeholder for duration filtering
            
            # Intersect all result sets
            if result_sets:
                final_result = result_sets[0]
                for result_set in result_sets[1:]:
                    final_result &= result_set
                return list(final_result)
            
            # If no filters, return all log IDs
            return self._get_all_log_ids()
    
    def _advanced_text_search(self, query: str) -> Optional[set]:
        """
        Perform advanced text search with phrase support and fuzzy matching.
        
        Args:
            query: Search query with potential phrases and operators
            
        Returns:
            Set of matching log IDs or None if no matches
        """
        query = query.lower().strip()
        
        # Handle quoted phrases
        phrases = []
        words = []
        in_quotes = False
        current_phrase = ""
        
        i = 0
        while i < len(query):
            char = query[i]
            if char == '"':
                if in_quotes:
                    # End of phrase
                    if current_phrase.strip():
                        phrases.append(current_phrase.strip())
                    current_phrase = ""
                    in_quotes = False
                else:
                    # Start of phrase
                    in_quotes = True
                i += 1
            elif in_quotes:
                current_phrase += char
                i += 1
            elif char == ' ':
                i += 1
            else:
                # Regular word
                word = ""
                while i < len(query) and query[i] not in [' ', '"']:
                    word += query[i]
                    i += 1
                if word.strip():
                    words.append(word.strip())
        
        # Handle unclosed phrase
        if in_quotes and current_phrase.strip():
            phrases.append(current_phrase.strip())
        
        # Search for phrases and words
        result_sets = []
        
        # Search phrases (exact phrase matching)
        for phrase in phrases:
            phrase_ids = self._search_phrase(phrase)
            if phrase_ids:
                result_sets.append(phrase_ids)
            else:
                return set()  # Phrase not found, no results
        
        # Search individual words
        for word in words:
            if len(word) > 1:  # Skip single characters
                word_ids = self._search_word_fuzzy(word)
                if word_ids:
                    result_sets.append(word_ids)
                else:
                    return set()  # Word not found, no results
        
        # Intersect all results (AND operation)
        if result_sets:
            final_result = result_sets[0]
            for result_set in result_sets[1:]:
                final_result &= result_set
            return final_result
        
        return set()
    
    def _search_phrase(self, phrase: str) -> set:
        """Search for exact phrase in log content."""
        phrase_ids = set()
        phrase_words = phrase.split()
        
        if not phrase_words:
            return phrase_ids
        
        # Get logs that contain all words in the phrase
        candidate_ids = None
        for word in phrase_words:
            if word in self.text_index:
                word_ids = set(self.text_index[word])
                if candidate_ids is None:
                    candidate_ids = word_ids
                else:
                    candidate_ids &= word_ids
            else:
                return set()  # Word not found
        
        return candidate_ids or set()
    
    def _search_word_fuzzy(self, word: str) -> set:
        """Search for word with fuzzy matching support."""
        word_ids = set()
        
        # Exact match first
        if word in self.text_index:
            word_ids.update(self.text_index[word])
        
        # Fuzzy matching - find words that contain the search term
        for indexed_word in self.text_index:
            if word in indexed_word and word != indexed_word:
                word_ids.update(self.text_index[indexed_word])
        
        return word_ids
    
    def _get_all_log_ids(self) -> List[str]:
        """Get all log IDs from the index."""
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
        Get comprehensive log statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        with self._lock:
            try:
                stats = {}
                
                if not self._log_cache:
                    return {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'success_rate': 0.0,
                        'average_duration': 0.0,
                        'max_duration': 0.0,
                        'min_duration': 0.0,
                        'schedule_stats': {},
                        'error_stats': {},
                        'trends': {}
                    }
                
                logs = list(self._log_cache.values())
                
                # Basic statistics
                total_executions = len(logs)
                successful_executions = sum(1 for log in logs if log.result.success)
                failed_executions = total_executions - successful_executions
                success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
                
                # Duration statistics
                durations = [log.duration.total_seconds() for log in logs]
                average_duration = sum(durations) / len(durations) if durations else 0.0
                max_duration = max(durations) if durations else 0.0
                min_duration = min(durations) if durations else 0.0
                
                stats.update({
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'failed_executions': failed_executions,
                    'success_rate': success_rate,
                    'average_duration': average_duration,
                    'max_duration': max_duration,
                    'min_duration': min_duration
                })
                
                # Schedule-specific statistics
                schedule_stats = {}
                schedule_groups = defaultdict(list)
                
                for log in logs:
                    schedule_groups[log.schedule_name].append(log)
                
                for schedule_name, schedule_logs in schedule_groups.items():
                    schedule_executions = len(schedule_logs)
                    schedule_successes = sum(1 for log in schedule_logs if log.result.success)
                    schedule_success_rate = (schedule_successes / schedule_executions * 100) if schedule_executions > 0 else 0.0
                    schedule_durations = [log.duration.total_seconds() for log in schedule_logs]
                    schedule_avg_duration = sum(schedule_durations) / len(schedule_durations) if schedule_durations else 0.0
                    
                    schedule_stats[schedule_name] = {
                        'executions': schedule_executions,
                        'success_rate': schedule_success_rate,
                        'avg_duration': schedule_avg_duration
                    }
                
                stats['schedule_stats'] = schedule_stats
                
                # Error statistics
                error_stats = {}
                error_messages = defaultdict(int)
                
                for log in logs:
                    if not log.result.success:
                        # Categorize errors by message patterns
                        message = log.result.message.lower()
                        if 'network' in message or 'connection' in message:
                            error_messages['網路連線錯誤'] += 1
                        elif 'timeout' in message:
                            error_messages['執行逾時'] += 1
                        elif 'permission' in message or 'access' in message:
                            error_messages['權限錯誤'] += 1
                        elif 'not found' in message or 'missing' in message:
                            error_messages['檔案或程序未找到'] += 1
                        else:
                            error_messages['其他錯誤'] += 1
                
                total_errors = sum(error_messages.values())
                for error_type, count in error_messages.items():
                    percentage = (count / total_errors * 100) if total_errors > 0 else 0.0
                    error_stats[error_type] = {
                        'count': count,
                        'percentage': percentage,
                        'last_occurrence': 'N/A'  # Could be enhanced to track last occurrence
                    }
                
                stats['error_stats'] = error_stats
                
                # Trend analysis
                trends = self._calculate_trends(logs)
                stats['trends'] = trends
                
                # Performance metrics
                stats.update({
                    'average_response_time': average_duration,
                    'p95_response_time': self._calculate_percentile(durations, 95),
                    'p99_response_time': self._calculate_percentile(durations, 99),
                    'max_concurrent_executions': 1,  # Simplified - could be enhanced
                    'average_system_load': 0.0,  # Would need system monitoring
                    'peak_memory_usage': 0.0  # Would need memory monitoring
                })
                
                return stats
                
            except Exception as e:
                self.logger.error(f"Error calculating statistics: {e}")
                return {}
    
    def _calculate_trends(self, logs: List[ExecutionLog]) -> Dict[str, Any]:
        """Calculate execution trends."""
        trends = {
            'daily': defaultdict(int),
            'hourly': defaultdict(int)
        }
        
        for log in logs:
            # Daily trends
            day_key = log.execution_time.strftime('%Y-%m-%d')
            trends['daily'][day_key] += 1
            
            # Hourly trends
            hour_key = log.execution_time.hour
            trends['hourly'][hour_key] += 1
        
        # Convert to regular dicts and sort
        trends['daily'] = dict(sorted(trends['daily'].items()))
        trends['hourly'] = dict(sorted(trends['hourly'].items()))
        
        return trends
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def get_log_count(self, filters: Dict[str, Any] = None) -> int:
        """
        Get count of logs matching filters.
        
        Args:
            filters: Filter criteria
            
        Returns:
            Number of matching logs
        """
        with self._lock:
            if not filters:
                return len(self._log_cache)
            
            log_ids = self._index.search(filters)
            return len(log_ids)
    
    def backup_logs(self, backup_path: str) -> bool:
        """
        Create a backup of all logs.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if backup was successful
        """
        try:
            all_logs = list(self._log_cache.values())
            return self.export_logs(all_logs, 'json', backup_path)
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_logs(self, backup_path: str) -> bool:
        """
        Restore logs from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore was successful
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if 'logs' not in backup_data:
                self.logger.error("Invalid backup file format")
                return False
            
            # Clear current data
            with self._lock:
                self._log_cache.clear()
                self._index.clear()
                
                # Restore logs
                for log_data in backup_data['logs']:
                    log = ExecutionLog.from_dict(log_data)
                    self._log_cache[log.id] = log
                    self._index.add_log(log)
                
                # Rewrite log files
                self._rewrite_log_files()
            
            self.logger.info(f"Restored {len(backup_data['logs'])} logs from backup")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return False


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