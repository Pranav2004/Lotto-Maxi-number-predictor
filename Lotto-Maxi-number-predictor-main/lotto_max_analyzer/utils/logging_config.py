"""Logging configuration for Lotto Max Analyzer."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from ..config import LOG_LEVEL, LOG_FORMAT


def setup_logging(level: str = None, log_file: Optional[Path] = None, 
                 console_output: bool = True, file_output: bool = True) -> logging.Logger:
    """
    Setup comprehensive logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: ~/.lotto_max_analyzer/logs/app.log)
        console_output: Whether to output to console
        file_output: Whether to output to file
        
    Returns:
        Configured logger
    """
    # Set logging level
    if level is None:
        level = LOG_LEVEL
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger('lotto_max_analyzer')
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        if log_file is None:
            log_dir = Path.home() / '.lotto_max_analyzer' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'app.log'
        
        try:
            # Use rotating file handler to prevent huge log files
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB max, 5 backups
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # If we can't write to the log file, just log to console
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            root_logger.warning(f"Could not setup file logging: {e}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'lotto_max_analyzer.{name}')


def set_log_level(level: str):
    """
    Change the logging level for all loggers.
    
    Args:
        level: New logging level
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Update root logger
    root_logger = logging.getLogger('lotto_max_analyzer')
    root_logger.setLevel(numeric_level)
    
    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)


def log_system_info():
    """Log system information for debugging."""
    import platform
    import sys
    
    logger = get_logger('system')
    logger.info("=== System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Python Executable: {sys.executable}")
    logger.info("===========================")