#!/usr/bin/env python3
"""
Base parser class that defines the interface and common functionality
for all file format-specific parsers.
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Iterator

from config.target_fields import TARGET_FIELDS, DEFAULT_VALUES
from utils.column_mapper import ColumnMapper
from utils.error_handler import log_error, ParserError

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """
    Abstract base class for all file parsers. Provides common functionality and 
    defines the interface that all parsers must implement.
    """
    
    def __init__(self, filename: str):
        """
        Initialize the parser with a filename.
        
        Args:
            filename: Path to the file to parse
        """
        self.filename = filename
        self.basename = os.path.basename(filename)
        self.column_mapper = ColumnMapper()
        self.data = []
        self.headers = []
        self.field_mapping = {}
        
        logger.info(f"Initializing parser for file: {self.basename}")
    
    @abstractmethod
    def read_file(self) -> None:
        """
        Read the file and extract raw data.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def detect_headers(self) -> List[str]:
        """
        Detect and extract headers from the file.
        Must be implemented by subclasses.
        
        Returns:
            List of header strings
        """
        pass
    
    def map_fields(self) -> Dict[str, str]:
        """
        Map source headers to target fields using the column mapper.
        
        Returns:
            Dictionary mapping target fields to source headers
        """
        logger.info("Mapping source headers to target fields")
        
        if not self.headers:
            logger.warning("No headers found. Attempting to detect headers.")
            self.headers = self.detect_headers()
            
        if not self.headers:
            raise ParserError("Could not detect headers in the file")
            
        # Use the column mapper to match headers to target fields
        self.field_mapping = self.column_mapper.map_columns(self.headers)
        
        # Log the mapping results
        logger.info(f"Field mapping results: {self.field_mapping}")
        unmapped_targets = [f for f in TARGET_FIELDS if f not in self.field_mapping]
        if unmapped_targets:
            logger.warning(f"Unmapped target fields: {unmapped_targets}")
            
        return self.field_mapping
    
    def transform_data(self) -> List[Dict[str, Any]]:
        """
        Transform raw data to the target schema using the field mapping.
        
        Returns:
            List of dictionaries with standardized field names
        """
        logger.info("Transforming data to target schema")
        
        if not self.field_mapping:
            self.map_fields()
            
        if not self.data:
            logger.warning("No data to transform")
            return []
            
        transformed_data = []
        
        for row in self._iterate_data_rows():
            try:
                transformed_row = self._transform_row(row)
                transformed_data.append(transformed_row)
            except Exception as e:
                log_error(f"Error transforming row: {e}", row)
                
        logger.info(f"Transformed {len(transformed_data)} rows")
        return transformed_data
    
    def _transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single row according to the field mapping.
        
        Args:
            row: Dictionary representing a single data row
            
        Returns:
            Transformed row with standardized field names
        """
        transformed = {}
        
        # Initialize with default values
        for field, default in DEFAULT_VALUES.items():
            transformed[field] = default
            
        # Apply field mapping
        for target_field, source_field in self.field_mapping.items():
            if source_field in row:
                transformed[target_field] = self._clean_value(row[source_field], target_field)
            
        # Handle special fields and validations
        self._handle_special_fields(transformed)
        
        return transformed
    
    def _handle_special_fields(self, row: Dict[str, Any]) -> None:
        """
        Handle special field transformations and validations.
        
        Args:
            row: Dictionary representing a transformed row
        """
        # Handle discontinued field
        if "Discontinued" in row:
            row["Discontinued"] = self._parse_discontinued(row["Discontinued"])
            
        # Additional special field handling can be added here
    
    def _parse_discontinued(self, value: Any) -> bool:
        """
        Parse the discontinued field value to a boolean.
        
        Args:
            value: Input value for the discontinued field
            
        Returns:
            Boolean indicating if the product is discontinued
        """
        if isinstance(value, bool):
            return value
            
        if isinstance(value, (int, float)):
            return value > 0
            
        if isinstance(value, str):
            value = value.strip().lower()
            return value in ('yes', 'y', 'true', 't', '1', 'discontinued', 'obsolete')
            
        return False
    
    def _clean_value(self, value: Any, field: str) -> Any:
        """
        Clean and normalize a field value.
        
        Args:
            value: The value to clean
            field: The target field name
            
        Returns:
            Cleaned value
        """
        if value is None:
            return None
            
        # Convert to string for text fields
        if isinstance(value, (int, float)) and field in [
            "SKU", "Short Description", "Long Description", "Model",
            "Category Group", "Category", "Manufacturer", "Manufacturer SKU",
            "Image URL", "Document Name", "Document URL", "Unit Of Measure"
        ]:
            return str(value)
            
        # Handle price fields separately
        if field in ["Buy Cost", "Trade Price", "MSRP GBP", "MSRP USD", "MSRP EUR"]:
            if isinstance(value, str):
                # Remove currency symbols and non-numeric characters
                value = re.sub(r'[^\d.,]', '', value)
                # Try to convert to float
                try:
                    if ',' in value and '.' in value:
                        # Handle both comma and dot
                        if value.index(',') > value.index('.'):
                            # Format like 1,234.56
                            value = value.replace(',', '')
                        else:
                            # Format like 1.234,56
                            value = value.replace('.', '').replace(',', '.')
                    elif ',' in value:
                        # Might be using comma as decimal separator
                        value = value.replace(',', '.')
                    
                    return float(value)
                except ValueError:
                    return None
                    
        # Strip whitespace from string values
        if isinstance(value, str):
            return value.strip()
            
        return value
    
    @abstractmethod
    def _iterate_data_rows(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate through data rows, converting each to a dictionary.
        Must be implemented by subclasses.
        
        Yields:
            Dictionary for each data row
        """
        pass
        
    def parse(self) -> List[Dict[str, Any]]:
        """
        Main parsing method that orchestrates the parsing process.
        
        Returns:
            List of dictionaries with parsed data in the target schema
        """
        logger.info(f"Starting parsing of file: {self.basename}")
        
        try:
            # Step 1: Read the file
            self.read_file()
            
            # Step 2: Detect headers
            self.headers = self.detect_headers()
            
            # Step 3: Map fields
            self.field_mapping = self.map_fields()
            
            # Step 4: Transform data
            result = self.transform_data()
            
            logger.info(f"Successfully parsed {len(result)} rows from {self.basename}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing file {self.basename}: {str(e)}")
            raise ParserError(f"Error parsing file: {str(e)}")