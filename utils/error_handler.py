#!/usr/bin/env python3
"""
Error handling utilities for the catalog parser.
Provides consistent error handling throughout the application.
"""

import sys
import logging
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ParserError(Exception):
    """
    Base exception class for parser errors.
    Provides additional context for debugging.
    """
    
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.data = data
        
    def __str__(self):
        if self.data:
            return f"{self.message} - Context: {str(self.data)}"
        return self.message

class FileError(ParserError):
    """Exception for file-related errors."""
    pass

class HeaderError(ParserError):
    """Exception for header detection errors."""
    pass

class MappingError(ParserError):
    """Exception for field mapping errors."""
    pass

class TransformationError(ParserError):
    """Exception for data transformation errors."""
    pass

def log_error(message: str, data: Optional[Any] = None, exc_info: bool = False) -> None:
    """
    Log an error with consistent formatting.
    
    Args:
        message: Error message
        data: Associated data for context (optional)
        exc_info: Whether to include exception information (optional)
    """
    if data:
        logger.error(f"{message} - Context: {str(data)}", exc_info=exc_info)
    else:
        logger.error(message, exc_info=exc_info)

def handle_exception(e: Exception, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle exceptions in a standardized way.
    
    Args:
        e: The exception
        context: Optional context information
        
    Returns:
        Dictionary with error details
    """
    error_type = type(e).__name__
    error_message = str(e)
    error_trace = traceback.format_exc()
    
    log_error(
        f"Error: {error_type}: {error_message}", 
        data=context, 
        exc_info=True
    )
    
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": error_message,
            "trace": error_trace,
            "context": context
        }
    }

def init_logging(log_file: str = None, console: bool = True, level: int = logging.INFO) -> None:
    """
    Initialize logging for the application.
    
    Args:
        log_file: Path to log file (optional)
        console: Whether to log to console (optional)
        level: Logging level (optional)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    # Log startup message
    logger.info("Logging initialized")