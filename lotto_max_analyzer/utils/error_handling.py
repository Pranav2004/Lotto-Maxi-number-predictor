"""Comprehensive error handling utilities for Lotto Max Analyzer."""

import logging
import traceback
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime
import sqlite3
import requests


class LottoMaxError(Exception):
    """Base exception for Lotto Max Analyzer."""
    pass


class DataError(LottoMaxError):
    """Exception for data-related errors."""
    pass


class NetworkError(LottoMaxError):
    """Exception for network-related errors."""
    pass


class AnalysisError(LottoMaxError):
    """Exception for analysis-related errors."""
    pass


class ValidationError(LottoMaxError):
    """Exception for validation errors."""
    pass


class ConfigurationError(LottoMaxError):
    """Exception for configuration errors."""
    pass


class ErrorHandler:
    """Comprehensive error handling and recovery system."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = {}
    
    def handle_database_error(self, error: Exception, operation: str = "database operation") -> Optional[Any]:
        """
        Handle database-related errors with recovery strategies.
        
        Args:
            error: The database error that occurred
            operation: Description of the operation that failed
            
        Returns:
            None or recovery result
        """
        self.logger.error(f"Database error during {operation}: {error}")
        
        if isinstance(error, sqlite3.OperationalError):
            if "database is locked" in str(error).lower():
                self.logger.warning("Database is locked, retrying in 1 second...")
                time.sleep(1)
                return "retry"
            elif "no such table" in str(error).lower():
                self.logger.warning("Database table missing, attempting to recreate...")
                return "recreate_tables"
            elif "disk full" in str(error).lower():
                raise DataError("Database storage is full. Please free up disk space.")
        
        elif isinstance(error, sqlite3.IntegrityError):
            if "unique constraint" in str(error).lower():
                self.logger.warning("Duplicate data detected, skipping...")
                return "skip_duplicate"
        
        elif isinstance(error, sqlite3.DatabaseError):
            if "database disk image is malformed" in str(error).lower():
                raise DataError("Database file is corrupted. Please delete and recreate the database.")
        
        # Generic database error
        raise DataError(f"Database operation failed: {error}")
    
    def handle_network_error(self, error: Exception, url: str = "", retry_count: int = 0) -> str:
        """
        Handle network-related errors with retry logic.
        
        Args:
            error: The network error that occurred
            url: URL that failed (if applicable)
            retry_count: Current retry attempt
            
        Returns:
            Action to take ('retry', 'fallback', 'fail')
        """
        self.logger.error(f"Network error for {url}: {error}")
        
        if isinstance(error, requests.exceptions.ConnectionError):
            if retry_count < 3:
                delay = 2 ** retry_count  # Exponential backoff
                self.logger.warning(f"Connection failed, retrying in {delay} seconds...")
                time.sleep(delay)
                return "retry"
            else:
                self.logger.error("Max retries exceeded for connection")
                return "fallback"
        
        elif isinstance(error, requests.exceptions.Timeout):
            if retry_count < 2:
                self.logger.warning("Request timed out, retrying with longer timeout...")
                return "retry"
            else:
                return "fallback"
        
        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = getattr(error.response, 'status_code', None)
            if status_code == 429:  # Rate limited
                self.logger.warning("Rate limited, waiting before retry...")
                time.sleep(60)  # Wait 1 minute
                return "retry" if retry_count < 2 else "fallback"
            elif status_code in [500, 502, 503, 504]:  # Server errors
                if retry_count < 3:
                    self.logger.warning(f"Server error {status_code}, retrying...")
                    time.sleep(5)
                    return "retry"
                else:
                    return "fallback"
            elif status_code == 404:
                self.logger.error("Resource not found")
                return "fallback"
            else:
                self.logger.error(f"HTTP error {status_code}")
                return "fail"
        
        elif isinstance(error, requests.exceptions.RequestException):
            if retry_count < 2:
                self.logger.warning("Request failed, retrying...")
                time.sleep(1)
                return "retry"
            else:
                return "fallback"
        
        # Unknown network error
        self.logger.error(f"Unknown network error: {error}")
        return "fail"
    
    def handle_analysis_error(self, error: Exception, operation: str = "analysis") -> Optional[Any]:
        """
        Handle analysis-related errors.
        
        Args:
            error: The analysis error that occurred
            operation: Description of the analysis operation
            
        Returns:
            Recovery action or None
        """
        self.logger.error(f"Analysis error during {operation}: {error}")
        
        if isinstance(error, (ZeroDivisionError, ValueError)):
            if "insufficient data" in str(error).lower():
                raise AnalysisError(
                    "Not enough data for analysis. Please fetch more historical data or "
                    "adjust the date range to include more draws."
                )
            elif "division by zero" in str(error).lower():
                self.logger.warning("Division by zero in analysis, using fallback calculation")
                return "use_fallback"
        
        elif isinstance(error, MemoryError):
            raise AnalysisError(
                "Analysis requires too much memory. Try reducing the date range or "
                "processing data in smaller chunks."
            )
        
        elif isinstance(error, OverflowError):
            raise AnalysisError(
                "Numerical overflow in analysis. The dataset may be too large or "
                "contain extreme values."
            )
        
        # Generic analysis error
        raise AnalysisError(f"Analysis failed: {error}")
    
    def handle_file_error(self, error: Exception, file_path: str = "", operation: str = "file operation") -> str:
        """
        Handle file-related errors.
        
        Args:
            error: The file error that occurred
            file_path: Path to the file that caused the error
            operation: Description of the file operation
            
        Returns:
            Action to take ('retry', 'create_dir', 'fail')
        """
        self.logger.error(f"File error during {operation} on {file_path}: {error}")
        
        if isinstance(error, FileNotFoundError):
            if "directory" in str(error).lower() or "folder" in str(error).lower():
                self.logger.warning("Directory not found, attempting to create...")
                return "create_dir"
            else:
                raise DataError(f"File not found: {file_path}")
        
        elif isinstance(error, PermissionError):
            raise DataError(
                f"Permission denied accessing {file_path}. "
                f"Please check file permissions or run with appropriate privileges."
            )
        
        elif isinstance(error, OSError) and error.errno == 28:  # No space left on device
            raise DataError(
                f"No space left on device. Please free up disk space before continuing."
            )
        
        elif isinstance(error, IsADirectoryError):
            raise DataError(f"Expected file but found directory: {file_path}")
        
        elif isinstance(error, NotADirectoryError):
            raise DataError(f"Expected directory but found file: {file_path}")
        
        # Generic file error
        raise DataError(f"File operation failed: {error}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log error with context information.
        
        Args:
            error: The error that occurred
            context: Additional context information
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Track error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = {
            'timestamp': datetime.now(),
            'message': error_msg,
            'context': context or {}
        }
        
        # Log with full context
        log_msg = f"{error_type}: {error_msg}"
        if context:
            log_msg += f" | Context: {context}"
        
        self.logger.error(log_msg)
        
        # Log stack trace for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors that have occurred.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'error_counts': self.error_counts.copy(),
            'last_errors': self.last_errors.copy(),
            'total_errors': sum(self.error_counts.values())
        }


def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator for retrying functions on specific exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return=None, 
                log_errors: bool = True, **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        default_return: Value to return if function fails
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if failed
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logging.error(f"Safe execution failed for {func.__name__}: {e}")
        return default_return


def validate_and_handle_errors(validation_func: Callable) -> Callable:
    """
    Decorator that validates inputs and handles validation errors.
    
    Args:
        validation_func: Function to validate inputs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate inputs
                validation_func(*args, **kwargs)
                # Execute original function
                return func(*args, **kwargs)
            except ValidationError as e:
                logging.error(f"Validation failed for {func.__name__}: {e}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error in {func.__name__}: {e}")
                raise LottoMaxError(f"Operation failed: {e}") from e
        
        return wrapper
    return decorator


# Global error handler instance
error_handler = ErrorHandler()


def handle_database_error(error: Exception, operation: str = "database operation") -> Optional[Any]:
    """Convenience function for handling database errors."""
    return error_handler.handle_database_error(error, operation)


def handle_network_error(error: Exception, url: str = "", retry_count: int = 0) -> str:
    """Convenience function for handling network errors."""
    return error_handler.handle_network_error(error, url, retry_count)


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Convenience function for logging errors."""
    return error_handler.log_error(error, context)