"""
Action sequence executor for executing action sequences with proper error handling and timing.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.action_step import ActionStep, ExecutionOptions
from ..models.execution import ExecutionResult
from .windows_controller import WindowsController


class ActionSequenceExecutor:
    """Executor for action sequences with support for delays, error handling, and timeouts."""
    
    def __init__(self, windows_controller: WindowsController):
        """
        Initialize the action sequence executor.
        
        Args:
            windows_controller: Windows controller instance for executing actions
        """
        self.windows_controller = windows_controller
    
    def execute_sequence(self, action_sequence: List[ActionStep], 
                        execution_options: ExecutionOptions,
                        target_app: str = "") -> ExecutionResult:
        """
        Execute a sequence of actions with proper timing and error handling.
        
        Args:
            action_sequence: List of action steps to execute
            execution_options: Options controlling execution behavior
            target_app: Target application name for context
            
        Returns:
            ExecutionResult: Overall result of the sequence execution
        """
        if not action_sequence:
            return ExecutionResult.failure_result(
                operation="execute_sequence",
                target=target_app,
                message="Action sequence is empty"
            )
        
        start_time = datetime.now()
        executed_steps = []
        failed_steps = []
        
        try:
            for i, step in enumerate(action_sequence):
                step_start_time = datetime.now()
                
                # Check timeout
                if execution_options.max_execution_time:
                    elapsed = datetime.now() - start_time
                    if elapsed >= execution_options.max_execution_time:
                        return ExecutionResult.failure_result(
                            operation="execute_sequence",
                            target=target_app,
                            message=f"Sequence execution timed out after {elapsed.total_seconds():.2f} seconds",
                            details={
                                "executed_steps": len(executed_steps),
                                "total_steps": len(action_sequence),
                                "timeout": execution_options.max_execution_time.total_seconds()
                            }
                        )
                
                # Execute the action step
                result = self._execute_single_step(step, target_app)
                
                step_duration = datetime.now() - step_start_time
                step_info = {
                    "step_index": i,
                    "step_id": step.id,
                    "action_type": step.action_type.value,
                    "duration": step_duration.total_seconds(),
                    "success": result.success,
                    "message": result.message
                }
                
                if result.success:
                    executed_steps.append(step_info)
                    
                    # Apply delay after successful execution
                    delay = step.delay_after or execution_options.default_delay_between_actions
                    if delay.total_seconds() > 0:
                        time.sleep(delay.total_seconds())
                        
                else:
                    failed_steps.append(step_info)
                    
                    # Handle failure based on options
                    if execution_options.stop_on_first_error or not step.continue_on_error:
                        return ExecutionResult.failure_result(
                            operation="execute_sequence",
                            target=target_app,
                            message=f"Sequence stopped at step {i+1}: {result.message}",
                            details={
                                "failed_step": step_info,
                                "executed_steps": executed_steps,
                                "failed_steps": failed_steps,
                                "total_steps": len(action_sequence)
                            }
                        )
                    
                    # If retry is enabled, try once more
                    if execution_options.retry_failed_actions:
                        retry_result = self._execute_single_step(step, target_app)
                        if retry_result.success:
                            step_info["retried"] = True
                            step_info["success"] = True
                            step_info["message"] = f"Succeeded on retry: {retry_result.message}"
                            executed_steps.append(step_info)
                            
                            # Apply delay after successful retry
                            delay = step.delay_after or execution_options.default_delay_between_actions
                            if delay.total_seconds() > 0:
                                time.sleep(delay.total_seconds())
                        else:
                            step_info["retried"] = True
                            step_info["retry_message"] = retry_result.message
                            # Continue with next step if continue_on_error is True
            
            # Calculate overall result
            total_duration = datetime.now() - start_time
            success_count = len(executed_steps)
            failure_count = len(failed_steps)
            
            if failure_count == 0:
                return ExecutionResult.success_result(
                    operation="execute_sequence",
                    target=target_app,
                    message=f"Successfully executed all {success_count} steps in {total_duration.total_seconds():.2f} seconds",
                    details={
                        "executed_steps": executed_steps,
                        "total_steps": len(action_sequence),
                        "duration": total_duration.total_seconds(),
                        "success_rate": 1.0
                    }
                )
            else:
                success_rate = success_count / len(action_sequence)
                if success_rate >= 0.5:  # Consider partial success if more than half succeeded
                    return ExecutionResult.success_result(
                        operation="execute_sequence",
                        target=target_app,
                        message=f"Partially successful: {success_count}/{len(action_sequence)} steps completed",
                        details={
                            "executed_steps": executed_steps,
                            "failed_steps": failed_steps,
                            "total_steps": len(action_sequence),
                            "duration": total_duration.total_seconds(),
                            "success_rate": success_rate
                        }
                    )
                else:
                    return ExecutionResult.failure_result(
                        operation="execute_sequence",
                        target=target_app,
                        message=f"Sequence mostly failed: {failure_count}/{len(action_sequence)} steps failed",
                        details={
                            "executed_steps": executed_steps,
                            "failed_steps": failed_steps,
                            "total_steps": len(action_sequence),
                            "duration": total_duration.total_seconds(),
                            "success_rate": success_rate
                        }
                    )
        
        except Exception as e:
            total_duration = datetime.now() - start_time
            return ExecutionResult.failure_result(
                operation="execute_sequence",
                target=target_app,
                message=f"Exception occurred during sequence execution: {str(e)}",
                details={
                    "exception": str(e),
                    "executed_steps": executed_steps,
                    "failed_steps": failed_steps,
                    "duration": total_duration.total_seconds()
                }
            )
    
    def _execute_single_step(self, step: ActionStep, target_app: str) -> ExecutionResult:
        """
        Execute a single action step.
        
        Args:
            step: Action step to execute
            target_app: Target application name for context
            
        Returns:
            ExecutionResult: Result of the step execution
        """
        try:
            # Validate step before execution
            if not step.validate():
                return ExecutionResult.failure_result(
                    operation=step.action_type.value,
                    target=target_app,
                    message=f"Action step validation failed: {step.id}"
                )
            
            # Execute the action using the windows controller
            result = self.windows_controller.execute_action(step.action_type, step.action_params)
            
            # Add step-specific information to the result
            if result.details is None:
                result.details = {}
            result.details.update({
                "step_id": step.id,
                "step_description": step.description,
                "continue_on_error": step.continue_on_error,
                "delay_after": step.delay_after.total_seconds()
            })
            
            return result
            
        except Exception as e:
            return ExecutionResult.failure_result(
                operation=step.action_type.value,
                target=target_app,
                message=f"Exception occurred while executing step {step.id}: {str(e)}",
                details={
                    "exception": str(e),
                    "step_id": step.id,
                    "step_description": step.description
                }
            )
    
    def validate_sequence(self, action_sequence: List[ActionStep]) -> tuple[bool, List[str]]:
        """
        Validate an action sequence before execution.
        
        Args:
            action_sequence: List of action steps to validate
            
        Returns:
            tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        if not action_sequence:
            return False, ["Action sequence is empty"]
        
        errors = []
        
        for i, step in enumerate(action_sequence):
            if not step.validate():
                errors.append(f"Step {i+1} (ID: {step.id}) validation failed")
            
            # Check for reasonable delay values
            if step.delay_after.total_seconds() < 0:
                errors.append(f"Step {i+1} has negative delay: {step.delay_after.total_seconds()}")
            
            if step.delay_after.total_seconds() > 300:  # 5 minutes
                errors.append(f"Step {i+1} has excessive delay: {step.delay_after.total_seconds()} seconds")
        
        return len(errors) == 0, errors
    
    def estimate_execution_time(self, action_sequence: List[ActionStep], 
                               execution_options: ExecutionOptions) -> timedelta:
        """
        Estimate the total execution time for an action sequence.
        
        Args:
            action_sequence: List of action steps
            execution_options: Execution options
            
        Returns:
            timedelta: Estimated execution time
        """
        if not action_sequence:
            return timedelta(0)
        
        total_seconds = 0
        
        for step in action_sequence:
            # Estimate action execution time (rough estimates)
            action_time = self._estimate_action_time(step.action_type)
            total_seconds += action_time
            
            # Add delay time
            delay = step.delay_after or execution_options.default_delay_between_actions
            total_seconds += delay.total_seconds()
        
        return timedelta(seconds=total_seconds)
    
    def _estimate_action_time(self, action_type) -> float:
        """
        Estimate execution time for different action types in seconds.
        
        Args:
            action_type: Type of action
            
        Returns:
            float: Estimated execution time in seconds
        """
        from ..models.action import ActionType
        
        # Rough time estimates based on action complexity
        time_estimates = {
            ActionType.LAUNCH_APP: 3.0,
            ActionType.CLOSE_APP: 1.0,
            ActionType.SWITCH_APP: 0.5,
            ActionType.RESIZE_WINDOW: 0.3,
            ActionType.MOVE_WINDOW: 0.3,
            ActionType.MINIMIZE_WINDOW: 0.2,
            ActionType.MAXIMIZE_WINDOW: 0.2,
            ActionType.FOCUS_WINDOW: 0.3,
            ActionType.CLICK_ABS: 0.2,
            ActionType.DRAG_ELEMENT: 0.5,
            ActionType.MOVE_MOUSE: 0.1,
            ActionType.SCROLL: 0.3,
            ActionType.TYPE_TEXT: 1.0,
            ActionType.SEND_KEYS: 0.2,
            ActionType.PRESS_KEY: 0.1,
            ActionType.CLIPBOARD_COPY: 0.1,
            ActionType.CLIPBOARD_PASTE: 0.2,
            ActionType.GET_DESKTOP_STATE: 2.0,
            ActionType.WAIT: 0.0,  # Wait time is handled separately
            ActionType.SCRAPE_WEBPAGE: 5.0,
            ActionType.CUSTOM_COMMAND: 2.0,
        }
        
        return time_estimates.get(action_type, 1.0)  # Default to 1 second