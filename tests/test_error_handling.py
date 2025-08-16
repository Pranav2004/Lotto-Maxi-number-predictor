"""Tests for error handling utilities."""

import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from lotto_max_analyzer.utils.error_handling import (
    ErrorHandler, LottoMaxError, DataError, NetworkError, 
    AnalysisError, ValidationError, retry_on_network_error,
    safe_operation, validate_inputs
)


class TestErrorHandler:
    """Test the ErrorHandler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_handle_validation_error(self):
        """Test handling of validation errors."""
        exc = ValidationError("Invalid input")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Input validation error: Invalid input" in result
    
    def test_handle_data_error(self):
        """Test handling of data errors."""
        exc = DataError("Data corruption detected")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Data error: Data corruption detected" in result
    
    def test_handle_network_error(self):
        """Test handling of network errors."""
        exc = NetworkError("Connection timeout")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Network error: Connection timeout" in result
    
    def test_handle_analysis_error(self):
        """Test handling of analysis errors."""
        exc = AnalysisError("Insufficient data for analysis")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Analysis error: Insufficient data for analysis" in result
    
    def test_handle_file_not_found_error(self):
        """Test handling of file not found errors."""
        exc = FileNotFoundError("File does not exist")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ File not found: File does not exist" in result
    
    def test_handle_permission_error(self):
        """Test handling of permission errors."""
        exc = PermissionError("Access denied")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Permission denied: Access denied" in result
    
    def test_handle_memory_error(self):
        """Test handling of memory errors."""
        exc = MemoryError("Out of memory")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Out of memory" in result
    
    def test_handle_keyboard_interrupt(self):
        """Test handling of keyboard interrupts."""
        exc = KeyboardInterrupt()
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "⏹️  Operation cancelled by user." in result
    
    def test_handle_generic_error(self):
        """Test handling of generic errors."""
        exc = RuntimeError("Something went wrong")
        result = self.error_handler.handle_exception(exc, "test context")
        
        assert "❌ Unexpected error occurred" in result
        assert "ERR_" in result
    
    def test_safe_execute_success(self):
        """Test safe execution of successful function."""
        def test_func(x, y):
            return x + y
        
        result = self.error_handler.safe_execute(test_func, 2, 3)
        assert result == 5
    
    def test_safe_execute_failure(self):
        """Test safe execution of failing function."""
        def test_func():
            raise ValueError("Test error")
        
        result = self.error_handler.safe_execute(test_func, default="fallback")
        assert result == "fallback"
    
    def test_validate_and_execute_success(self):
        """Test validation and execution with valid inputs."""
        def validator(x):
            if x < 0:
                raise ValidationError("Must be positive")
        
        def test_func(x):
            return x * 2
        
        result = self.error_handler.validate_and_execute(test_func, validator, 5)
        assert result == 10
    
    def test_validate_and_execute_validation_failure(self):
        """Test validation and execution with invalid inputs."""
        def validator(x):
            if x < 0:
                raise ValidationError("Must be positive")
        
        def test_func(x):
            return x * 2
        
        with pytest.raises(ValidationError):
            self.error_handler.validate_and_execute(test_func, validator, -5)
    
    def test_create_fallback_chain_success(self):
        """Test fallback chain with successful first function."""
        def func1():
            return "success"
        
        def func2():
            return "fallback"
        
        fallback_func = self.error_handler.create_fallback_chain(func1, func2)
        result = fallback_func()
        assert result == "success"
    
    def test_create_fallback_chain_fallback(self):
        """Test fallback chain with failing first function."""
        def func1():
            raise ValueError("First function failed")
        
        def func2():
            return "fallback"
        
        fallback_func = self.error_handler.create_fallback_chain(func1, func2)
        result = fallback_func()
        assert result == "fallback"
    
    def test_create_fallback_chain_all_fail(self):
        """Test fallback chain with all functions failing."""
        def func1():
            raise ValueError("First function failed")
        
        def func2():
            raise ValueError("Second function failed")
        
        fallback_func = self.error_handler.create_fallback_chain(func1, func2)
        
        with pytest.raises(ValueError, match="Second function failed"):
            fallback_func()
    
    def test_graceful_shutdown(self):
        """Test graceful shutdown with cleanup functions."""
        cleanup_called = []
        
        def cleanup1():
            cleanup_called.append("cleanup1")
        
        def cleanup2():
            cleanup_called.append("cleanup2")
        
        self.error_handler.graceful_shutdown([cleanup1, cleanup2])
        
        assert cleanup_called == ["cleanup1", "cleanup2"]
    
    def test_graceful_shutdown_with_failing_cleanup(self):
        """Test graceful shutdown with failing cleanup function."""
        cleanup_called = []
        
        def cleanup1():
            cleanup_called.append("cleanup1")
        
        def cleanup2():
            raise RuntimeError("Cleanup failed")
        
        def cleanup3():
            cleanup_called.append("cleanup3")
        
        # Should not raise exception
        self.error_handler.graceful_shutdown([cleanup1, cleanup2, cleanup3])
        
        assert cleanup_called == ["cleanup1", "cleanup3"]
    
    def test_log_performance_warning(self, caplog):
        """Test performance warning logging."""
        with caplog.at_level(logging.WARNING):
            self.error_handler.log_performance_warning("test operation", 15.0, 10.0)
        
        assert "Performance warning" in caplog.text
        assert "test operation took 15.00 seconds" in caplog.text
    
    def test_no_performance_warning_under_threshold(self, caplog):
        """Test no performance warning when under threshold."""
        with caplog.at_level(logging.WARNING):
            self.error_handler.log_performance_warning("test operation", 5.0, 10.0)
        
        assert "Performance warning" not in caplog.text
    
    def test_create_error_context(self):
        """Test error context creation."""
        context = self.error_handler.create_error_context(
            operation="test_op",
            user_id="123",
            data_size=1000
        )
        
        assert "timestamp" in context
        assert "context" in context
        assert "stack_trace" in context
        assert context["context"]["operation"] == "test_op"
        assert context["context"]["user_id"] == "123"
        assert context["context"]["data_size"] == 1000


class TestRetryDecorator:
    """Test the retry decorator."""
    
    def test_retry_success_first_attempt(self):
        """Test retry decorator with successful first attempt."""
        call_count = 0
        
        @retry_on_network_error(max_retries=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test retry decorator with success after failures."""
        call_count = 0
        
        @retry_on_network_error(max_retries=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network failed")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test retry decorator when max attempts exceeded."""
        call_count = 0
        
        @retry_on_network_error(max_retries=2)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Network failed")
        
        with pytest.raises(NetworkError):
            test_func()
        
        assert call_count == 3  # Initial attempt + 2 retries


class TestSafeOperationDecorator:
    """Test the safe operation decorator."""
    
    def test_safe_operation_success(self):
        """Test safe operation decorator with successful function."""
        @safe_operation(default="fallback")
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_safe_operation_failure(self):
        """Test safe operation decorator with failing function."""
        @safe_operation(default="fallback")
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        assert result == "fallback"


class TestValidateInputsDecorator:
    """Test the validate inputs decorator."""
    
    def test_validate_inputs_success(self):
        """Test validate inputs decorator with valid inputs."""
        def validator(x):
            if x < 0:
                raise ValidationError("Must be positive")
        
        @validate_inputs(validator)
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_validate_inputs_failure(self):
        """Test validate inputs decorator with invalid inputs."""
        def validator(x):
            if x < 0:
                raise ValidationError("Must be positive")
        
        @validate_inputs(validator)
        def test_func(x):
            return x * 2
        
        with pytest.raises(ValidationError):
            test_func(-5)