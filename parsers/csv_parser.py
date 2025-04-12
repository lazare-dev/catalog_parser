#!/usr/bin/env python3
"""
CSV parser for processing catalog data in CSV format.
"""

import os
import csv
import logging
import chardet
from typing import List, Dict, Any, Tuple, Optional, Iterator
from io import StringIO

from parsers.base_parser import BaseParser
from utils.error_handler import ParserError, FileError, log_error
from utils.manufacturer_detector import ManufacturerDetector
from utils.price_utils import PriceUtils
from config.settings import FALLBACK_ENCODING, MAX_HEADER_ROWS

logger = logging.getLogger(__name__)

class CSVParser(BaseParser):
    """
    Parser for CSV files. Handles various CSV formats with different
    delimiters and encodings.
    """
    
    def __init__(self, filename: str):
        """
        Initialize the CSV parser.
        
        Args:
            filename: Path to the CSV file
        """
        super().__init__(filename)
        self.encoding = None
        self.delimiter = None
        self.has_headers = True
        self.manufacturer_detector = ManufacturerDetector()
        
    def read_file(self) -> None:
        """
        Read and parse the CSV file, detecting encoding and delimiter.
        """
        logger.info(f"Reading CSV file: {self.basename}")
        
        try:
            # Detect encoding
            self.encoding = self._detect_encoding()
            logger.debug(f"Detected encoding: {self.encoding}")
            
            # Detect delimiter
            self.delimiter = self._detect_delimiter()
            logger.debug(f"Detected delimiter: {self.delimiter}")
            
            # Read the file content
            with open(self.filename, 'r', encoding=self.encoding, errors='replace') as f:
                csv_reader = csv.reader(f, delimiter=self.delimiter)
                self.data = list(csv_reader)
                
            if not self.data:
                raise FileError("CSV file is empty")
                
            logger.info(f"Successfully read {len(self.data)} rows from CSV")
            
        except Exception as e:
            error_msg = f"Error reading CSV file: {str(e)}"
            logger.error(error_msg)
            raise FileError(error_msg)
            
    def detect_headers(self) -> List[str]:
        """
        Detect and extract headers from the CSV file.
        
        Returns:
            List of header strings
        """
        logger.info("Detecting headers in CSV file")
        
        if not self.data:
            logger.warning("No data available to detect headers")
            return []
            
        # Check if file has headers
        self.has_headers = self._check_has_headers()
        
        if not self.has_headers:
            logger.warning("CSV appears to have no headers, using column indices")
            # Create generic headers (Column1, Column2, etc.)
            if self.data:
                return [f"Column{i+1}" for i in range(len(self.data[0]))]
            return []
            
        # Get headers from first row
        headers = self.data[0]
        
        # Clean up headers
        headers = [str(h).strip() if h is not None else f"Column{i+1}" 
                  for i, h in enumerate(headers)]
        
        # Remove empty headers
        for i, header in enumerate(headers):
            if not header:
                headers[i] = f"Column{i+1}"
                
        logger.info(f"Detected {len(headers)} headers: {headers}")
        return headers
        
    def _detect_encoding(self) -> str:
        """
        Detect the encoding of the CSV file.
        
        Returns:
            Detected encoding
        """
        try:
            # Read a sample of the file
            with open(self.filename, 'rb') as f:
                sample = f.read(4096)
                
            # Use chardet to detect encoding
            result = chardet.detect(sample)
            encoding = result['encoding']
            
            # If no encoding detected or confidence is low, use fallback
            if not encoding or result['confidence'] < 0.7:
                logger.warning(
                    f"Low confidence encoding detection: {result}, "
                    f"using fallback: {FALLBACK_ENCODING}"
                )
                return FALLBACK_ENCODING
                
            return encoding
            
        except Exception as e:
            logger.warning(f"Error detecting encoding: {str(e)}, using fallback")
            return FALLBACK_ENCODING
            
    def _detect_delimiter(self) -> str:
        """
        Detect the delimiter used in the CSV file.
        
        Returns:
            Detected delimiter
        """
        try:
            # Common delimiters to check
            delimiters = [',', ';', '\t', '|']
            
            # Read a sample of the file
            with open(self.filename, 'r', encoding=self.encoding, errors='replace') as f:
                sample = f.read(4096)
                
            # Count occurrences of each delimiter
            counts = {d: sample.count(d) for d in delimiters}
            
            # Get the delimiter with the most occurrences
            max_count = 0
            detected_delimiter = ','  # Default to comma
            
            for d, count in counts.items():
                if count > max_count:
                    max_count = count
                    detected_delimiter = d
                    
            # Additional check: if tab is present, prefer it over comma if close
            if '\t' in counts and counts['\t'] > 0:
                if counts[','] / counts['\t'] < 2:  # If comma is less than 2x tab count
                    detected_delimiter = '\t'
                    
            return detected_delimiter
            
        except Exception as e:
            logger.warning(f"Error detecting delimiter: {str(e)}, using comma")
            return ','
            
    def _check_has_headers(self) -> bool:
        """
        Check if the CSV file has headers.
        
        Returns:
            True if headers are detected, False otherwise
        """
        if not self.data or len(self.data) < 2:
            # Not enough data to tell
            return True
            
        # Get first and second rows
        first_row = self.data[0]
        second_row = self.data[1]
        
        # Count numeric values in each row
        first_row_numeric = sum(1 for cell in first_row if self._is_numeric(cell))
        second_row_numeric = sum(1 for cell in second_row if self._is_numeric(cell))
        
        # If second row has significantly more numeric values, first row is likely headers
        if second_row_numeric > first_row_numeric + 2:
            return True
            
        # Check if first row contains typical header keywords
        header_keywords = ['id', 'name', 'price', 'cost', 'sku', 'description', 'category', 'brand', 
                          'product', 'model', 'manufacturer', 'image', 'url']
        
        first_row_text = ' '.join(str(cell).lower() for cell in first_row if cell)
        keyword_matches = sum(1 for keyword in header_keywords if keyword in first_row_text)
        
        # If multiple header keywords found, first row is likely headers
        if keyword_matches >= 2:
            return True
            
        # Default to assuming there are headers
        return True
        
    def _is_numeric(self, value: Any) -> bool:
        """
        Check if a value is numeric.
        
        Args:
            value: Value to check
            
        Returns:
            True if numeric, False otherwise
        """
        if value is None:
            return False
            
        # Try to convert to float
        try:
            float(str(value).strip().replace(',', '.'))
            return True
        except (ValueError, TypeError):
            return False
            
    def _iterate_data_rows(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate through data rows, converting each to a dictionary.
        
        Yields:
            Dictionary for each data row
        """
        if not self.data:
            return
            
        # Skip header row if present
        start_row = 1 if self.has_headers else 0
        
        # Get headers
        if self.has_headers:
            headers = self.headers
        else:
            # Use column indices as headers
            headers = [f"Column{i+1}" for i in range(len(self.data[0]))]
            
        # Process each data row
        for row_index in range(start_row, len(self.data)):
            row = self.data[row_index]
            
            # Skip empty rows
            if not row or all(not cell for cell in row):
                continue
                
            # Create dictionary for row
            row_dict = {}
            
            # Map cells to headers
            for i, cell in enumerate(row):
                if i < len(headers):
                    header = headers[i]
                    row_dict[header] = cell
                else:
                    # Extra cells beyond header count
                    row_dict[f"ExtraColumn{i+1}"] = cell
                    
            yield row_dict
            
    def transform_data(self) -> List[Dict[str, Any]]:
        """
        Transform raw data to the target schema, with special handling for CSV files.
        
        Returns:
            List of dictionaries with standardized field names
        """
        transformed_data = super().transform_data()
        
        if not transformed_data:
            return []
            
        # Attempt to extract manufacturer from filename if not already set
        has_manufacturer = any(row.get('Manufacturer') for row in transformed_data)
        
        if not has_manufacturer:
            # Try to detect manufacturer from filename
            manufacturer = self.manufacturer_detector.detect_from_filename(self.filename)
            
            if manufacturer:
                logger.info(f"Setting manufacturer to '{manufacturer}' from filename")
                for row in transformed_data:
                    row['Manufacturer'] = manufacturer
                    
        # Process row-based price information
        self._process_row_based_prices(transformed_data)
        
        # Validate and normalize price fields
        for row in transformed_data:
            row = PriceUtils.validate_price_fields(row)
            
        return transformed_data
        
    def _process_row_based_prices(self, data: List[Dict[str, Any]]) -> None:
        """
        Process row-based price information that might be in description fields.
        
        Args:
            data: List of data dictionaries to process
        """
        # Check for price information in description fields
        for row in data:
            for field in ['Long Description', 'Short Description']:
                if field in row and row[field]:
                    # Try to extract prices from description
                    prices = PriceUtils.extract_prices_from_description(row[field])
                    
                    # Apply extracted prices if found
                    for price_field, price_value in prices.items():
                        # Only set if not already present
                        if price_field not in row or row[price_field] is None:
                            row[price_field] = price_value