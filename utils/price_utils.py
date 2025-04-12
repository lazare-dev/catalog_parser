#!/usr/bin/env python3
"""
Price handling utilities for normalizing and processing price values
across different formats and currencies.
"""

import re
import logging
from typing import Any, Optional, Tuple, Dict, List

from config.settings import DECIMAL_SEPARATORS, THOUSAND_SEPARATORS, CURRENCY_SYMBOLS
from config.field_mappings import CURRENCY_INDICATORS, ROW_PRICE_PATTERNS

logger = logging.getLogger(__name__)

class PriceUtils:
    """
    Utility class for handling price fields and values.
    """
    
    @staticmethod
    def normalize_price(value: Any) -> Optional[float]:
        """
        Normalize price value to float.
        
        Args:
            value: Price value in various formats
            
        Returns:
            Normalized price as float or None if invalid
        """
        if value is None:
            return None
            
        # Already a number
        if isinstance(value, (int, float)):
            return float(value)
            
        # String value needs parsing
        if isinstance(value, str):
            # Remove currency symbols, spaces, and other non-numeric characters
            cleaned = re.sub(r'[^\d\.,]', '', value.strip())
            
            if not cleaned:
                return None
                
            try:
                # Handle different decimal and thousand separators
                if ',' in cleaned and '.' in cleaned:
                    # Need to determine which is which
                    if cleaned.rindex(',') > cleaned.rindex('.'):
                        # Format like 1.234,56
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    else:
                        # Format like 1,234.56
                        cleaned = cleaned.replace(',', '')
                elif ',' in cleaned:
                    # Could be either decimal or thousand separator
                    if len(cleaned.split(',')[-1]) in [0, 1, 2, 3]:
                        # Likely a decimal separator
                        cleaned = cleaned.replace(',', '.')
                    else:
                        # Likely a thousand separator
                        cleaned = cleaned.replace(',', '')
                
                return float(cleaned)
            except ValueError:
                logger.warning(f"Could not parse price value: {value}")
                return None
                
        return None
    
    @staticmethod
    def detect_currency(value: str) -> Optional[str]:
        """
        Detect currency from a price string.
        
        Args:
            value: Price string
            
        Returns:
            Currency code ('GBP', 'USD', 'EUR') or None
        """
        if not value or not isinstance(value, str):
            return None
            
        value_lower = value.lower()
        
        # Check for currency symbols and codes
        for currency, indicators in CURRENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in value_lower:
                    return currency
                    
        # No currency detected
        return None
    
    @staticmethod
    def extract_prices_from_row_format(row_data: str) -> Dict[str, float]:
        """
        Extract prices from row-based format text.
        
        Args:
            row_data: Text containing price information
            
        Returns:
            Dictionary mapping price field types to values
        """
        if not row_data or not isinstance(row_data, str):
            return {}
            
        prices = {}
        
        # Check each price type pattern
        for price_type, patterns in ROW_PRICE_PATTERNS.items():
            for pattern in patterns:
                # Find matches in the text
                matches = re.finditer(pattern, row_data, re.IGNORECASE)
                
                for match in matches:
                    # Look for a number after the match
                    start_pos = match.end()
                    price_text = re.search(r'[-+]?\d[\d\s,\.]*', row_data[start_pos:start_pos+50])
                    
                    if price_text:
                        price_value = PriceUtils.normalize_price(price_text.group())
                        if price_value is not None:
                            # For MSRP, detect currency
                            if price_type == "MSRP":
                                currency = PriceUtils.detect_currency(row_data[start_pos-20:start_pos+50])
                                if currency:
                                    prices[f"MSRP {currency}"] = price_value
                                else:
                                    # Default to generic MSRP if no currency detected
                                    prices[price_type] = price_value
                            else:
                                prices[price_type] = price_value
                            
                            # Once we find a valid price, move to next pattern
                            break
        
        return prices
    
    @staticmethod
    def validate_price_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean price fields in a data row.
        
        Args:
            data: Dictionary containing data fields
            
        Returns:
            Dictionary with validated price fields
        """
        price_fields = ["Buy Cost", "Trade Price", "MSRP GBP", "MSRP USD", "MSRP EUR"]
        
        for field in price_fields:
            if field in data:
                data[field] = PriceUtils.normalize_price(data[field])
        
        # Handle potential mismatches in currency fields
        generic_msrp = data.get("MSRP")
        if generic_msrp is not None:
            # Try to determine currency
            for currency_field in ["MSRP GBP", "MSRP USD", "MSRP EUR"]:
                if currency_field not in data or data[currency_field] is None:
                    # Extract the currency code
                    currency = currency_field.split()[-1]
                    
                    # If we can find a currency hint somewhere
                    if any(hint in str(data).lower() for hint in CURRENCY_INDICATORS.get(currency, [])):
                        data[currency_field] = generic_msrp
                        
            # Remove the generic field
            data.pop("MSRP", None)
                        
        return data
    
    @staticmethod
    def extract_prices_from_description(description: str) -> Dict[str, float]:
        """
        Extract price information from product descriptions.
        
        Args:
            description: Product description text
            
        Returns:
            Dictionary mapping price field types to values
        """
        if not description or not isinstance(description, str):
            return {}
            
        # Use the same logic as row-based format
        return PriceUtils.extract_prices_from_row_format(description)