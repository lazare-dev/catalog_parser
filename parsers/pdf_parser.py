#!/usr/bin/env python3
"""
PDF parser for extracting catalog data from PDF files.
"""

import os
import re
import logging
import tempfile
from typing import List, Dict, Any, Tuple, Optional, Iterator
from io import StringIO

from parsers.base_parser import BaseParser
from utils.error_handler import ParserError, FileError, log_error
from utils.manufacturer_detector import ManufacturerDetector
from utils.price_utils import PriceUtils

# Import PDF libraries - handle gracefully if not available
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pdfplumber not installed, PDF support limited")
    
try:
    import tabula
    TABULA_SUPPORT = True
except ImportError:
    TABULA_SUPPORT = False
    logging.warning("tabula-py not installed, PDF table extraction limited")

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """
    Parser for PDF files. Extracts tabular data and text from PDFs.
    """
    
    def __init__(self, filename: str, page_range: Optional[str] = None):
        """
        Initialize the PDF parser.
        
        Args:
            filename: Path to the PDF file
            page_range: Page range to extract (e.g., '1-5', '2,3,6')
        """
        super().__init__(filename)
        
        if not PDF_SUPPORT:
            raise ImportError("PDF parsing requires pdfplumber. Please install with: pip install pdfplumber")
        
        self.page_range = page_range
        self.pages = []
        self.tables = []
        self.extracted_text = ""
        self.manufacturer_detector = ManufacturerDetector()
        
    def read_file(self) -> None:
        """
        Read and extract data from the PDF file.
        """
        logger.info(f"Reading PDF file: {self.basename}")
        
        try:
            # Extract tables first
            self._extract_tables()
            
            # If no tables found, extract text
            if not self.tables:
                self._extract_text()
                
                # Try to parse extracted text into structured data
                self._parse_extracted_text()
            else:
                # Convert tables to common data structure
                self._process_tables()
                
            if not self.data:
                raise FileError("Could not extract usable data from PDF")
                
            logger.info(f"Successfully extracted data from PDF: {len(self.data)} rows")
            
        except Exception as e:
            error_msg = f"Error processing PDF file: {str(e)}"
            logger.error(error_msg)
            raise FileError(error_msg)
            
    def _extract_tables(self) -> None:
        """
        Extract tables from the PDF.
        """
        logger.info("Attempting to extract tables from PDF")
        
        try:
            # Try tabula first if available
            if TABULA_SUPPORT:
                self._extract_tables_with_tabula()
                
            # Fallback to pdfplumber if no tables found
            if not self.tables:
                self._extract_tables_with_pdfplumber()
                
            if self.tables:
                logger.info(f"Successfully extracted {len(self.tables)} tables from PDF")
            else:
                logger.warning("No tables found in PDF")
                
        except Exception as e:
            logger.warning(f"Table extraction failed: {str(e)}")
            self.tables = []
            
    def _extract_tables_with_tabula(self) -> None:
        """
        Extract tables using tabula-py library.
        """
        try:
            # Parse tables from all pages by default
            pages = self.page_range if self.page_range else 'all'
            
            # Extract tables
            tables = tabula.read_pdf(
                self.filename, 
                pages=pages, 
                multiple_tables=True,
                guess=True,
                pandas_options={'header': None}
            )
            
            # Convert pandas DataFrames to lists
            for table in tables:
                if not table.empty:
                    # Convert DataFrame to list of lists
                    table_data = table.fillna("").values.tolist()
                    self.tables.append(table_data)
                    
        except Exception as e:
            logger.warning(f"Tabula table extraction failed: {str(e)}")
            
    def _extract_tables_with_pdfplumber(self) -> None:
        """
        Extract tables using pdfplumber library.
        """
        try:
            with pdfplumber.open(self.filename) as pdf:
                # Get page range
                if self.page_range:
                    # Parse page range (e.g., '1-5', '2,3,6')
                    pages_to_extract = self._parse_page_range(self.page_range, len(pdf.pages))
                    pdf_pages = [pdf.pages[i-1] for i in pages_to_extract if 0 < i <= len(pdf.pages)]
                else:
                    pdf_pages = pdf.pages
                    
                for page in pdf_pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and any(any(cell for cell in row) for row in table):
                            # Clean table data
                            cleaned_table = [
                                [str(cell).strip() if cell is not None else "" for cell in row]
                                for row in table
                            ]
                            self.tables.append(cleaned_table)
                            
        except Exception as e:
            logger.warning(f"PDFPlumber table extraction failed: {str(e)}")
            
    def _parse_page_range(self, page_range: str, max_pages: int) -> List[int]:
        """
        Parse page range specification.
        
        Args:
            page_range: Page range string (e.g., '1-5', '2,3,6')
            max_pages: Maximum number of pages
            
        Returns:
            List of page numbers
        """
        pages = []
        
        # Split by comma
        parts = page_range.split(',')
        
        for part in parts:
            part = part.strip()
            
            if '-' in part:
                # Range (e.g., '1-5')
                try:
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start, min(end + 1, max_pages + 1)))
                except ValueError:
                    logger.warning(f"Invalid page range: {part}")
            else:
                # Single page
                try:
                    page = int(part)
                    if 1 <= page <= max_pages:
                        pages.append(page)
                except ValueError:
                    logger.warning(f"Invalid page number: {part}")
                    
        return sorted(set(pages))
        
    def _extract_text(self) -> None:
        """
        Extract text content from the PDF.
        """
        logger.info("Extracting text from PDF")
        
        try:
            text_content = []
            
            with pdfplumber.open(self.filename) as pdf:
                # Get page range
                if self.page_range:
                    pages_to_extract = self._parse_page_range(self.page_range, len(pdf.pages))
                    pdf_pages = [pdf.pages[i-1] for i in pages_to_extract if 0 < i <= len(pdf.pages)]
                else:
                    pdf_pages = pdf.pages
                    
                for page in pdf_pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                        
            self.extracted_text = '\n'.join(text_content)
            
            if not self.extracted_text.strip():
                logger.warning("No text content extracted from PDF")
                
        except Exception as e:
            logger.warning(f"Text extraction failed: {str(e)}")
            self.extracted_text = ""
            
    def _process_tables(self) -> None:
        """
        Process extracted tables into a common data structure.
        """
        if not self.tables:
            return
            
        # Find the most promising table (largest with good data)
        best_table = None
        best_score = -1
        
        for table in self.tables:
            if not table:
                continue
                
            # Skip very small tables
            if len(table) < 2 or len(table[0]) < 2:
                continue
                
            # Score table based on size and data quality
            rows = len(table)
            cols = max(len(row) for row in table)
            data_cells = sum(sum(1 for cell in row if cell.strip()) for row in table)
            
            # Calculate score - prefer tables with more data cells and columns
            score = data_cells + cols * 2
            
            if score > best_score:
                best_score = score
                best_table = table
                
        if not best_table:
            logger.warning("No suitable tables found in PDF")
            return
            
        # Use the best table as our data
        self.data = best_table
        
    def _parse_extracted_text(self) -> None:
        """
        Parse extracted text into structured data if no tables found.
        """
        if not self.extracted_text:
            return
            
        logger.info("Parsing extracted text into structured data")
        
        # Try to identify product entries in the text
        from parsers.text_parser import TextParser
        
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(self.extracted_text)
            temp_path = temp_file.name
            
        try:
            # Use the text parser to handle the content
            text_parser = TextParser(temp_path)
            text_parser.read_file()
            
            # Get data from text parser
            if text_parser.data:
                self.data = text_parser.data
                logger.info(f"Successfully parsed text into {len(self.data)} rows")
            else:
                logger.warning("Text parser could not extract structured data")
                
        except Exception as e:
            logger.warning(f"Error using text parser: {str(e)}")
            
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_path)
            except:
                pass
                
    def detect_headers(self) -> List[str]:
        """
        Detect and extract headers from the PDF data.
        
        Returns:
            List of header strings
        """
        logger.info("Detecting headers in PDF data")
        
        if not self.data:
            logger.warning("No data available to detect headers")
            return []
            
        # For table data, assume first row contains headers
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
            if not row or all(not str(cell).strip() for cell in row):
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
        Transform raw data to the target schema, with special handling for PDF data.
        
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