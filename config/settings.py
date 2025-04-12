#!/usr/bin/env python3
"""
General settings and configuration for the catalog parser.
Centralized location for all configurable parameters.
"""
import os
import logging
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'
TEMP_DIR = BASE_DIR / 'temp'
OUTPUT_DIR = BASE_DIR / 'output'

# Create directories if they don't exist
for directory in [LOGS_DIR, TEMP_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOGS_DIR / 'catalog_parser.log'

# File processing settings
SUPPORTED_EXTENSIONS = {
    'excel': ['.xlsx', '.xls', '.xlsm'],
    'csv': ['.csv'],
    'text': ['.txt', '.text'],
    'numbers': ['.numbers'],
    'pdf': ['.pdf']
}

# CSV output settings
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'
CSV_ENCODING = 'utf-8-sig'  # With BOM for Excel compatibility

# Parser settings
MAX_HEADER_ROWS = 10  # Maximum number of rows to check for headers
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence score to accept a field match
FALLBACK_ENCODING = 'latin-1'  # Fallback encoding for text files

# Manufacturer detection settings
COMMON_MANUFACTURERS = [
    'apple', 'samsung', 'sony', 'lg', 'dell', 'hp', 'lenovo', 'asus', 
    'acer', 'toshiba', 'microsoft', 'philips', 'panasonic', 'bosch', 
    'siemens', 'canon', 'nikon', 'intel', 'amd', 'nvidia'
]

# Price format settings
DECIMAL_SEPARATORS = ['.', ',']
THOUSAND_SEPARATORS = [',', '.', ' ']
CURRENCY_SYMBOLS = ['$', '£', '€', 'USD', 'GBP', 'EUR']

# Web application settings
WEB_HOST = '0.0.0.0'
WEB_PORT = int(os.environ.get('PORT', 8080))
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB