"""
Unit tests for core.logging_config module
"""

import unittest
import sys
import os
import logging
import tempfile
import io
from pathlib import Path
from unittest.mock import patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logging_config import (
    EirLogFormatter, PerformanceLogFilter, LoggingContext,
    setup_logging, get_logger, log_performance, log_error_with_context,
    log_function_call, log_user_action
)


class TestEirLogFormatter(unittest.TestCase):
    """Test cases for EirLogFormatter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.formatter = EirLogFormatter()
        self.record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
    
    def test_format_basic_message(self):
        """Test basic message formatting"""
        formatted = self.formatter.format(self.record)
        
        # Should contain timestamp, level, module, and message
        self.assertIn("INFO", formatted)
        self.assertIn("test", formatted)  # module name
        self.assertIn("Test message", formatted)
    
    def test_format_with_colors(self):
        """Test message formatting with colors enabled"""
        formatter = EirLogFormatter(use_colors=True)
        formatted = formatter.format(self.record)
        
        # Should contain ANSI color codes for INFO level
        self.assertIn("\033[", formatted)  # ANSI escape sequence
    
    def test_format_without_colors(self):
        """Test message formatting without colors"""
        formatter = EirLogFormatter(use_colors=False)
        formatted = formatter.format(self.record)
        
        # Should not contain ANSI color codes
        self.assertNotIn("\033[", formatted)
    
    def test_different_log_levels(self):
        """Test formatting for different log levels"""
        formatter = EirLogFormatter(use_colors=True)
        
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        for level in levels:
            self.record.levelno = level
            self.record.levelname = logging.getLevelName(level)
            formatted = formatter.format(self.record)
            self.assertIn(logging.getLevelName(level), formatted)


class TestPerformanceLogFilter(unittest.TestCase):
    """Test cases for PerformanceLogFilter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.filter = PerformanceLogFilter()
        self.record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
    
    def test_filter_performance_records(self):
        """Test filtering of performance-related records"""
        # Regular record should pass
        self.assertTrue(self.filter.filter(self.record))
        
        # Performance record should be filtered based on settings
        self.record.msg = "Performance: Function took 0.5s"
        result = self.filter.filter(self.record)
        self.assertIsInstance(result, bool)
    
    def test_filter_timing_records(self):
        """Test filtering of timing records"""
        self.record.msg = "Timing: operation completed in 1.2s"
        result = self.filter.filter(self.record)
        self.assertIsInstance(result, bool)


class TestLoggingContext(unittest.TestCase):
    """Test cases for LoggingContext context manager"""
    
    def test_logging_context_basic(self):
        """Test basic LoggingContext functionality"""
        with LoggingContext("test_operation") as ctx:
            self.assertEqual(ctx.operation, "test_operation")
            self.assertIsNotNone(ctx.start_time)
    
    def test_logging_context_with_logger(self):
        """Test LoggingContext with custom logger"""
        logger = get_logger("test_context")
        
        with patch.object(logger, 'info') as mock_info:
            with LoggingContext("test_op", logger=logger):
                pass
            
            # Should have logged start and end messages
            self.assertTrue(mock_info.called)
            self.assertGreaterEqual(mock_info.call_count, 1)


class TestLoggingFunctions(unittest.TestCase):
    """Test cases for logging utility functions"""
    
    def test_setup_logging(self):
        """Test logging setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = setup_logging(log_file=log_file, log_level="DEBUG")
            
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logger.level, logging.DEBUG)
    
    def test_get_logger(self):
        """Test logger creation"""
        logger = get_logger("test_module")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "eir.test_module")
    
    def test_log_performance(self):
        """Test performance logging function"""
        logger = get_logger("test_perf")
        
        with patch.object(logger, 'info') as mock_info:
            log_performance("test_operation", 1.5, logger)
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn("Performance", call_args)
            self.assertIn("test_operation", call_args)
            self.assertIn("1.5", call_args)
    
    def test_log_error_details(self):
        """Test error details logging function"""
        logger = get_logger("test_error")
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            with patch.object(logger, 'error') as mock_error:
                log_error_with_context(logger, e, {"context": "test"})
                
                mock_error.assert_called_once()
                call_args = mock_error.call_args[0][0]
                self.assertIn("Error occurred", call_args)
                self.assertIn("ValueError", call_args)
    
    def test_log_function_call(self):
        """Test function call logging decorator"""
        logger = get_logger("test_func")
        
        @log_function_call(logger)
        def test_function(x, y):
            return x + y
        
        with patch.object(logger, 'debug') as mock_debug:
            result = test_function(1, 2)
            
            self.assertEqual(result, 3)
            # Should log function entry and exit
            self.assertGreaterEqual(mock_debug.call_count, 1)
    
    def test_log_user_action(self):
        """Test user action logging function"""
        logger = get_logger("test_action")
        
        with patch.object(logger, 'info') as mock_info:
            log_user_action("test_action", {"item": "value"}, logger)
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn("User action", call_args)
            self.assertIn("test_action", call_args)


class TestLoggerIntegration(unittest.TestCase):
    """Integration tests for logging functionality"""
    
    def test_complete_logging_workflow(self):
        """Test complete logging workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration_test.log"
            
            # Setup logging
            logger = setup_logging(log_file=log_file, log_level="DEBUG")
            
            # Test various logging operations
            test_logger = get_logger("integration_test")
            test_logger.info("Test message")
            test_logger.warning("Test warning")
            test_logger.error("Test error")
            
            # Use context manager
            with LoggingContext("test_operation", logger=test_logger):
                test_logger.debug("Inside context")
            
            # Log performance
            log_performance("test_op", 0.5, {"records": 10})
            
            # Verify log file was created and contains expected content
            self.assertTrue(log_file.exists())
            
            with open(log_file, 'r') as f:
                log_content = f.read()
                self.assertIn("Test message", log_content)
                self.assertIn("Test warning", log_content)
                self.assertIn("Test error", log_content)
                self.assertIn("test_operation", log_content)
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy functionality"""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")
        
        # Child logger should inherit from parent
        self.assertTrue(child_logger.name.startswith(parent_logger.name))
    
    def test_log_level_filtering(self):
        """Test log level filtering"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "level_test.log"
            
            # Setup with WARNING level
            setup_logging(log_file=log_file, log_level="WARNING")
            logger = get_logger("level_test")
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Read log file
            with open(log_file, 'r') as f:
                log_content = f.read()
                
                # Only WARNING and above should be logged
                self.assertNotIn("Debug message", log_content)
                self.assertNotIn("Info message", log_content)
                self.assertIn("Warning message", log_content)
                self.assertIn("Error message", log_content)


if __name__ == '__main__':
    unittest.main()