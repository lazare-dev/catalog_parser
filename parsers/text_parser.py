#!/usr/bin/env python3
"""
Text parser for processing catalog data in plain text formats.
"""

import os
import re
import csv
import logging
import chardet
from typing import List, Dict, Any, Tuple, Optional, Iterator
from io import StringIO

from parsers.base_parser import BaseParser
from utils.error_handler import ParserError, FileError, log_error
from utils.manufacturer_detector import ManufacturerDetector
from utils.price_utils import PriceUtils
from config.settings import FALLBACK_ENCODING

logger = logging.getLogger(__name__)

class TextParser(BaseParser):
    """
    Parser for plain text files. Attempts to infer structure from content.
    """
    
    def __init__(self, filename: str):
        """
        Initialize the text parser.
        
        Args:
            filename: Path to the text file
        """
        super().__init__(filename)
        self.encoding = None
        self.format_type = None  # 'tabular', 'delimited', 'key-value', or 'unstructured'
        self.delimiter = None
        self.separator = None  # For key-value pairs
        self.manufacturer_detector = ManufacturerDetector()
        
    def read_file(self) -> None:
        """
        Read and parse the text file, detecting format.
        """
        logger.info(f"Reading text file: {self.basename}")
        
        try:
            # Detect encoding
            self.encoding = self._detect_encoding()
            logger.debug(f"Detected encoding: {self.encoding}")
            
            # Read file content
            with open(self.filename, 'r', encoding=self.encoding, errors='replace') as f:
                content = f.read()
                
            if not content.strip():
                raise FileError("Text file is empty")
                
            # Detect format type
            self.format_type = self._detect_format_type(content)
            logger.info(f"Detected format type: {self.format_type}")
            
            # Parse content based on format type
            if self.format_type == 'delimited':
                self._parse_delimited(content)
            elif self.format_type == 'tabular':
                self._parse_tabular(content)
            elif self.format_type == 'key-value':
                self._parse_key_value(content)
            else:  # unstructured
                self._parse_unstructured(content)
                
            logger.info(f"Successfully parsed text file into {len(self.data)} rows")
            
        except Exception as e:
            error_msg = f"Error reading text file: {str(e)}"
            logger.error(error_msg)
            raise FileError(error_msg)
            
    def _detect_encoding(self) -> str:
        """
        Detect the encoding of the text file.
        
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
            
    def _detect_format_type(self, content: str) -> str:
        """
        Detect the format type of the text content.
        
        Args:
            content: Text file content
            
        Returns:
            Format type: 'tabular', 'delimited', 'key-value', or 'unstructured'
        """
        # Take a sample of lines
        lines = content.splitlines()[:50]
        
        if not lines:
            return 'unstructured'
            
        # Count lines with common delimiters
        delimiter_counts = {
            ',': sum(1 for line in lines if ',' in line),
            ';': sum(1 for line in lines if ';' in line),
            '\t': sum(1 for line in lines if '\t' in line),
            '|': sum(1 for line in lines if '|' in line)
        }
        
        # Check for fixed-width tabular format (consistent line lengths)
        line_lengths = [len(line) for line in lines if line.strip()]
        length_variance = max(line_lengths) - min(line_lengths) if line_lengths else 0
        
        # Check for key-value pairs (lines with : or =)
        kv_pattern = re.compile(r'^\s*[\w\s]+[:|=]')
        kv_count = sum(1 for line in lines if kv_pattern.search(line))
        
        # Determine format type based on indicators
        max_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])
        
        if max_delimiter[1] >= len(lines) * 0.7:
            # Consistent delimiter in most lines
            self.delimiter = max_delimiter[0]
            return 'delimited'
        elif length_variance < 5 and all(len(line) > 20 for line in lines if line.strip()):
            # Consistent line lengths suggest fixed-width format
            return 'tabular'
        elif kv_count >= len(lines) * 0.7:
            # Mostly key-value pairs
            if sum(1 for line in lines if ':' in line) > sum(1 for line in lines if '=' in line):
                self.separator = ':'
            else:
                self.separator = '='
            return 'key-value'
        else:
            # Default to unstructured
            return 'unstructured'
            
    def _parse_delimited(self, content: str) -> None:
        """
        Parse delimited text content.
        
        Args:
            content: Text file content
        """
        # Create CSV reader with detected delimiter
        reader = csv.reader(
            StringIO(content), 
            delimiter=self.delimiter,
            quotechar='"'
        )
        
        # Read all rows
        self.data = list(reader)
        
        if not self.data:
            raise FileError("No data could be parsed from delimited text")
            
    def _parse_tabular(self, content: str) -> None:
        """
        Parse fixed-width tabular text content.
        
        Args:
            content: Text file content
        """
        lines = content.splitlines()
        
        # Find column boundaries by analyzing spaces in the first few lines
        sample_lines = [line for line in lines[:10] if line.strip()]
        
        if not sample_lines:
            raise FileError("No data found in tabular text")
            
        # Detect column boundaries based on consistent spacing
        col_boundaries = self._detect_column_boundaries(sample_lines)
        
        # Parse data using detected boundaries
        self.data = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Extract values at column boundaries
            row = []
            for i in range(len(col_boundaries)):
                start = col_boundaries[i]
                end = col_boundaries[i + 1] if i < len(col_boundaries) - 1 else len(line)
                
                if start < len(line):
                    value = line[start:end].strip()
                    row.append(value)
                else:
                    row.append("")
                    
            self.data.append(row)
            
    def _detect_column_boundaries(self, sample_lines: List[str]) -> List[int]:
        """
        Detect column boundaries in fixed-width tabular data.
        
        Args:
            sample_lines: Sample lines from the beginning of the file
            
        Returns:
            List of column boundary positions
        """
        # Find positions with consistent spaces in all sample lines
        line_length = min(len(line) for line in sample_lines)
        space_counts = [0] * line_length
        
        for line in sample_lines:
            for i in range(min(line_length, len(line))):
                if line[i].isspace():
                    space_counts[i] += 1
                    
        # Identify potential column boundaries (positions with spaces in all lines)
        boundaries = [0]  # Always start at position 0
        
        for i in range(1, line_length - 1):
            if (space_counts[i] == len(sample_lines) and 
                space_counts[i - 1] == len(sample_lines) and
                space_counts[i + 1] < len(sample_lines)):
                # Found end of a space sequence followed by non-space
                boundaries.append(i + 1)
                
        return boundaries
        
    def _parse_key_value(self, content: str) -> None:
        """
        Parse key-value pairs text content.
        
        Args:
            content: Text file content
        """
        lines = content.splitlines()
        
        # Extract key-value pairs
        pairs = []
        current_record = {}
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line might separate records
                if current_record:
                    pairs.append(current_record)
                    current_record = {}
                continue
                
            # Try to split on separator
            if self.separator in line:
                key, value = line.split(self.separator, 1)
                key = key.strip()
                value = value.strip()
                
                if key:
                    current_record[key] = value
                    
        # Add the last record if not empty
        if current_record:
            pairs.append(current_record)
            
        # Convert pairs to rows with uniform structure
        if pairs:
            # Get all unique keys
            all_keys = set()
            for record in pairs:
                all_keys.update(record.keys())
                
            # Convert to list of lists
            headers = sorted(list(all_keys))
            
            rows = []
            rows.append(headers)  # First row is headers
            
            for record in pairs:
                row = [record.get(key, "") for key in headers]
                rows.append(row)
                
            self.data = rows
        else:
            raise FileError("No key-value pairs found in text")
            
    def _parse_unstructured(self, content: str) -> None:
        """
        Parse unstructured text content by trying to extract product information.
        
        Args:
            content: Text file content
        """
        lines = content.splitlines()
        
        # Try to find product blocks in the content
        products = self._extract_product_blocks(lines)
        
        if products:
            # Convert products to rows with consistent structure
            all_keys = set()
            for product in products:
                all_keys.update(product.keys())
                
            # Create headers and data
            headers = sorted(list(all_keys))
            
            rows = []
            rows.append(headers)  # First row is headers
            
            for product in products:
                row = [product.get(key, "") for key in headers]
                rows.append(row)
                
            self.data = rows
        else:
            # Fallback: convert the entire content to a single record
            logger.warning("No structured product data found, treating as a single record")
            
            # Try to extract product attributes from the whole content
            product = self._extract_product_attributes(content)
            
            if product:
                headers = sorted(list(product.keys()))
                rows = [headers, [product.get(key, "") for key in headers]]
                self.data = rows
            else:
                # Last resort: just use the content as a description
                self.data = [
                    ["Description"],
                    [content.strip()]
                ]
    
    def _extract_product_blocks(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Extract product blocks from text lines.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of product dictionaries
        """
        products = []
        current_product = {}
        current_key = None
        
        # Common product identifiers to look for
        product_start_patterns = [
            r'^\s*product\s*:\s*',
            r'^\s*item\s*:\s*',
            r'^\s*sku\s*:\s*',
            r'^\s*#\d+\s*',
            r'^\s*\d+\.\s+',
            r'^\s*-{3,}\s*'  # Separator line
        ]
        
        # Attributes to look for
        attribute_patterns = {
            'SKU': r'(?:sku|item\s*(?:code|number|#)|product\s*(?:code|number|#)|part\s*(?:number|#))\s*:\s*(.*)',
            'Short Description': r'(?:name|title|short\s*desc|product\s*name)\s*:\s*(.*)',
            'Long Description': r'(?:description|details|features|specs|specification)\s*:\s*(.*)',
            'Model': r'(?:model|model\s*(?:number|#))\s*:\s*(.*)',
            'Category': r'(?:category|product\s*type|group)\s*:\s*(.*)',
            'Manufacturer': r'(?:manufacturer|brand|maker|vendor)\s*:\s*(.*)',
            'Buy Cost': r'(?:cost|buy\s*(?:cost|price)|wholesale\s*price)\s*:\s*(.*)',
            'MSRP GBP': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*gbp|\s*£|\s*pounds)?\s*:\s*(.*)',
            'MSRP USD': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*usd|\s*\$|\s*dollars)?\s*:\s*(.*)',
            'MSRP EUR': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*eur|\s*€|\s*euros)?\s*:\s*(.*)',
            'Trade Price': r'(?:trade\s*price|dealer\s*price|distributor\s*price)\s*:\s*(.*)'
        }
        
        # Process each line
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                # Empty line might indicate a new product
                if current_product:
                    # Only add if it has at least one key attribute
                    if 'SKU' in current_product or 'Short Description' in current_product:
                        products.append(current_product)
                    current_product = {}
                continue
            
            # Check if line starts a new product
            new_product = False
            for pattern in product_start_patterns:
                if re.match(pattern, line):
                    if current_product:
                        # Only add if it has at least one key attribute
                        if 'SKU' in current_product or 'Short Description' in current_product:
                            products.append(current_product)
                    current_product = {}
                    new_product = True
                    break
            
            # If not a new product, try to extract attributes
            if not new_product:
                for attr, pattern in attribute_patterns.items():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        current_product[attr] = match.group(1).strip()
                        break
        
        # Add the last product if not empty
        if current_product and ('SKU' in current_product or 'Short Description' in current_product):
            products.append(current_product)
        
        return products
    
    def _extract_product_attributes(self, content: str) -> Dict[str, str]:
        """
        Extract product attributes from unstructured text.
        
        Args:
            content: Text content
            
        Returns:
            Dictionary of product attributes
        """
        product = {}
        
        # Attributes to look for with regex patterns
        attribute_patterns = {
            'SKU': r'(?:sku|item\s*(?:code|number|#)|product\s*(?:code|number|#)|part\s*(?:number|#))\s*:\s*([\w\-\d]+)',
            'Short Description': r'(?:name|title|short\s*desc|product\s*name)\s*:\s*([^\n\r]+)',
            'Long Description': r'(?:description|details|features|specs|specification)\s*:\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            'Model': r'(?:model|model\s*(?:number|#))\s*:\s*([\w\-\d]+)',
            'Category': r'(?:category|product\s*type|group)\s*:\s*([^\n\r]+)',
            'Manufacturer': r'(?:manufacturer|brand|maker|vendor)\s*:\s*([^\n\r]+)',
            'Buy Cost': r'(?:cost|buy\s*(?:cost|price)|wholesale\s*price)\s*:\s*([^\n\r]+)',
            'MSRP GBP': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*gbp|\s*£|\s*pounds)?\s*:\s*([^\n\r]+)',
            'MSRP USD': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*usd|\s*\$|\s*dollars)?\s*:\s*([^\n\r]+)',
            'MSRP EUR': r'(?:msrp|rrp|retail\s*price|list\s*price)(?:\s*eur|\s*€|\s*euros)?\s*:\s*([^\n\r]+)',
            'Trade Price': r'(?:trade\s*price|dealer\s*price|distributor\s*price)\s*:\s*([^\n\r]+)'
        }
        
        # Extract attributes
        for attr, pattern in attribute_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                product[attr] = match.group(1).strip()
        
        # If no structured attributes found, try to guess
        if not product:
            # Try to find a SKU-like pattern
            sku_match = re.search(r'\b([A-Z0-9]{5,20})\b', content)
            if sku_match:
                product['SKU'] = sku_match.group(1)
            
            # Use first line as short description if available
            first_line = content.strip().split('\n')[0].strip()
            if first_line and len(first_line) < 200:
                product['Short Description'] = first_line
            
            # Use rest as long description
            if len(content.strip().split('\n')) > 1:
                product['Long Description'] = '\n'.join(content.strip().split('\n')[1:])
        
        return product
    
    def detect_headers(self) -> List[str]:
        """
        Detect and extract headers from the text file.
        
        Returns:
            List of header strings
        """
        logger.info("Detecting headers in text file")
        
        if not self.data:
            logger.warning("No data available to detect headers")
            return []
        
        # Assume first row contains headers
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
    
    def _iterate_data_rows(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate through data rows, converting each to a dictionary.
        
        Yields:
            Dictionary for each data row
        """
        if not self.data or len(self.data) < 2:  # Need at least headers and one data row
            return
        
        # Get headers
        headers = self.headers
        
        # Process each data row (skip header row)
        for row_index in range(1, len(self.data)):
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
        Transform raw data to the target schema, with special handling for text files.
        
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
                    prices = PriceUtils.extract_prices_from_description(str(row[field]))
                    
                    # Apply extracted prices if found
                    for price_field, price_value in prices.items():
                        # Only set if not already present
                        if price_field not in row or row[price_field] is None:
                            row[price_field] = price_value