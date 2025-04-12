#!/usr/bin/env python3
"""
Manufacturer detection utility to extract manufacturer information
from filenames and catalog content.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

from config.settings import COMMON_MANUFACTURERS

logger = logging.getLogger(__name__)

class ManufacturerDetector:
    """
    Utility class for detecting manufacturer information.
    """
    
    def __init__(self, additional_manufacturers: List[str] = None):
        """
        Initialize with optional additional manufacturers.
        
        Args:
            additional_manufacturers: Additional manufacturer names to detect
        """
        self.manufacturers = set(COMMON_MANUFACTURERS)
        
        if additional_manufacturers:
            self.manufacturers.update([m.lower() for m in additional_manufacturers])
            
        logger.debug(f"Initialized manufacturer detector with {len(self.manufacturers)} manufacturers")
    
    def detect_from_filename(self, filename: str) -> Optional[str]:
        """
        Detect manufacturer from filename.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            Detected manufacturer name or None
        """
        if not filename:
            return None
            
        # Extract just the basename without extension
        basename = os.path.splitext(os.path.basename(filename))[0].lower()
        
        # Replace common separators with spaces
        normalized = re.sub(r'[_\-\.\(\)]', ' ', basename)
        
        # Check for exact manufacturer names
        for manufacturer in self.manufacturers:
            # Match full word only (surrounded by spaces or start/end of string)
            pattern = r'(^|\s)' + re.escape(manufacturer) + r'(\s|$)'
            if re.search(pattern, normalized, re.IGNORECASE):
                logger.info(f"Detected manufacturer from filename: {manufacturer}")
                return manufacturer.title()  # Return with title case
                
        # Try more flexible matching for compound names
        words = normalized.split()
        for manufacturer in self.manufacturers:
            mfr_words = manufacturer.lower().split()
            
            # If multi-word manufacturer, check if all words appear in sequence
            if len(mfr_words) > 1:
                for i in range(len(words) - len(mfr_words) + 1):
                    if words[i:i+len(mfr_words)] == mfr_words:
                        logger.info(f"Detected multi-word manufacturer from filename: {manufacturer}")
                        return manufacturer.title()
        
        # No manufacturer detected
        logger.debug(f"No manufacturer detected from filename: {filename}")
        return None
    
    def detect_from_data(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Detect potential manufacturers from data content.
        
        Args:
            data: List of data rows
            
        Returns:
            Dictionary of manufacturer candidates with frequency counts
        """
        manufacturer_counts = {}
        
        # Function to check a field value for manufacturer names
        def check_field(value):
            if not value or not isinstance(value, str):
                return
                
            value_lower = value.lower()
            for manufacturer in self.manufacturers:
                if manufacturer in value_lower:
                    manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1
        
        # Check relevant fields in each row
        for row in data:
            for field in ['Manufacturer', 'Short Description', 'Long Description']:
                if field in row:
                    check_field(row[field])
        
        # Sort by frequency
        sorted_manufacturers = {
            k: v for k, v in sorted(
                manufacturer_counts.items(), 
                key=lambda item: item[1], 
                reverse=True
            )
        }
        
        if sorted_manufacturers:
            logger.info(f"Detected manufacturers from data: {sorted_manufacturers}")
        else:
            logger.debug("No manufacturers detected from data")
            
        return sorted_manufacturers
    
    def get_most_likely_manufacturer(self, data: List[Dict[str, Any]], filename: str) -> Optional[str]:
        """
        Get the most likely manufacturer based on filename and data content.
        
        Args:
            data: List of data rows
            filename: Filename
            
        Returns:
            Most likely manufacturer name or None
        """
        # First try from filename - highest confidence
        filename_manufacturer = self.detect_from_filename(filename)
        if filename_manufacturer:
            return filename_manufacturer
            
        # Then try from data content
        data_manufacturers = self.detect_from_data(data)
        if data_manufacturers:
            # Return the most frequent
            return list(data_manufacturers.keys())[0].title()
            
        return None