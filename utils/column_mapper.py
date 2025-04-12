#!/usr/bin/env python3
"""
Column mapper utility for mapping source columns to target fields.
This is the heart of the intelligent field detection system.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

from config.target_fields import TARGET_FIELDS
from config.field_mappings import (
    FIELD_PATTERNS, 
    GENERIC_MSRP_PATTERNS, 
    CURRENCY_INDICATORS
)
from config.settings import CONFIDENCE_THRESHOLD
from utils.ml_model import ml_fallback_model

logger = logging.getLogger(__name__)

class ColumnMapper:
    """
    Utility class for mapping source columns to target fields using
    pattern matching and scoring algorithms.
    """
    
    def __init__(self):
        self.confidence_threshold = CONFIDENCE_THRESHOLD
    
    def map_columns(self, headers: List[str]) -> Dict[str, str]:
        """
        Map source headers to target fields based on pattern matching.
        
        Args:
            headers: List of source header strings
            
        Returns:
            Dictionary mapping target fields to source headers
        """
        logger.info(f"Mapping {len(headers)} headers to target fields")
        
        # Clean and normalize headers
        cleaned_headers = [self._clean_header(h) for h in headers]
        
        # Store results: {target_field: (source_header, confidence_score)}
        mapping_results = {}
        
        # First pass: exact pattern matches
        self._apply_pattern_matching(cleaned_headers, headers, mapping_results)
        
        # Second pass: handle generic MSRP fields with currency detection
        self._handle_generic_msrp(cleaned_headers, headers, mapping_results)
        
        # Third pass: fuzzy matching for unmatched fields
        self._apply_fuzzy_matching(cleaned_headers, headers, mapping_results)
        
        # Build final mapping
        field_mapping = {
            target: orig_header
            for target, (orig_header, _) in mapping_results.items()
        }
        
        logger.info(f"Mapped {len(field_mapping)}/{len(TARGET_FIELDS)} fields")
        return field_mapping
    
    def _clean_header(self, header: str) -> str:
        """
        Clean and normalize a header string for better matching.
        
        Args:
            header: Original header string
            
        Returns:
            Cleaned header string
        """
        if header is None:
            return ""
            
        # Convert to string if not already
        if not isinstance(header, str):
            header = str(header)
            
        # Remove leading/trailing whitespace
        header = header.strip()
        
        # Normalize whitespace
        header = re.sub(r'\s+', ' ', header)
        
        # Remove special characters often found in headers
        header = re.sub(r'[_\-\.\[\]\(\)\{\}\*\+\?\^\$\|]', ' ', header)
        
        # Remove duplicate spaces
        header = re.sub(r'\s+', ' ', header)
        
        # Normalize case
        header = header.lower()
        
        return header.strip()
    
    def _apply_pattern_matching(
        self, 
        cleaned_headers: List[str], 
        original_headers: List[str],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Apply regex pattern matching to map headers to target fields.
        
        Args:
            cleaned_headers: List of cleaned header strings
            original_headers: List of original header strings
            results: Dictionary to store results
        """
        logger.debug("Applying pattern matching")
        
        for target_field in TARGET_FIELDS:
            if target_field in results:
                continue
                
            patterns = FIELD_PATTERNS.get(target_field, [])
            best_match = None
            best_score = 0.0
            
            for i, cleaned_header in enumerate(cleaned_headers):
                for pattern in patterns:
                    if re.match(pattern, cleaned_header):
                        # Direct match, high confidence
                        score = 1.0
                        if score > best_score:
                            best_score = score
                            best_match = (original_headers[i], score)
                            break
            
            if best_match and best_score >= self.confidence_threshold:
                results[target_field] = best_match
    
    def _handle_generic_msrp(
        self, 
        cleaned_headers: List[str], 
        original_headers: List[str],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Handle generic MSRP fields with currency detection.
        
        Args:
            cleaned_headers: List of cleaned header strings
            original_headers: List of original header strings
            results: Dictionary to store results
        """
        logger.debug("Handling generic MSRP fields")
        
        # Skip if all MSRP fields are already mapped
        if all(f in results for f in ["MSRP GBP", "MSRP USD", "MSRP EUR"]):
            return
            
        # Find generic MSRP headers
        generic_msrp_headers = []
        
        for i, cleaned_header in enumerate(cleaned_headers):
            for pattern in GENERIC_MSRP_PATTERNS:
                if re.match(pattern, cleaned_header):
                    generic_msrp_headers.append((i, original_headers[i], cleaned_header))
                    break
        
        # If we found generic MSRP headers, try to assign them to specific currencies
        for i, orig_header, cleaned_header in generic_msrp_headers:
            currency = self._detect_currency(orig_header, cleaned_header)
            if currency:
                target_field = f"MSRP {currency}"
                if target_field in TARGET_FIELDS and target_field not in results:
                    results[target_field] = (orig_header, 0.9)
    
    def _detect_currency(self, header: str, cleaned_header: str) -> Optional[str]:
        """
        Detect currency from a header string.
        
        Args:
            header: Original header string
            cleaned_header: Cleaned header string
            
        Returns:
            Currency code (GBP, USD, EUR) or None
        """
        # First check original header for currency symbols/codes
        for currency, indicators in CURRENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in header.lower():
                    return currency
        
        # No currency detected
        return None
        
    def _apply_fuzzy_matching(
        self, 
        cleaned_headers: List[str], 
        original_headers: List[str],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Apply fuzzy matching for unmatched fields using similarity scoring.
        
        Args:
            cleaned_headers: List of cleaned header strings
            original_headers: List of original header strings
            results: Dictionary to store results
        """
        logger.debug("Applying fuzzy matching for remaining fields")
        
        # Only process unmatched target fields
        unmatched_targets = [f for f in TARGET_FIELDS if f not in results]
        
        # Skip if all fields are matched
        if not unmatched_targets:
            return
            
        # Skip if no headers are available
        if not cleaned_headers:
            return
            
        # For each unmatched target field
        for target_field in unmatched_targets:
            best_match = None
            best_score = 0.0
            
            # Try direct string similarity with field name
            target_keywords = target_field.lower().split()
            
            for i, cleaned_header in enumerate(cleaned_headers):
                # Skip headers already mapped to other fields
                if original_headers[i] in [v[0] for v in results.values()]:
                    continue
                    
                # Calculate similarity score
                similarity = self._calculate_similarity(target_field, cleaned_header)
                
                # Check keyword presence
                keyword_score = 0
                for keyword in target_keywords:
                    if keyword in cleaned_header:
                        keyword_score += 0.2  # Boost for each keyword found
                
                # Combined score (max 1.0)
                combined_score = min(similarity + keyword_score, 1.0)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = (original_headers[i], combined_score)
            
            # Only accept match if score is above threshold
            if best_match and best_score >= self.confidence_threshold:
                results[target_field] = best_match

# ML fallback for unmapped headers
        for i, cleaned_header in enumerate(cleaned_headers):
            original = original_headers[i]
            if original in [v[0] for v in results.values()]:
                continue  # already mapped

            prediction = ml_fallback_model.predict([cleaned_header])[0]
            confidence = max(ml_fallback_model.predict_proba([cleaned_header])[0])

            if confidence >= self.confidence_threshold:
                if prediction not in results:
                    results[prediction] = (original, confidence)
                    logger.info(f"ML fallback mapped '{original}' to '{prediction}' (confidence: {confidence:.2f})")

def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using SequenceMatcher.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()