#!/usr/bin/env python3
"""
Column mapper utility for mapping source columns to target fields.
This is the heart of the intelligent field detection system.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Any, Set
from difflib import SequenceMatcher
from collections import Counter

from config.target_fields import TARGET_FIELDS
from config.field_mappings import (
    FIELD_PATTERNS,
    GENERIC_MSRP_PATTERNS,
    CURRENCY_INDICATORS,
    CURRENCY_VALUE_PATTERNS,
    FIELD_VALUE_FORMATS,
    FIELD_RELATIONSHIPS,
    FIELD_UNITS,
    HEADER_SYNONYMS
)
from config.settings import CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

class ColumnMapper:
    """
    Utility class for mapping source columns to target fields using
    pattern matching and scoring algorithms.
    """
    
    def __init__(self):
        self.confidence_threshold = CONFIDENCE_THRESHOLD
    
    def map_columns(self, headers: List[str], sample_data: List[List[Any]] = None) -> Dict[str, str]:
        """
        Map source headers to target fields based on pattern matching.
        
        Args:
            headers: List of source header strings
            sample_data: Sample data rows for content-based analysis
            
        Returns:
            Dictionary mapping target fields to source headers
        """
        logger.info(f"Mapping {len(headers)} headers to target fields")
        
        # Clean and normalize headers
        cleaned_headers = [self._clean_header(h) for h in headers]
        
        # Store all information extracted from headers
        # Format: {header_index: {attribute: value}}
        header_info = {}
        
        # Extract information from headers (brackets, parentheses, etc.)
        for i, (header, cleaned) in enumerate(zip(headers, cleaned_headers)):
            header_info[i] = self._extract_header_info(header, cleaned)
        
        # Store results: {target_field: (source_header, confidence_score)}
        mapping_results = {}
        
        # First pass: exact pattern matches
        self._apply_pattern_matching(cleaned_headers, headers, mapping_results)
        
        # Second pass: handle generic MSRP fields with currency detection
        self._handle_generic_msrp(cleaned_headers, headers, header_info, mapping_results)
        
        # Third pass: apply content-based detection if sample data is available
        if sample_data and len(sample_data) > 0:
            self._apply_content_based_detection(headers, sample_data, mapping_results)
        
        # Fourth pass: apply contextual field detection
        self._apply_contextual_detection(headers, cleaned_headers, mapping_results)
        
        # Fifth pass: fuzzy matching for unmatched fields
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
        
        # Replace special characters with spaces, but preserve currency symbols
        header = re.sub(r'[_\-\.\[\]\(\)\{\}\*\+\?\^\$\|]', ' ', header)
        header = re.sub(r'[^\w\s£$€]', ' ', header)  # Keep only alphanumeric and currency
        
        # Remove duplicate spaces
        header = re.sub(r'\s+', ' ', header)
        
        # Normalize case
        header = header.lower()
        
        return header.strip()
    
    def _extract_header_info(self, header: str, cleaned_header: str) -> Dict[str, Any]:
        """
        Extract additional information from a header string.
        
        Args:
            header: Original header string
            cleaned_header: Cleaned header string
            
        Returns:
            Dictionary of extracted information
        """
        info = {
            "original": header,
            "cleaned": cleaned_header,
            "brackets": [],
            "parentheses": [],
            "has_currency": False,
            "currency": None
        }
        
        # Extract content within brackets
        brackets = re.findall(r'\[(.*?)\]', header)
        if brackets:
            info["brackets"] = brackets
        
        # Extract content within parentheses
        parentheses = re.findall(r'\((.*?)\)', header)
        if parentheses:
            info["parentheses"] = parentheses
        
        # Detect currency indicators
        for currency, indicators in CURRENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in header.lower():
                    info["has_currency"] = True
                    info["currency"] = currency
                    break
            if info["has_currency"]:
                break
        
        return info
    
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
                # Skip headers already mapped to other fields with high confidence
                if original_headers[i] in [v[0] for k, v in results.items() if v[1] > 0.9]:
                    continue
                    
                for pattern in patterns:
                    # Try exact match first
                    if re.match(pattern, cleaned_header):
                        # Direct match, high confidence
                        score = 1.0
                        if score > best_score:
                            best_score = score
                            best_match = (original_headers[i], score)
                            break
                    
                    # Try partial match
                    if not best_match and re.search(pattern, cleaned_header):
                        # Partial match, good confidence
                        score = 0.8
                        if score > best_score:
                            best_score = score
                            best_match = (original_headers[i], score)
            
            if best_match and best_score >= self.confidence_threshold:
                results[target_field] = best_match
    
    def _handle_generic_msrp(
        self, 
        cleaned_headers: List[str], 
        original_headers: List[str],
        header_info: Dict[int, Dict[str, Any]],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Handle generic MSRP fields with currency detection.
        
        Args:
            cleaned_headers: List of cleaned header strings
            original_headers: List of original header strings
            header_info: Header information dictionary
            results: Dictionary to store results
        """
        logger.debug("Handling generic MSRP fields")
        
        # Skip if all MSRP fields are already mapped
        if all(f in results for f in ["MSRP GBP", "MSRP USD", "MSRP EUR"]):
            return
            
        # Find generic MSRP headers
        generic_msrp_headers = []
        
        for i, cleaned_header in enumerate(cleaned_headers):
            # Skip headers already mapped to other fields
            if original_headers[i] in [v[0] for v in results.values()]:
                continue
                
            for pattern in GENERIC_MSRP_PATTERNS:
                if re.match(pattern, cleaned_header) or re.search(pattern, cleaned_header):
                    generic_msrp_headers.append((i, original_headers[i], cleaned_header))
                    break
        
        # If we found generic MSRP headers, try to assign them to specific currencies
        for i, orig_header, cleaned_header in generic_msrp_headers:
            # Check if header has currency information
            if header_info[i]["has_currency"]:
                currency = header_info[i]["currency"]
                target_field = f"MSRP {currency}"
                if target_field in TARGET_FIELDS and target_field not in results:
                    results[target_field] = (orig_header, 0.9)
            else:
                # No currency detected, use generic MSRP
                if "MSRP" not in results:
                    results["MSRP"] = (orig_header, 0.8)
    
    def _apply_content_based_detection(
        self, 
        headers: List[str],
        sample_data: List[List[Any]],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Apply content-based detection by analyzing column values.
        
        Args:
            headers: List of original header strings
            sample_data: Sample data rows for content-based analysis
            results: Dictionary to store results
        """
        logger.debug("Applying content-based detection")
        
        # Skip if no data to analyze
        if not sample_data or len(sample_data) == 0:
            return
            
        # Transpose data to get columns
        columns = []
        for i in range(len(headers)):
            column = []
            for row in sample_data:
                if i < len(row):
                    column.append(row[i])
                else:
                    column.append(None)
            columns.append(column)
        
        # Fields to check with content-based detection
        fields_to_check = [
            field for field in TARGET_FIELDS 
            if field not in results and field in FIELD_VALUE_FORMATS
        ]
        
        for i, (header, column) in enumerate(zip(headers, columns)):
            # Skip headers already mapped to fields
            if header in [v[0] for v in results.values()]:
                continue
                
            # Check for price fields with currency
            if self._is_price_column(column):
                currency = self._detect_currency_from_values(column)
                if currency:
                    target_field = f"MSRP {currency}"
                    if target_field in TARGET_FIELDS and target_field not in results:
                        results[target_field] = (header, 0.85)
                else:
                    if "MSRP" not in results:
                        results["MSRP"] = (header, 0.75)
            
            # Check for other field formats
            for field in fields_to_check:
                if self._matches_field_format(column, field):
                    results[field] = (header, 0.8)
                    break
    
    def _is_price_column(self, column: List[Any]) -> bool:
        """
        Check if a column contains price values.
        
        Args:
            column: List of column values
            
        Returns:
            True if column likely contains price values
        """
        # Count values that look like prices
        price_pattern = r'(?:^|[^\d])(?:[\£\$\€])?\s*[\d,]+(?:\.\d{2})?(?!\d)'
        num_prices = 0
        num_values = 0
        
        for value in column:
            if value is not None and value != "":
                num_values += 1
                if isinstance(value, (int, float)) or (isinstance(value, str) and re.search(price_pattern, value)):
                    num_prices += 1
        
        # If more than 70% of values look like prices, this is likely a price column
        return num_values > 0 and num_prices / num_values > 0.7
    
    def _detect_currency_from_values(self, column: List[Any]) -> Optional[str]:
        """
        Detect currency from column values.
        
        Args:
            column: List of column values
            
        Returns:
            Currency code or None
        """
        currency_counts = {currency: 0 for currency in CURRENCY_INDICATORS.keys()}
        
        for value in column:
            if not isinstance(value, str):
                continue
                
            for currency, patterns in CURRENCY_VALUE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        currency_counts[currency] += 1
                        break
        
        # Return most common currency if it appears at least 3 times
        most_common = max(currency_counts.items(), key=lambda x: x[1])
        if most_common[1] >= 3:
            return most_common[0]
        
        return None
    
    def _matches_field_format(self, column: List[Any], field: str) -> bool:
        """
        Check if column values match the expected format for a field.
        
        Args:
            column: List of column values
            field: Target field to check
            
        Returns:
            True if column likely matches field format
        """
        patterns = FIELD_VALUE_FORMATS.get(field, [])
        if not patterns:
            return False
            
        # Count values that match the field format
        num_matches = 0
        num_values = 0
        
        for value in column:
            if value is not None and value != "":
                num_values += 1
                if any(re.match(pattern, str(value), re.IGNORECASE) for pattern in patterns):
                    num_matches += 1
        
        # If more than 70% of values match the format, this is likely the correct field
        return num_values > 0 and num_matches / num_values > 0.7
    
    def _apply_contextual_detection(
        self, 
        headers: List[str],
        cleaned_headers: List[str],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Apply contextual field detection based on field relationships.
        
        Args:
            headers: List of original header strings
            cleaned_headers: List of cleaned header strings
            results: Dictionary to store results
        """
        logger.debug("Applying contextual field detection")
        
        # Apply field relationships to find related fields
        for field, related_fields in FIELD_RELATIONSHIPS.items():
            if field in results:
                field_index = headers.index(results[field][0])
                
                # Check adjacent columns
                for offset in range(-2, 3):
                    nearby_index = field_index + offset
                    
                    if nearby_index == field_index or nearby_index < 0 or nearby_index >= len(headers):
                        continue
                    
                    nearby_header = headers[nearby_index]
                    nearby_cleaned = cleaned_headers[nearby_index]
                    
                    # Skip if already mapped
                    if nearby_header in [v[0] for v in results.values()]:
                        continue
                    
                    # Check if this nearby header could be one of the related fields
                    for related_field in related_fields:
                        if related_field in results:
                            continue
                            
                        # Check if header contains keywords related to this field
                        keywords = related_field.lower().split()
                        keyword_matches = sum(1 for kw in keywords if kw in nearby_cleaned)
                        
                        if keyword_matches > 0:
                            # Found a potential match
                            confidence = 0.6 + (0.1 * keyword_matches)
                            results[related_field] = (nearby_header, min(confidence, 0.85))
        
        # Special case for price fields
        self._infer_price_fields(headers, cleaned_headers, results)
    
    def _infer_price_fields(
        self,
        headers: List[str],
        cleaned_headers: List[str],
        results: Dict[str, Tuple[str, float]]
    ) -> None:
        """
        Infer price field relationships based on context.
        
        Args:
            headers: List of original header strings
            cleaned_headers: List of cleaned header strings
            results: Dictionary to store results
        """
        # Check if we have an MSRP field but missing Buy Cost
        if any(field in results for field in ["MSRP", "MSRP GBP", "MSRP USD", "MSRP EUR"]) and "Buy Cost" not in results:
            # Find MSRP column index
            msrp_field = next(field for field in ["MSRP", "MSRP GBP", "MSRP USD", "MSRP EUR"] if field in results)
            msrp_index = headers.index(results[msrp_field][0])
            
            # Look for nearby columns that might be Buy Cost
            for offset in range(-3, 4):
                if offset == 0:
                    continue
                    
                cost_index = msrp_index + offset
                if cost_index < 0 or cost_index >= len(headers):
                    continue
                    
                cost_header = headers[cost_index]
                cost_cleaned = cleaned_headers[cost_index]
                
                # Skip if already mapped
                if cost_header in [v[0] for v in results.values()]:
                    continue
                
                # Simple heuristic: if it contains "cost" or similar terms
                cost_terms = ["cost", "buy", "wholesale", "net", "dealer"]
                for term in cost_terms:
                    if term in cost_cleaned and "retail" not in cost_cleaned and "list" not in cost_cleaned:
                        results["Buy Cost"] = (cost_header, 0.7)
                        break
    
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
            
            # Get target keywords and their synonyms
            target_keywords = target_field.lower().split()
            expanded_keywords = self._expand_with_synonyms(target_keywords)
            
            for i, cleaned_header in enumerate(cleaned_headers):
                # Skip headers already mapped to other fields with high confidence
                if original_headers[i] in [v[0] for k, v in results.items() if v[1] > 0.85]:
                    continue
                    
                # Calculate string similarity
                similarity = self._calculate_similarity(target_field, cleaned_header)
                
                # Calculate ngram similarity
                ngram_sim = self._calculate_ngram_similarity(target_field, cleaned_header)
                
                # Check keyword presence with synonyms
                header_words = cleaned_header.split()
                keyword_score = 0
                
                for keyword in expanded_keywords:
                    if keyword in header_words:
                        keyword_score += 0.15  # Boost for each keyword found
                    elif keyword in cleaned_header:
                        keyword_score += 0.1   # Smaller boost for partial match
                
                # Combined score (max 1.0)
                combined_score = min(max(similarity, ngram_sim) + keyword_score, 1.0)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = (original_headers[i], combined_score)
            
            # Only accept match if score is above threshold
            if best_match and best_score >= self.confidence_threshold:
                results[target_field] = best_match
    
    def _expand_with_synonyms(self, keywords: List[str]) -> Set[str]:
        """
        Expand keywords with their synonyms.
        
        Args:
            keywords: List of keywords to expand
            
        Returns:
            Set of expanded keywords including synonyms
        """
        expanded = set(keywords)
        
        for keyword in keywords:
            if keyword in HEADER_SYNONYMS:
                for synonym in HEADER_SYNONYMS[keyword]:
                    expanded.add(synonym)
        
        return expanded
    
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
    
    def _calculate_ngram_similarity(self, str1: str, str2: str, n: int = 3) -> float:
        """
        Calculate similarity using character n-grams.
        
        Args:
            str1: First string
            str2: Second string
            n: N-gram size
            
        Returns:
            Jaccard similarity score (0.0 to 1.0)
        """
        # Handle short strings
        if len(str1) < n or len(str2) < n:
            return self._calculate_similarity(str1, str2)
        
        # Generate n-grams
        str1 = str1.lower().replace(" ", "")
        str2 = str2.lower().replace(" ", "")
        
        ngrams1 = set([str1[i:i+n] for i in range(len(str1) - n + 1)])
        ngrams2 = set([str2[i:i+n] for i in range(len(str2) - n + 1)])
        
        # Calculate Jaccard similarity
        if not ngrams1 or not ngrams2:
            return 0.0
            
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        
        return len(intersection) / len(union)