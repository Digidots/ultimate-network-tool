"""
Logging module for Ultimate Network Tool
Provides timestamped logging with comprehensive error handling
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class UNTLogger:
    """Unified logging system for all UNT operations"""

    def __init__(self, log_dir=None):
        """Initialize logger with timestamped log file"""
        if log_dir is None:
            log_dir = Path(__file__).parent / "logs"
        else:
            log_dir = Path(log_dir)

        # Create logs directory if it doesn't exist
        log_dir.mkdir(exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"unt_{timestamp}.log"

        # Configure logging
        self.logger = logging.getLogger("UNT")
        self.logger.setLevel(logging.DEBUG)

        # File handler with detailed format
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler with simpler format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.log_file = log_file
        self.info(f"Logging initialized: {log_file}")

    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        """Log error message with optional exception info"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message, exc_info=False):
        """Log critical message with optional exception info"""
        self.logger.critical(message, exc_info=exc_info)

    def log_action(self, action, details=""):
        """Log user action"""
        self.info(f"ACTION: {action} | {details}")

    def log_network_event(self, event_type, details):
        """Log network event (capture, probe, etc.)"""
        self.info(f"NETWORK: {event_type} | {details}")

    def log_result(self, operation, result, confidence=""):
        """Log operation result"""
        conf_str = f" | Confidence: {confidence}" if confidence else ""
        self.info(f"RESULT: {operation} | {result}{conf_str}")

    def log_exception(self, context, exception):
        """Log exception with full context"""
        self.error(f"EXCEPTION in {context}: {str(exception)}", exc_info=True)


# Global logger instance
_logger_instance = None


def get_logger():
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = UNTLogger()
    return _logger_instance
