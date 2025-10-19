"""
Logging configuration for Eir application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import os

from core.config import get_config


class EirLogFormatter(logging.Formatter):
    """Custom formatter for Eir logs with color support"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True, include_module: bool = True):
        self.use_colors = use_colors and sys.stdout.isatty()
        self.include_module = include_module
        
        if self.include_module:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        else:
            fmt = '%(asctime)s - %(levelname)s - %(message)s'
            
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors"""
        # Add extra context for certain modules
        if hasattr(record, 'pathname'):
            # Shorten module names for readability
            module_parts = Path(record.pathname).parts
            if 'eir-fresh' in module_parts:
                idx = module_parts.index('eir-fresh')
                if idx + 1 < len(module_parts):
                    record.name = '.'.join(module_parts[idx+1:]).replace('.py', '')
        
        formatted = super().format(record)
        
        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            # Only colorize the level name
            formatted = formatted.replace(
                record.levelname, 
                f"{color}{record.levelname}{reset}"
            )
        
        return formatted


class PerformanceLogFilter(logging.Filter):
    """Filter to add performance context to logs"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add performance context if available
        if hasattr(record, 'timing'):
            record.msg = f"{record.msg} (took {record.timing:.3f}s)"
        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    max_log_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (uses config default if None)
        console_output: Enable console logging
        file_output: Enable file logging
        max_log_size: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured root logger
    """
    config = get_config()
    
    # Determine log level
    if log_level is None:
        log_level = config.development.log_level
    
    # Determine log file path
    if log_file is None and file_output:
        log_file = config.get_log_path()
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    handlers = []
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = EirLogFormatter(use_colors=True, include_module=True)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(PerformanceLogFilter())
        handlers.append(console_handler)
    
    # File handler with rotation
    if file_output and log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_formatter = EirLogFormatter(use_colors=False, include_module=True)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(PerformanceLogFilter())
        handlers.append(file_handler)
    
    # Add all handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Log startup information
    logger = logging.getLogger('eir.startup')
    logger.info(f"Logging initialized - Level: {log_level}, Console: {console_output}, File: {file_output}")
    if log_file and file_output:
        logger.info(f"Log file: {log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_performance(func_name: str, elapsed_time: float, logger: Optional[logging.Logger] = None) -> None:
    """
    Log performance information.
    
    Args:
        func_name: Name of the function/operation
        elapsed_time: Time elapsed in seconds
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = logging.getLogger('eir.performance')
    
    # Create log record with timing information
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=f"Performance: {func_name}",
        args=(),
        exc_info=None
    )
    record.timing = elapsed_time
    logger.handle(record)


def log_user_action(action: str, details: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None) -> None:
    """
    Log user actions for analytics and debugging.
    
    Args:
        action: Description of the user action
        details: Additional details about the action
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = logging.getLogger('eir.user_actions')
    
    message = f"User action: {action}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        message += f" ({detail_str})"
    
    logger.info(message)


def log_error_with_context(
    error: Exception, 
    context: str, 
    user_data: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log errors with additional context information.
    
    Args:
        error: The exception that occurred
        context: Context description (e.g., "loading model", "saving file")
        user_data: User data that might be relevant (sanitized)
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = logging.getLogger('eir.errors')
    
    message = f"Error during {context}: {type(error).__name__}: {str(error)}"
    
    if user_data:
        # Sanitize user data - remove sensitive information
        sanitized_data = {}
        for key, value in user_data.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'key', 'token', 'secret']):
                sanitized_data[key] = '[REDACTED]'
            else:
                sanitized_data[key] = str(value)[:100]  # Limit length
        
        if sanitized_data:
            detail_str = ", ".join(f"{k}={v}" for k, v in sanitized_data.items())
            message += f" | Context: {detail_str}"
    
    logger.error(message, exc_info=True)


def configure_external_loggers() -> None:
    """Configure logging for external libraries"""
    # Reduce verbosity of external libraries
    external_loggers = [
        'urllib3',
        'requests',
        'matplotlib',
        'PIL',
        'networkx'
    ]
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Special handling for Qt/PySide6 if available
    try:
        qt_logger = logging.getLogger('PySide6')
        qt_logger.setLevel(logging.WARNING)
    except:
        pass


def setup_debug_logging() -> None:
    """Set up enhanced logging for debugging"""
    config = get_config()
    
    if config.development.debug_mode:
        # Enable debug level logging
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Add debug handler for specific modules
        debug_modules = ['eir.models', 'eir.file_io', 'eir.ui', 'eir.ai']
        for module_name in debug_modules:
            logger = logging.getLogger(module_name)
            logger.setLevel(logging.DEBUG)
        
        logger = logging.getLogger('eir.debug')
        logger.debug("Debug logging enabled")


class LoggingContext:
    """Context manager for logging with additional context"""
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        self.operation = operation
        self.logger = logger or logging.getLogger('eir.operations')
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} (took {elapsed:.3f}s)")
        else:
            self.logger.error(f"Failed: {self.operation} after {elapsed:.3f}s - {exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions


def initialize_logging() -> logging.Logger:
    """Initialize the complete logging system"""
    # Setup main logging
    logger = setup_logging()
    
    # Configure external libraries
    configure_external_loggers()
    
    # Setup debug logging if enabled
    setup_debug_logging()
    
    return logger


# Convenience decorators
def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator to log function calls with timing"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(f'eir.{func.__module__}')
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                log_performance(func.__name__, elapsed, func_logger)
                return result
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                log_error_with_context(
                    e, 
                    f"calling {func.__name__}", 
                    {'elapsed_time': elapsed}, 
                    func_logger
                )
                raise
        return wrapper
    return decorator