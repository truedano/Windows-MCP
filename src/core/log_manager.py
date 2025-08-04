"""
Log management system for Windows Scheduler GUI.
"""

import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict, Counter

from src.models.execution import ExecutionLog, ExecutionResult, ExecutionStatistics
from src.models.task import Task
from src.storage.log_storage import get_log_storage, LogStorage
from src.core.config_manager import get_config_manager
from src.utils.constants import MAX_LOGS_IN_MEMORY


class LogManager:
    """
    Central log management system.
    
    Manages execution log recording, querying, and statistics generation.
    """
    
    def __init__(self, storage: Optional[LogStorage] = None):
        """
        Initialize log manager.
        
        Args:
            storage: Log storage instance
        """
        self.storage = storage or get_log_storage()
        self.config_manager = get_config_manager()
        
        # In-memory log cache for fast access
        self._log_cache: List[ExecutionLog] = []
        self._max_logs = MAX_LOGS_IN_MEMORY
        self._cache_lock = threading.RLock()
        
        # Statistics cache
        self._stats_cache: Optional[ExecutionStatistics] = None
        self._stats_cache_time: Optional[datetime] = None
        self._stats_cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        
        # Event callbacks
        self._log_added_callbacks: List[Callable[[ExecutionLog], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load recent logs into cache
        self._load_recent_logs()
    
    def _load_recent_logs(self) -> None:
        """Load recent logs into memory cache."""
        try:
            # Load recent logs (last 1000)
            recent_logs = self.storage.load_logs(0, 1000, {})
            
            with self._cache_lock:
                self._log_cache = recent_logs
                
            self.logger.info(f"Loaded {len(recent_logs)} recent logs into cache")
            
        except Exception as e:
            self.logger.error(f"Error loading recent logs: {e}")
    
    def log_execution(self, task: Task, result: ExecutionResult, duration: timedelta = None) -> bool:
        """
        Log a task execution.
        
        Args:
            task: The executed task
            result: Execution result
            duration: Execution duration (calculated if not provided)
            
        Returns:
            True if logging was successful
        """
        try:
            # Calculate duration if not provided
            if duration is None:
                # Estimate duration based on result timestamp and current time
                duration = datetime.now() - result.timestamp
            
            # Create execution log
            execution_log = ExecutionLog.create_log(
                task.name,
                result,
                duration,
                task.retry_count
            )
            
            # Save to storage
            success = self.storage.save_log(execution_log)
            
            if success:
                # Add to cache
                self._add_to_cache(execution_log)
                
                # Invalidate stats cache
                self._invalidate_stats_cache()
                
                # Notify callbacks
                self._notify_log_added(execution_log)
                
                self.logger.debug(f"Logged execution for task: {task.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error logging execution for task {task.name}: {e}")
            return False
    
    def _add_to_cache(self, log: ExecutionLog) -> None:
        """Add log to memory cache."""
        with self._cache_lock:
            # Add to beginning of cache (most recent first)
            self._log_cache.insert(0, log)
            
            # Trim cache if too large
            if len(self._log_cache) > self._max_logs:
                self._log_cache = self._log_cache[:self._max_logs]
    
    def get_logs(self, page: int = 0, page_size: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[ExecutionLog]:
        """
        Get execution logs with pagination and filtering.
        
        Args:
            page: Page number (0-based)
            page_size: Number of logs per page
            filters: Filter criteria
            
        Returns:
            List of ExecutionLog objects
        """
        try:
            filters = filters or {}
            
            # Check if we can serve from cache (for recent logs without complex filters)
            if self._can_serve_from_cache(filters, page, page_size):
                return self._get_from_cache(page, page_size, filters)
            
            # Load from storage
            return self.storage.load_logs(page, page_size, filters)
            
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return []
    
    def _can_serve_from_cache(self, filters: Dict[str, Any], page: int, page_size: int) -> bool:
        """Check if request can be served from cache."""
        # Only serve from cache for simple requests
        if page > 0:  # Only first page
            return False
        
        if page_size > len(self._log_cache):  # Cache doesn't have enough logs
            return False
        
        # Check for complex filters that require storage query
        complex_filters = ['start_date', 'end_date', 'query']
        if any(key in filters for key in complex_filters):
            return False
        
        return True
    
    def _get_from_cache(self, page: int, page_size: int, filters: Dict[str, Any]) -> List[ExecutionLog]:
        """Get logs from memory cache."""
        with self._cache_lock:
            filtered_logs = self._log_cache.copy()
            
            # Apply simple filters
            if 'schedule_name' in filters:
                schedule_name = filters['schedule_name']
                filtered_logs = [log for log in filtered_logs if log.schedule_name == schedule_name]
            
            if 'success' in filters:
                success = filters['success']
                filtered_logs = [log for log in filtered_logs if log.result.success == success]
            
            if 'operation' in filters:
                operation = filters['operation']
                filtered_logs = [log for log in filtered_logs if log.result.operation == operation]
            
            # Apply pagination
            start_idx = page * page_size
            end_idx = start_idx + page_size
            
            return filtered_logs[start_idx:end_idx]
    
    def search_logs(self, query: str, limit: int = 100) -> List[ExecutionLog]:
        """
        Search logs by query string.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching ExecutionLog objects
        """
        try:
            return self.storage.search_logs(query)[:limit]
        except Exception as e:
            self.logger.error(f"Error searching logs: {e}")
            return []
    
    def export_logs(self, logs: List[ExecutionLog], format: str, file_path: str) -> bool:
        """
        Export logs to file.
        
        Args:
            logs: List of logs to export
            format: Export format ('json', 'csv', 'txt')
            file_path: Output file path
            
        Returns:
            True if export was successful
        """
        try:
            return self.storage.export_logs(logs, format, file_path)
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return False
    
    def clear_old_logs(self, before_date: datetime) -> bool:
        """
        Clear logs before a specific date.
        
        Args:
            before_date: Delete logs before this date
            
        Returns:
            True if clearing was successful
        """
        try:
            success = self.storage.delete_logs(before_date)
            
            if success:
                # Remove from cache as well
                with self._cache_lock:
                    self._log_cache = [
                        log for log in self._log_cache 
                        if log.execution_time >= before_date
                    ]
                
                # Invalidate stats cache
                self._invalidate_stats_cache()
                
                self.logger.info(f"Cleared logs before {before_date}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error clearing old logs: {e}")
            return False
    
    def get_execution_statistics(self, force_refresh: bool = False) -> ExecutionStatistics:
        """
        Get execution statistics.
        
        Args:
            force_refresh: Force refresh of statistics cache
            
        Returns:
            ExecutionStatistics object
        """
        # Check cache first
        if not force_refresh and self._is_stats_cache_valid():
            return self._stats_cache
        
        try:
            # Calculate statistics from recent logs
            with self._cache_lock:
                logs = self._log_cache.copy()
            
            if not logs:
                return ExecutionStatistics.empty_stats()
            
            # Calculate basic statistics
            total_executions = len(logs)
            successful_executions = sum(1 for log in logs if log.result.success)
            failed_executions = total_executions - successful_executions
            
            # Calculate average duration
            total_duration = sum((log.duration for log in logs), timedelta())
            average_duration = total_duration / total_executions if total_executions > 0 else timedelta()
            
            # Find most frequent errors
            error_messages = [
                log.result.message for log in logs 
                if not log.result.success and log.result.message
            ]
            error_counter = Counter(error_messages)
            most_frequent_errors = [error for error, count in error_counter.most_common(5)]
            
            # Create statistics object
            stats = ExecutionStatistics(
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                average_duration=average_duration,
                most_frequent_errors=most_frequent_errors
            )
            
            # Update cache
            self._stats_cache = stats
            self._stats_cache_time = datetime.now()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating execution statistics: {e}")
            return ExecutionStatistics.empty_stats()
    
    def _is_stats_cache_valid(self) -> bool:
        """Check if statistics cache is still valid."""
        if not self._stats_cache or not self._stats_cache_time:
            return False
        
        return datetime.now() - self._stats_cache_time < self._stats_cache_duration
    
    def _invalidate_stats_cache(self) -> None:
        """Invalidate statistics cache."""
        self._stats_cache = None
        self._stats_cache_time = None
    
    def get_logs_by_schedule(self, schedule_name: str, limit: int = 100) -> List[ExecutionLog]:
        """
        Get logs for a specific schedule.
        
        Args:
            schedule_name: Name of the schedule
            limit: Maximum number of logs to return
            
        Returns:
            List of ExecutionLog objects
        """
        filters = {'schedule_name': schedule_name}
        return self.get_logs(0, limit, filters)
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 1000) -> List[ExecutionLog]:
        """
        Get logs within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of logs to return
            
        Returns:
            List of ExecutionLog objects
        """
        filters = {
            'start_date': start_date.date(),
            'end_date': end_date.date()
        }
        return self.get_logs(0, limit, filters)
    
    def get_failed_logs(self, limit: int = 100) -> List[ExecutionLog]:
        """
        Get failed execution logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of failed ExecutionLog objects
        """
        filters = {'success': False}
        return self.get_logs(0, limit, filters)
    
    def get_recent_activity(self, hours: int = 24, limit: int = 50) -> List[ExecutionLog]:
        """
        Get recent activity logs.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of logs to return
            
        Returns:
            List of recent ExecutionLog objects
        """
        start_date = datetime.now() - timedelta(hours=hours)
        end_date = datetime.now()
        
        return self.get_logs_by_date_range(start_date, end_date, limit)
    
    def get_schedule_statistics(self, schedule_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific schedule.
        
        Args:
            schedule_name: Name of the schedule
            
        Returns:
            Dictionary containing schedule statistics
        """
        try:
            logs = self.get_logs_by_schedule(schedule_name, 1000)
            
            if not logs:
                return {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'success_rate': 0.0,
                    'average_duration': 0.0,
                    'last_execution': None,
                    'last_success': None,
                    'last_failure': None
                }
            
            total = len(logs)
            successful = sum(1 for log in logs if log.result.success)
            failed = total - successful
            
            # Calculate average duration
            total_duration = sum((log.duration for log in logs), timedelta())
            avg_duration = total_duration.total_seconds() / total if total > 0 else 0.0
            
            # Find last execution times
            last_execution = logs[0].execution_time if logs else None
            last_success = next((log.execution_time for log in logs if log.result.success), None)
            last_failure = next((log.execution_time for log in logs if not log.result.success), None)
            
            return {
                'total_executions': total,
                'successful_executions': successful,
                'failed_executions': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0.0,
                'average_duration': avg_duration,
                'last_execution': last_execution.isoformat() if last_execution else None,
                'last_success': last_success.isoformat() if last_success else None,
                'last_failure': last_failure.isoformat() if last_failure else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting schedule statistics for {schedule_name}: {e}")
            return {}
    
    def get_daily_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily execution statistics for the past N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            List of daily statistics dictionaries
        """
        try:
            daily_stats = []
            
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                start_datetime = datetime.combine(date, datetime.min.time())
                end_datetime = datetime.combine(date, datetime.max.time())
                
                logs = self.get_logs_by_date_range(start_datetime, end_datetime)
                
                total = len(logs)
                successful = sum(1 for log in logs if log.result.success)
                failed = total - successful
                
                daily_stats.append({
                    'date': date.isoformat(),
                    'total_executions': total,
                    'successful_executions': successful,
                    'failed_executions': failed,
                    'success_rate': (successful / total * 100) if total > 0 else 0.0
                })
            
            return daily_stats
            
        except Exception as e:
            self.logger.error(f"Error getting daily statistics: {e}")
            return []
    
    def get_error_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get summary of most common errors.
        
        Args:
            limit: Maximum number of error types to return
            
        Returns:
            List of error summary dictionaries
        """
        try:
            failed_logs = self.get_failed_logs(1000)
            
            # Count error messages
            error_counter = Counter()
            error_details = defaultdict(list)
            
            for log in failed_logs:
                error_msg = log.result.message
                error_counter[error_msg] += 1
                error_details[error_msg].append({
                    'schedule_name': log.schedule_name,
                    'execution_time': log.execution_time.isoformat(),
                    'operation': log.result.operation,
                    'target': log.result.target
                })
            
            # Create summary
            error_summary = []
            for error_msg, count in error_counter.most_common(limit):
                error_summary.append({
                    'error_message': error_msg,
                    'count': count,
                    'percentage': (count / len(failed_logs) * 100) if failed_logs else 0.0,
                    'recent_occurrences': error_details[error_msg][:5]  # Last 5 occurrences
                })
            
            return error_summary
            
        except Exception as e:
            self.logger.error(f"Error getting error summary: {e}")
            return []
    
    def generate_execution_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate comprehensive execution report for a date range.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary containing comprehensive report data
        """
        try:
            logs = self.get_logs_by_date_range(start_date, end_date, 10000)
            
            if not logs:
                return {
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'duration_days': (end_date - start_date).days
                    },
                    'summary': {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'success_rate': 0.0,
                        'unique_schedules': 0
                    },
                    'schedule_breakdown': [],
                    'daily_breakdown': [],
                    'error_analysis': [],
                    'performance_metrics': {}
                }
            
            # Basic summary
            total = len(logs)
            successful = sum(1 for log in logs if log.result.success)
            failed = total - successful
            unique_schedules = len(set(log.schedule_name for log in logs))
            
            # Schedule breakdown
            schedule_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0})
            for log in logs:
                schedule_stats[log.schedule_name]['total'] += 1
                if log.result.success:
                    schedule_stats[log.schedule_name]['successful'] += 1
                else:
                    schedule_stats[log.schedule_name]['failed'] += 1
            
            schedule_breakdown = []
            for schedule_name, stats in schedule_stats.items():
                schedule_breakdown.append({
                    'schedule_name': schedule_name,
                    'total_executions': stats['total'],
                    'successful_executions': stats['successful'],
                    'failed_executions': stats['failed'],
                    'success_rate': (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
                })
            
            # Daily breakdown
            daily_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0})
            for log in logs:
                date_key = log.execution_time.date().isoformat()
                daily_stats[date_key]['total'] += 1
                if log.result.success:
                    daily_stats[date_key]['successful'] += 1
                else:
                    daily_stats[date_key]['failed'] += 1
            
            daily_breakdown = []
            for date_str, stats in sorted(daily_stats.items()):
                daily_breakdown.append({
                    'date': date_str,
                    'total_executions': stats['total'],
                    'successful_executions': stats['successful'],
                    'failed_executions': stats['failed'],
                    'success_rate': (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
                })
            
            # Error analysis
            failed_logs = [log for log in logs if not log.result.success]
            error_counter = Counter(log.result.message for log in failed_logs)
            error_analysis = [
                {
                    'error_message': error_msg,
                    'count': count,
                    'percentage': (count / len(failed_logs) * 100) if failed_logs else 0.0
                }
                for error_msg, count in error_counter.most_common(10)
            ]
            
            # Performance metrics
            durations = [log.duration.total_seconds() for log in logs]
            performance_metrics = {
                'average_duration': sum(durations) / len(durations) if durations else 0.0,
                'min_duration': min(durations) if durations else 0.0,
                'max_duration': max(durations) if durations else 0.0,
                'total_execution_time': sum(durations)
            }
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': (end_date - start_date).days
                },
                'summary': {
                    'total_executions': total,
                    'successful_executions': successful,
                    'failed_executions': failed,
                    'success_rate': (successful / total * 100) if total > 0 else 0.0,
                    'unique_schedules': unique_schedules
                },
                'schedule_breakdown': schedule_breakdown,
                'daily_breakdown': daily_breakdown,
                'error_analysis': error_analysis,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error generating execution report: {e}")
            return {}
    
    def add_log_added_callback(self, callback: Callable[[ExecutionLog], None]) -> None:
        """Add callback for log added events."""
        self._log_added_callbacks.append(callback)
    
    def remove_log_added_callback(self, callback: Callable[[ExecutionLog], None]) -> None:
        """Remove callback for log added events."""
        if callback in self._log_added_callbacks:
            self._log_added_callbacks.remove(callback)
    
    def _notify_log_added(self, log: ExecutionLog) -> None:
        """Notify callbacks that a log was added."""
        for callback in self._log_added_callbacks:
            try:
                callback(log)
            except Exception as e:
                self.logger.error(f"Error in log added callback: {e}")
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get log storage statistics."""
        try:
            return self.storage.get_statistics()
        except Exception as e:
            self.logger.error(f"Error getting storage statistics: {e}")
            return {}
    
    def cleanup_logs(self) -> Dict[str, Any]:
        """
        Perform log cleanup based on configuration.
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            config = self.config_manager.get_config()
            retention_days = config.log_retention_days
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Get count before cleanup
            old_logs = self.get_logs_by_date_range(
                datetime.min, 
                cutoff_date, 
                10000
            )
            old_count = len(old_logs)
            
            # Perform cleanup
            success = self.clear_old_logs(cutoff_date)
            
            result = {
                'success': success,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'logs_removed': old_count if success else 0
            }
            
            if success:
                self.logger.info(f"Log cleanup completed: removed {old_count} logs older than {retention_days} days")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {e}")
            return {'success': False, 'error': str(e)}


# Global log manager instance
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """
    Get the global log manager instance.
    
    Returns:
        LogManager instance
    """
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager


def initialize_log_manager(storage: Optional[LogStorage] = None) -> LogManager:
    """
    Initialize the global log manager.
    
    Args:
        storage: Optional custom storage instance
        
    Returns:
        LogManager instance
    """
    global _log_manager
    _log_manager = LogManager(storage)
    return _log_manager