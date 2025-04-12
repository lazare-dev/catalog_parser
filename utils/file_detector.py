#!/usr/bin/env python3
"""
File detection utilities for automatically determining file formats
and appropriate parsers.
"""

import os
import logging
import magic
from typing import List, Dict, Any, Tuple, Optional

from config.settings import SUPPORTED_EXTENSIONS
from utils.error_handler import FileError

logger = logging.getLogger(__name__)

class FileDetector:
    """
    Utility class for detecting file types and selecting appropriate parsers.
    """
    
    @staticmethod
    def detect_file_type(filename: str) -> str:
        """
        Detect file type based on extension and content.
        
        Args:
            filename: Path to the file
            
        Returns:
            Detected file type ('excel', 'csv', 'text', 'numbers', 'pdf')
            
        Raises:
            FileError: If file doesn't exist or type is unsupported
        """
        logger.info(f"Detecting file type for: {filename}")
        
        # Check if file exists
        if not os.path.isfile(filename):
            raise FileError(f"File does not exist: {filename}")
            
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Match extension to supported types
        for file_type, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                logger.info(f"Detected file type by extension: {file_type}")
                
                # Additional validation for specific types
                if file_type == 'csv':
                    # Verify it's actually a text file
                    mime = magic.from_file(filename, mime=True)
                    if not mime.startswith('text/'):
                        # Try to detect the real type
                        real_type = FileDetector._detect_by_content(filename)
                        if real_type:
                            logger.warning(
                                f"File with .csv extension appears to be {real_type}"
                            )
                            return real_type
                            
                # Excel validation
                if file_type == 'excel':
                    # Verify it's actually an Excel file
                    mime = magic.from_file(filename, mime=True)
                    if not any(m in mime for m in ['excel', 'spreadsheet', 'officedocument']):
                        logger.warning(f"File with Excel extension has MIME type: {mime}")
                        # Try content-based detection as fallback
                        real_type = FileDetector._detect_by_content(filename)
                        if real_type:
                            return real_type
                
                return file_type
        
        # If extension not recognized, try content-based detection
        detected_type = FileDetector._detect_by_content(filename)
        if detected_type:
            logger.info(f"Detected file type by content: {detected_type}")
            return detected_type
            
        # If all else fails
        raise FileError(f"Unsupported file type: {ext}")
    
    @staticmethod
    def _detect_by_content(filename: str) -> Optional[str]:
        """
        Detect file type based on content.
        
        Args:
            filename: Path to the file
            
        Returns:
            Detected file type or None if undetectable
        """
        try:
            # Use python-magic to detect MIME type
            mime = magic.from_file(filename, mime=True)
            logger.debug(f"MIME type detected: {mime}")
            
            # Map MIME types to our file types
            if any(m in mime for m in ['excel', 'spreadsheet', 'officedocument.sheet']):
                return 'excel'
                
            if mime == 'application/pdf':
                return 'pdf'
                
            if mime.startswith('text/') or 'charset' in mime:
                # Check if it's a CSV by examining content
                with open(filename, 'rb') as f:
                    sample = f.read(4096).decode('utf-8', errors='ignore')
                    
                # Check for CSV indicators (commas with consistent pattern)
                comma_count = sample.count(',')
                line_count = sample.count('\n')
                
                if line_count > 0:
                    avg_commas_per_line = comma_count / line_count
                    if avg_commas_per_line >= 2:  # Assume CSV if average >= 2 commas per line
                        return 'csv'
                        
                # Otherwise assume plain text
                return 'text'
                
            if 'zip' in mime and filename.endswith('.numbers'):
                return 'numbers'
                
            # Unknown type
            return None
                
        except Exception as e:
            logger.warning(f"Error during content-based detection: {str(e)}")
            return None
    
    @staticmethod
    def get_appropriate_parser(filename: str):
        """
        Get the appropriate parser class for a file.
        
        Args:
            filename: Path to the file
            
        Returns:
            Parser class (not instantiated)
            
        Raises:
            FileError: If appropriate parser not found
        """
        file_type = FileDetector.detect_file_type(filename)
        
        # Import lazily to avoid circular imports
        if file_type == 'excel':
            from parsers.excel_parser import ExcelParser
            return ExcelParser
            
        elif file_type == 'csv':
            from parsers.csv_parser import CSVParser
            return CSVParser
            
        elif file_type == 'text':
            from parsers.text_parser import TextParser
            return TextParser
            
        elif file_type == 'numbers':
            from parsers.numbers_parser import NumbersParser
            return NumbersParser
            
        elif file_type == 'pdf':
            from parsers.pdf_parser import PDFParser
            return PDFParser
            
        raise FileError(f"No parser available for file type: {file_type}")