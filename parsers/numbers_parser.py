#!/usr/bin/env python3
"""
Numbers parser for processing catalog data in Apple Numbers format.
"""

import os
import logging
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import shutil
import json
import re
import plistlib
from typing import List, Dict, Any, Tuple, Optional, Iterator
from pathlib import Path

from parsers.base_parser import BaseParser
from utils.error_handler import ParserError, FileError, log_error
from utils.manufacturer_detector import ManufacturerDetector
from utils.price_utils import PriceUtils
from config.settings import MAX_HEADER_ROWS

logger = logging.getLogger(__name__)

class NumbersParser(BaseParser):
    """
    Parser for Apple Numbers spreadsheet files (.numbers format).
    Extracts data by parsing the internal XML structure.
    """
    
    def __init__(self, filename: str, sheet_index: int = 0, table_index: int = 0, 
                 sheet_name: Optional[str] = None, table_name: Optional[str] = None):
        """
        Initialize the Numbers parser.
        
        Args:
            filename: Path to the Numbers file
            sheet_index: Index of the sheet to parse (default: 0)
            table_index: Index of the table to parse (default: 0)
            sheet_name: Name of the sheet to parse (overrides sheet_index if provided)
            table_name: Name of the table to parse (overrides table_index if provided)
        """
        super().__init__(filename)
        self.sheet_index = sheet_index
        self.table_index = table_index
        self.sheet_name = sheet_name
        self.table_name = table_name
        self.sheet_names = []
        self.table_names = []
        self.header_row_index = 0
        self.manufacturer_detector = ManufacturerDetector()
        self.temp_dir = None
    
    def read_file(self) -> None:
        """
        Read and parse the Numbers file by extracting the zip archive and parsing XML.
        """
        logger.info(f"Reading Numbers file: {self.basename}")
        
        if not os.path.exists(self.filename):
            raise FileError(f"File does not exist: {self.basename}")
            
        if not zipfile.is_zipfile(self.filename):
            raise FileError(f"File is not a valid Numbers file (not a zip archive): {self.basename}")
            
        try:
            # Create a temporary directory for extraction
            self.temp_dir = tempfile.mkdtemp()
            
            try:
                # Extract the Numbers file (which is a zip archive)
                with zipfile.ZipFile(self.filename, 'r') as zip_ref:
                    # Log contents for debugging
                    file_list = zip_ref.namelist()
                    logger.debug(f"Files in Numbers archive: {file_list[:20]}...")
                    zip_ref.extractall(self.temp_dir)
                    
                # Parse the extracted files
                self._parse_numbers_format()
                
                if not self.data:
                    raise FileError("Could not extract usable data from Numbers file")
                    
                logger.info(f"Successfully extracted data from Numbers: {len(self.data)} rows")
                
            except zipfile.BadZipFile as e:
                raise FileError(f"Invalid zip file: {str(e)}")
            finally:
                # Clean up the temporary directory if we're done with it
                if self.temp_dir:
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                    self.temp_dir = None
                
        except Exception as e:
            error_msg = f"Error processing Numbers file: {str(e)}"
            logger.error(error_msg)
            raise FileError(error_msg)
    
    def _parse_numbers_format(self) -> None:
        """
        Parse the Numbers file structure by attempting multiple strategies.
        """
        # Try different approaches in order of preference
        strategies = [
            self._extract_from_iwa_files,
            self._extract_from_index_json,
            self._extract_from_document_xml,
            self._extract_from_tables_xml,  # Moved up in priority
            self._extract_from_quicklook_thumbnail,
            self._extract_from_preview_pdf,
            self._extract_from_preview_xml
        ]
        
        for strategy in strategies:
            try:
                strategy()
                if self.data and any(any(cell for cell in row) for row in self.data):
                    logger.info(f"Successfully extracted data using {strategy.__name__}")
                    return
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {str(e)}")
                # Log more detailed error information for debugging
                logger.debug(f"Error details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # If we get here, all strategies failed
        self._fallback_extraction()
        
        if not self.data:
            raise FileError("Could not extract data from Numbers file using any available method")
    
    def _extract_from_iwa_files(self) -> None:
        """
        Extract data from IWA files in modern Numbers format.
        
        Numbers 5.0+ uses IWA format files that store data in a binary/protobuf-like format.
        This method attempts to extract text data from these files.
        """
        logger.debug("Attempting to extract from IWA files")
        
        # First, look for IWA files in the Index directory, which is where the table data is typically stored
        index_dir = os.path.join(self.temp_dir, 'Index')
        if not os.path.exists(index_dir) or not os.path.isdir(index_dir):
            logger.debug("Index directory not found")
            return
            
        # Look specifically in the Tables subdirectory if it exists
        tables_dir = os.path.join(index_dir, 'Tables')
        if os.path.exists(tables_dir) and os.path.isdir(tables_dir):
            logger.debug(f"Found Tables directory: {tables_dir}")
            
        # Collect all IWA files in the archive
        iwa_files = []
        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                if file.endswith('.iwa'):
                    iwa_files.append(os.path.join(root, file))
                    
        if not iwa_files:
            logger.debug("No IWA files found")
            return
            
        logger.debug(f"Found {len(iwa_files)} IWA files")
        
        # We'll first look for DataList and Tile IWA files which are more likely to contain table data
        data_list_files = [f for f in iwa_files if 'DataList' in os.path.basename(f)]
        tile_files = [f for f in iwa_files if 'Tile' in os.path.basename(f)]
        table_files = [f for f in iwa_files if 'Table' in os.path.basename(f)]
        
        # Add files that might contain data based on known patterns
        data_files = [f for f in iwa_files if any(pattern in os.path.basename(f) 
                                                for pattern in ['Data', 'Row', 'Cell', 'Value', 'Content'])]
        
        # Process files in order of likelihood to contain useful data
        priority_files = data_list_files + tile_files + table_files + data_files + [
            f for f in iwa_files 
            if f not in data_list_files and f not in tile_files and f not in table_files and f not in data_files
        ]
        
        # Track all extracted text chunks
        all_text_chunks = []
        
        # Tracking if we found any binary patterns that might indicate table data
        found_table_pattern = False
        
        # Process each IWA file
        for iwa_file in priority_files:
            try:
                file_basename = os.path.basename(iwa_file)
                logger.debug(f"Processing IWA file: {file_basename}")
                
                # Read the binary file
                with open(iwa_file, 'rb') as f:
                    content = f.read()
                    
                # Check for common binary patterns that indicate table data in Numbers format
                # These are approximate markers that might appear in table data
                markers = [
                    b'SNFL',  # Common Numbers table marker
                    b'SNST',  # Another table-related marker
                    b'SMFL',  # Found in some table data
                    b'NMBR',  # Numbers marker
                    b'TEXT',  # Text data marker
                    b'GRID',  # Grid/table marker
                    b'ROWS',  # Rows marker
                    b'COLS',  # Columns marker
                    b'TABLE', # Table marker
                    b'CELL',  # Cell marker
                    b'HEADER', # Header marker
                    b'VALUE'  # Value marker
                ]
                
                has_markers = any(marker in content for marker in markers)
                if has_markers:
                    logger.debug(f"File {file_basename} contains potential table markers")
                    found_table_pattern = True
                
                # Advanced pattern detection for table structures
                # These patterns might indicate table headers or structured data
                structured_patterns = [
                    rb'([\x20-\x7E]+[\x00-\x03][\x20-\x7E]+[\x00-\x03][\x20-\x7E]+)', # Structured data with control chars
                    rb'([A-Za-z0-9 ]{3,}[\x00-\x02][A-Za-z0-9 ]{3,})',  # Words separated by control chars
                    rb'[\x00-\x03]([0-9A-Za-z]{2,})[\x00-\x03]',       # Alphanumeric between control chars
                ]
                
                for pattern in structured_patterns:
                    structured_matches = re.findall(pattern, content)
                    if structured_matches:
                        logger.debug(f"Found structured patterns in {file_basename}: {len(structured_matches)} matches")
                        # Convert bytes to strings where possible
                        for match in structured_matches:
                            try:
                                if isinstance(match, bytes):
                                    text = match.decode('utf-8', errors='ignore')
                                    text = ''.join(c if c.isprintable() or c in ['\n', '\t', '\r'] else ' ' for c in text)
                                    if text and len(text) >= 3:
                                        all_text_chunks.append(text)
                            except Exception:
                                continue
                
                # Look for text content - first with UTF-8 and fallback to ASCII
                # We'll search for longer sequences of ASCII text that might represent table data
                text_chunks = []
                
                # Pattern to find strings in binary data - use more aggressive pattern
                # Look for sequences of printable ASCII chars (20-7E) or common separators
                result = re.findall(b'[\x20-\x7E\t\n\r]{4,}', content)
                
                # Convert to strings
                for binary_chunk in result:
                    try:
                        # Try UTF-8 first
                        text = binary_chunk.decode('utf-8', errors='ignore')
                        # Clean up control chars except tabs and newlines
                        text = ''.join(c if c.isprintable() or c in ['\n', '\t', '\r'] else ' ' for c in text)
                        text = text.strip()
                        if text and len(text) >= 3:  # Keep only non-empty chunks
                            text_chunks.append(text)
                    except UnicodeDecodeError:
                        # Fallback to ASCII if UTF-8 fails
                        text = binary_chunk.decode('ascii', errors='ignore')
                        text = text.strip()
                        if text and len(text) >= 3:
                            text_chunks.append(text)
                
                # Look specifically for structured data that might represent tables
                structured_chunks = []
                for chunk in text_chunks:
                    # Look for delimiter patterns that suggest table rows
                    if re.search(r'(\S+[,;|\t]\S+){2,}', chunk):  # Multiple delimiter-separated values
                        structured_chunks.append(chunk)
                        
                    # Look for patterns that might be column headers
                    if re.search(r'(^|\s)(id|sku|name|description|price|cost|model|category|manufacturer)(\s|$)', 
                               chunk.lower()):
                        structured_chunks.append(chunk)
                
                # Process structured chunks first, then regular chunks
                all_text_chunks.extend(structured_chunks)
                all_text_chunks.extend([c for c in text_chunks if c not in structured_chunks])
                
            except Exception as e:
                logger.debug(f"Error processing IWA file {iwa_file}: {str(e)}")
        
        # Now process all the collected text chunks
        if not all_text_chunks:
            logger.debug("No text chunks extracted from IWA files")
            return
            
        logger.debug(f"Total extracted text chunks: {len(all_text_chunks)}")
        
        # First try with structured chunks if available
        structured_chunks = [
            chunk for chunk in all_text_chunks
            if re.search(r'(\S+[,;|\t]\S+){2,}', chunk) or  # delimiter patterns
               re.search(r'(^|\s)(id|sku|name|description|price|cost|model|category|manufacturer)(\s|$)', 
                       chunk.lower())  # header patterns
        ]
        
        if structured_chunks:
            # Step 1: Look for row-like patterns in structured chunks first
            rows = self._find_row_patterns(structured_chunks)
            
            # Step 2: If we found rows with a consistent structure, use them
            if rows and len(rows) >= 2:  # Need at least header + data row
                logger.debug(f"Found {len(rows)} structured table rows")
                
                # Ensure data has content
                if any(any(cell for cell in row) for row in rows):
                    self.data = rows
                    return
        
        # Step 3: Try with all text chunks if structured approach didn't work
        rows = self._find_row_patterns(all_text_chunks)
        
        # Step 4: If we found rows with a consistent structure, use them
        if rows and len(rows) >= 2:  # Need at least header + data row
            logger.debug(f"Found {len(rows)} potential table rows")
            
            # Ensure data has content
            if any(any(cell for cell in row) for row in rows):
                self.data = rows
                return
            
        # Step 5: If we didn't find clear rows, try to group text chunks into potential rows
        # based on common delimiters or patterns
        if not self.data and len(all_text_chunks) > 10:
            # Try different delimiters to see if we can form rows
            for delimiter in ['\t', ',', ';', '|', ' - ', '  ']:  # Added space-based delimiters
                potential_rows = []
                for chunk in all_text_chunks:
                    if delimiter in chunk:
                        cells = [cell.strip() for cell in chunk.split(delimiter)]
                        if len(cells) >= 2:  # Need at least 2 cells to be a row
                            potential_rows.append(cells)
                
                # If we have enough rows with similar structure, we might have found a table
                if len(potential_rows) >= 3:  # Lower threshold to 3 rows
                    # Check for consistent column count
                    col_counts = [len(row) for row in potential_rows]
                    most_common_count = max(set(col_counts), key=col_counts.count)
                    consistent_rows = [row for row in potential_rows if len(row) == most_common_count]
                    
                    if len(consistent_rows) >= 3:  # At least 3 consistent rows
                        logger.debug(f"Found potential table with delimiter '{delimiter}': {len(consistent_rows)} rows")
                        
                        # Ensure data has content
                        if any(any(cell for cell in row) for row in consistent_rows):
                            self.data = consistent_rows
                            return
        
        # Step 6: Last resort - try to group chunks by patterns or proximity
        if not self.data and found_table_pattern:
            table_data = self._reconstruct_table_from_text(all_text_chunks)
            if table_data and len(table_data) > 1:
                logger.debug(f"Reconstructed {len(table_data)} rows from text chunks")
                
                # Ensure data has content
                if any(any(cell for cell in row) for row in table_data):
                    self.data = table_data
                    return
                
        logger.debug("Could not reconstruct table data from IWA files")
        
    def _find_row_patterns(self, text_chunks: List[str]) -> List[List[str]]:
        """
        Look for text chunks that follow patterns indicating table rows.
        
        Args:
            text_chunks: List of text chunks extracted from IWA files
            
        Returns:
            List of rows, where each row is a list of cell values
        """
        # Common delimiters that might separate cells in a row
        delimiters = ['\t', ',', ';', '|', ' - ', '  ']  # Added more delimiter options
        
        # Find chunks that contain any of these delimiters
        delimiter_chunks = {}
        for delimiter in delimiters:
            delimiter_chunks[delimiter] = [
                chunk for chunk in text_chunks 
                if delimiter in chunk and chunk.count(delimiter) >= 1  # Reduced from 2 to 1
            ]
        
        # Find the most promising delimiter based on frequency and consistency
        best_delimiter = None
        best_rows = []
        best_score = 0
        
        for delimiter, chunks in delimiter_chunks.items():
            if len(chunks) < 3:  # Reduced from 5 to 3
                continue
                
            # Split chunks into cells
            rows = [chunk.split(delimiter) for chunk in chunks]
            
            # Count columns per row
            col_counts = [len(row) for row in rows]
            
            # Calculate consistency score
            if not col_counts:
                continue
                
            # Check column count consistency
            most_common_col_count = max(set(col_counts), key=col_counts.count)
            consistency = sum(1 for count in col_counts if count == most_common_col_count) / len(col_counts)
            
            # Score based on number of rows and consistency
            score = len(rows) * consistency
            
            if score > best_score:
                best_score = score
                best_delimiter = delimiter
                # Keep rows with the most common column count
                best_rows = [row for row, count in zip(rows, col_counts) 
                           if count == most_common_col_count or count >= most_common_col_count - 1]
        
        if best_rows:
            # Clean up each cell (strip whitespace, etc.)
            best_rows = [[cell.strip() for cell in row] for row in best_rows]
            
            # Normalize row lengths
            max_cols = max(len(row) for row in best_rows)
            best_rows = [row + [""] * (max_cols - len(row)) for row in best_rows]
            
            # Look for header-like row to put first
            header_keywords = ['id', 'name', 'price', 'cost', 'sku', 'description', 'code', 
                              'product', 'item', 'quantity', 'catalog', 'retail', 'wholesale',
                              'model', 'category', 'manufacturer', 'image', 'msrp', 'upc', 'barcode']
            
            best_header_idx = -1
            best_header_score = -1
            
            for i, row in enumerate(best_rows[:5]):  # Check first few rows
                score = 0
                row_text = ' '.join(str(cell).lower() for cell in row)
                keyword_matches = sum(1 for keyword in header_keywords if keyword in row_text)
                score += keyword_matches * 2
                
                # Headers tend to have shorter cells
                avg_len = sum(len(str(cell)) for cell in row) / max(1, len(row))
                if avg_len < 30:
                    score += max(0, (30 - avg_len) / 10)
                
                if score > best_header_score:
                    best_header_score = score
                    best_header_idx = i
            
            # If we found a likely header, move it to the front
            if best_header_idx > 0:
                header_row = best_rows.pop(best_header_idx)
                best_rows.insert(0, header_row)
            
            return best_rows
        
        return []
    
    def _extract_from_index_json(self) -> None:
        """
        Extract data from Index.json which exists in newer Numbers files.
        """
        index_path = os.path.join(self.temp_dir, 'Index', 'Document.json')
        if not os.path.exists(index_path):
            logger.debug("Index.json not found")
            return
            
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Navigate the JSON structure to find tables
            if 'docInfo' not in data:
                logger.debug("No docInfo in Index.json")
                return
                
            document_data = data['docInfo']
            
            # Find sheets
            if 'sheetInfos' in document_data:
                sheets = document_data['sheetInfos']
                self.sheet_names = [sheet.get('sheetName', f"Sheet{i}") for i, sheet in enumerate(sheets)]
                
                # Find tables
                selected_sheet = None
                
                if self.sheet_name and self.sheet_names:
                    # Find by name
                    for sheet in sheets:
                        if sheet.get('sheetName') == self.sheet_name:
                            selected_sheet = sheet
                            break
                elif sheets:
                    # Use index with bounds checking
                    sheet_idx = min(self.sheet_index, len(sheets) - 1)
                    selected_sheet = sheets[sheet_idx]
                    
                if selected_sheet and 'tableInfos' in selected_sheet:
                    tables = selected_sheet['tableInfos']
                    self.table_names = [table.get('tableName', f"Table{i}") for i, table in enumerate(tables)]
                    
                    # Select table
                    selected_table = None
                    
                    if self.table_name and self.table_names:
                        # Find by name
                        for table in tables:
                            if table.get('tableName') == self.table_name:
                                selected_table = table
                                break
                    elif tables:
                        # Use index with bounds checking
                        table_idx = min(self.table_index, len(tables) - 1)
                        selected_table = tables[table_idx]
                        
                    if selected_table:
                        # Extract table data
                        self._extract_table_data_from_json(selected_table)
        except Exception as e:
            logger.debug(f"Error processing Index.json: {str(e)}")
    
    def _extract_table_data_from_json(self, table_info: Dict[str, Any]) -> None:
        """
        Extract table data from table info in the JSON.
        
        Args:
            table_info: Table information from JSON
        """
        # Try to find associated data file for this table
        if 'tableID' in table_info:
            table_id = table_info['tableID']
            logger.debug(f"Looking for data for table ID: {table_id}")
            
            # Look for data files that might contain this table data
            data_files = []
            for root, _, files in os.walk(os.path.join(self.temp_dir, 'Data')):
                for file in files:
                    data_files.append(os.path.join(root, file))
            
            # Try to find a data file specifically for this table
            for data_file in data_files:
                # Get the simple filename
                basename = os.path.basename(data_file)
                
                # If the filename contains the table ID or something similar, it might be this table
                if table_id in basename or any(pattern in basename for pattern in ['data', 'table', 'content']):
                    logger.debug(f"Checking data file: {basename}")
                    
                    # Try to read the data file with different methods
                    try:
                        # For binary files, try extracting text content
                        with open(data_file, 'rb') as f:
                            content = f.read()
                            
                        # Try to extract text chunks from this binary content
                        chunks = self._extract_ascii_text(content)
                        if chunks:
                            logger.debug(f"Extracted {len(chunks)} chunks from {basename}")
                            
                            # Try to reconstruct a table
                            table_data = self._reconstruct_table_from_text(chunks)
                            if table_data and len(table_data) > 1:
                                logger.debug(f"Reconstructed table with {len(table_data)} rows from {basename}")
                                self.data = table_data
                                return
                            
                    except Exception as e:
                        logger.debug(f"Error processing data file {basename}: {str(e)}")
            
            logger.debug(f"Could not find data for table ID: {table_id}")
        else:
            logger.debug("No tableID found in table info")
    
    def _extract_ascii_text(self, binary_data: bytes) -> List[str]:
        """
        Extract ASCII text chunks from binary data.
        
        Args:
            binary_data: Binary data to extract text from
            
        Returns:
            List of text chunks
        """
        # Convert to ASCII, ignoring non-ASCII characters
        try:
            text = binary_data.decode('ascii', errors='ignore')
        except:
            return []
            
        # Remove control characters except newlines and tabs
        text = ''.join(c if c.isprintable() or c in ['\n', '\t'] else ' ' for c in text)
        
        # Split into chunks at null bytes or long sequences of non-text
        chunks = re.split(r'[\x00]{2,}|\s{5,}', text)
        
        # Filter out chunks that are too short or don't contain meaningful text
        filtered_chunks = []
        for chunk in chunks:
            # Normalize whitespace
            chunk = re.sub(r'\s+', ' ', chunk).strip()
            
            # Keep chunks that have enough meaningful text
            if len(chunk) >= 3 and any(c.isalnum() for c in chunk):
                filtered_chunks.append(chunk)
                
        return filtered_chunks
    
    def _reconstruct_table_from_text(self, text_chunks: List[str]) -> List[List[str]]:
        """
        Attempt to reconstruct a table from text chunks.
        
        Args:
            text_chunks: List of text chunks
            
        Returns:
            List of rows (lists of cells)
        """
        # Step 1: Clean and sort text chunks by length and content
        cleaned_chunks = []
        for chunk in text_chunks:
            # Clean up the chunk
            cleaned = re.sub(r'\s+', ' ', chunk).strip()
            if cleaned and len(cleaned) >= 3:
                cleaned_chunks.append(cleaned)
        
        # Sort by length to group similar chunks (potential rows with similar column counts)
        cleaned_chunks.sort(key=len)
        
        # Step 2: Try multiple strategies to identify rows
        
        # Strategy 1: Check for chunks that naturally split into similar cells with a consistent separator
        for separator in ['\t', ',', ';', '|', ' - ', '  ', ':', '=']:  # Added more separators
            potential_rows = []
            
            for chunk in cleaned_chunks:
                if separator in chunk:
                    cells = [cell.strip() for cell in chunk.split(separator)]
                    if len(cells) >= 2 and any(cells):  # Changed from all to any
                        potential_rows.append(cells)
            
            # If we have enough rows with consistent structure
            if len(potential_rows) >= 3:  # Reduced from 3
                col_counts = [len(row) for row in potential_rows]
                most_common_col_count = max(set(col_counts), key=col_counts.count)
                
                # If many rows have the same column count, this might be our table
                consistent_rows = [row for row in potential_rows if len(row) == most_common_col_count]
                if len(consistent_rows) >= 3:  # Reduced from 3
                    logger.debug(f"Found {len(consistent_rows)} rows using separator '{separator}'")
                    
                    # Normalize row lengths
                    max_cols = max(len(row) for row in consistent_rows)
                    consistent_rows = [row + [""] * (max_cols - len(row)) for row in consistent_rows]
                    
                    return consistent_rows
        
        # Strategy 2: Look for chunks with similar patterns that might be rows
        # Group chunks that might belong to the same row type based on pattern similarity
        pattern_groups = {}
        
        for chunk in cleaned_chunks:
            # Create a simple pattern signature: letter/number/symbol pattern
            pattern = ''.join('A' if c.isalpha() else 
                             'N' if c.isdigit() else 
                             'S' for c in chunk[:20])  # Use first 20 chars for pattern
            
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(chunk)
        
        # Find the largest group of similar patterns
        largest_group = []
        for pattern, group in pattern_groups.items():
            if len(group) > len(largest_group):
                largest_group = group
        
        # If we have a large enough group, try to parse it as rows
        if len(largest_group) >= 3:  # Reduced from 5
            # See if these chunks split naturally along some common delimiter
            for separator in [' ', '\t', ',', ';', '|', '-', ':', '=']:  # Added more separators
                potential_rows = []
                for chunk in largest_group:
                    if separator in chunk:
                        cells = [cell.strip() for cell in chunk.split(separator)]
                        if len(cells) >= 2 and any(cells):  # Changed from all to any
                            potential_rows.append(cells)
                
                if len(potential_rows) >= 3:  # Reduced from 3
                    # Check column count consistency
                    col_counts = [len(row) for row in potential_rows]
                    most_common_col_count = max(set(col_counts), key=col_counts.count)
                    consistent_rows = [row for row in potential_rows if len(row) == most_common_col_count]
                    
                    if len(consistent_rows) >= 3:  # Reduced from 3
                        logger.debug(f"Found {len(consistent_rows)} pattern-based rows")
                        
                        # Normalize row lengths
                        max_cols = max(len(row) for row in consistent_rows)
                        consistent_rows = [row + [""] * (max_cols - len(row)) for row in consistent_rows]
                        
                        return consistent_rows
        
        # Strategy 3: Try to group chunks by line-like patterns (potential rows)
        # This is a more aggressive strategy to try when others fail
        
        # Sort chunks by length first to group similar-sized chunks
        length_sorted_chunks = sorted(cleaned_chunks, key=len)
        
        # Group chunks by similar lengths (potential cells in the same column)
        length_groups = {}
        for chunk in length_sorted_chunks:
            # Round length to nearest 5 to group similar lengths
            length_key = (len(chunk) // 5) * 5
            if length_key not in length_groups:
                length_groups[length_key] = []
            length_groups[length_key].append(chunk)
        
        # Find the largest groups
        large_groups = sorted([(length, chunks) for length, chunks in length_groups.items() 
                             if len(chunks) >= 3], key=lambda x: len(x[1]), reverse=True)
        
        if large_groups:
            # Try to reconstruct rows from these groups
            potential_rows = []
            
            # Start with a chunk from the largest group as the first cell in each row
            first_group = large_groups[0][1]
            
            for first_cell in first_group[:10]:  # Limit to first 10 chunks
                row = [first_cell]
                
                # Try to find related chunks for this row
                for _, group in large_groups[1:4]:  # Use up to 3 more groups
                    best_match = None
                    best_score = -1
                    
                    for chunk in group:
                        score = self._chunks_might_be_related(first_cell, chunk)
                        if score > best_score:
                            best_score = score
                            best_match = chunk
                    
                    if best_match:
                        row.append(best_match)
                        # Remove this chunk so it's not used again
                        group.remove(best_match)
                
                if len(row) >= 2:  # At least 2 cells
                    potential_rows.append(row)
            
            if len(potential_rows) >= 3:
                # Normalize row lengths
                max_cols = max(len(row) for row in potential_rows)
                potential_rows = [row + [""] * (max_cols - len(row)) for row in potential_rows]
                
                logger.debug(f"Reconstructed {len(potential_rows)} rows using length-based grouping")
                return potential_rows
        
        # Strategy 4: Last resort - try to construct a table from any recognizable patterns
        # Look for header-like chunks
        header_candidates = []
        for chunk in cleaned_chunks:
            lower_chunk = chunk.lower()
            if any(keyword in lower_chunk for keyword in ['sku', 'name', 'price', 'cost', 'description', 'model']):
                header_candidates.append(chunk)
                
        if header_candidates:
            # Try to split the most promising header candidate
            best_header = max(header_candidates, key=len)
            
            # Try various delimiters
            for separator in ['\t', ',', ';', '|', ' - ', '  ', ':', '=']:
                if separator in best_header:
                    header_cells = [cell.strip() for cell in best_header.split(separator)]
                    if len(header_cells) >= 2:
                        # Try to construct data rows
                        data_rows = []
                        for chunk in cleaned_chunks:
                            if chunk != best_header and separator in chunk:
                                data_cells = [cell.strip() for cell in chunk.split(separator)]
                                if len(data_cells) >= len(header_cells) - 1:  # Allow 1 fewer cell
                                    # Normalize to header length
                                    while len(data_cells) < len(header_cells):
                                        data_cells.append("")
                                    data_rows.append(data_cells)
                                    
                        if len(data_rows) >= 2:  # At least 2 data rows
                            result = [header_cells] + data_rows
                            logger.debug(f"Constructed table with {len(result)} rows from header pattern")
                            return result
        
        return []
        
    def _chunks_might_be_related(self, chunk1: str, chunk2: str) -> float:
        """
        Check if two chunks might be related (cells in the same row).
        
        Args:
            chunk1: First chunk
            chunk2: Second chunk
            
        Returns:
            Score indicating likelihood of relation (higher is better)
        """
        # Calculate similarity score
        score = 0.0
        
        # Check for similar length (less important)
        length_diff = abs(len(chunk1) - len(chunk2))
        if length_diff < 10:
            score += (10 - length_diff) / 10  # Up to 1.0 point
            
        # Check for similar character types (very important)
        c1_alpha = sum(1 for c in chunk1 if c.isalpha()) / max(1, len(chunk1))
        c2_alpha = sum(1 for c in chunk2 if c.isalpha()) / max(1, len(chunk2))
        
        c1_digit = sum(1 for c in chunk1 if c.isdigit()) / max(1, len(chunk1))
        c2_digit = sum(1 for c in chunk2 if c.isdigit()) / max(1, len(chunk2))
        
        # Character type similarity (higher is better)
        alpha_sim = 1.0 - abs(c1_alpha - c2_alpha)
        digit_sim = 1.0 - abs(c1_digit - c2_digit)
        score += (alpha_sim + digit_sim) * 2  # Up to 4.0 points
        
        # Check for similar word count
        words1 = [w for w in chunk1.split() if w]
        words2 = [w for w in chunk2.split() if w]
        word_diff = abs(len(words1) - len(words2))
        if word_diff < 3:
            score += (3 - word_diff) / 3  # Up to 1.0 point
            
        # Check if either is mostly numbers (might be a price field)
        if c1_digit > 0.5 or c2_digit > 0.5:
            score += 1.0  # Bonus point for numeric fields
            
        return score