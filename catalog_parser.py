#!/usr/bin/env python3
"""
Main catalog parser module that orchestrates the parsing process.
"""

import os
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional, Union
import json

from parsers.base_parser import BaseParser
from utils.file_detector import FileDetector
from utils.error_handler import init_logging, handle_exception, ParserError
from config.settings import (
    CSV_DELIMITER, CSV_QUOTECHAR, CSV_ENCODING, 
    LOG_FILE, LOG_LEVEL, OUTPUT_DIR
)
from config.target_fields import TARGET_FIELDS

logger = logging.getLogger(__name__)

class CatalogParser:
    """
    Main parser class that coordinates the parsing process.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the catalog parser.
        
        Args:
            debug: Enable debug logging
        """
        # Set up logging
        log_level = logging.DEBUG if debug else LOG_LEVEL
        init_logging(LOG_FILE, console=True, level=log_level)
        
        logger.info("Initializing Catalog Parser")
    
    def parse_file(self, filename: str, output_file: Optional[str] = None, 
                   sheet_name: Optional[str] = None, sheet_index: int = 0) -> Dict[str, Any]:
        """
        Parse a catalog file and convert to standardized format.
        
        Args:
            filename: Path to the file to parse
            output_file: Path to save the output CSV (optional)
            sheet_name: Sheet name for Excel/Numbers files (optional)
            sheet_index: Sheet index for Excel/Numbers files (optional)
            
        Returns:
            Dictionary with parsing results and metadata
        """
        if not os.path.exists(filename):
            error_msg = f"File not found: {filename}"
            logger.error(error_msg)
            return {"success": False, "error": {"message": error_msg}}
        
        try:
            logger.info(f"Starting to parse: {filename}")
            
            # Get appropriate parser based on file type
            parser_class = FileDetector.get_appropriate_parser(filename)
            
            # Create parser instance with sheet options if applicable
            if parser_class.__name__ in ['ExcelParser', 'NumbersParser']:
                parser = parser_class(filename, sheet_index=sheet_index, sheet_name=sheet_name)
            else:
                parser = parser_class(filename)
            
            # Parse the file
            parsed_data = parser.parse()
            
            logger.info(f"Successfully parsed {len(parsed_data)} records from {filename}")
            
            # Save to output file if requested
            if output_file:
                self.save_to_csv(parsed_data, output_file)
                logger.info(f"Results saved to: {output_file}")
            
            # Return results
            return {
                "success": True,
                "parsed_data": parsed_data,
                "record_count": len(parsed_data),
                "file_type": parser_class.__name__.replace('Parser', ''),
                "headers": list(parsed_data[0].keys()) if parsed_data else []
            }
            
        except Exception as e:
            return handle_exception(e, f"Error parsing file: {filename}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save parsed data to CSV file.
        
        Args:
            data: List of dictionaries with parsed data
            output_file: Path to save the output CSV
        """
        if not data:
            logger.warning("No data to save")
            return
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        try:
            with open(output_file, 'w', newline='', encoding=CSV_ENCODING) as f:
                # Use target fields as column order, adding any extra fields found
                all_fields = list(TARGET_FIELDS)
                
                # Add any extra fields not in TARGET_FIELDS
                for record in data:
                    for field in record.keys():
                        if field not in all_fields:
                            all_fields.append(field)
                
                writer = csv.DictWriter(
                    f, 
                    fieldnames=all_fields,
                    delimiter=CSV_DELIMITER,
                    quotechar=CSV_QUOTECHAR,
                    quoting=csv.QUOTE_MINIMAL
                )
                
                writer.writeheader()
                writer.writerows(data)
                
            logger.info(f"Saved {len(data)} records to {output_file}")
            
        except Exception as e:
            error_msg = f"Error saving to CSV: {str(e)}"
            logger.error(error_msg)
            raise ParserError(error_msg)
    
    def save_to_json(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save parsed data to JSON file.
        
        Args:
            data: List of dictionaries with parsed data
            output_file: Path to save the output JSON
        """
        if not data:
            logger.warning("No data to save")
            return
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(data)} records to {output_file}")
            
        except Exception as e:
            error_msg = f"Error saving to JSON: {str(e)}"
            logger.error(error_msg)
            raise ParserError(error_msg)
    
    def batch_process(self, directory: str, output_dir: Optional[str] = None, 
                      recursive: bool = False) -> Dict[str, Any]:
        """
        Process all supported files in a directory.
        
        Args:
            directory: Directory containing files to process
            output_dir: Directory to save output files (optional)
            recursive: Process subdirectories recursively (optional)
            
        Returns:
            Dictionary with batch processing results
        """
        if not os.path.isdir(directory):
            error_msg = f"Directory not found: {directory}"
            logger.error(error_msg)
            return {"success": False, "error": {"message": error_msg}}
        
        # Set default output directory if not provided
        if not output_dir:
            output_dir = OUTPUT_DIR
        
        # Make sure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "success": True,
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "file_results": []
        }
        
        try:
            # Walk through directory
            for root, _, files in os.walk(directory):
                # Skip if not recursive and not the main directory
                if not recursive and root != directory:
                    continue
                
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Try to detect file type
                    try:
                        file_type = FileDetector.detect_file_type(file_path)
                        results["total_files"] += 1
                        
                        # Create output filename
                        rel_path = os.path.relpath(file_path, directory)
                        output_path = os.path.join(output_dir, rel_path)
                        output_path = os.path.splitext(output_path)[0] + '.csv'
                        
                        # Create output directory if needed
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        # Process file
                        file_result = self.parse_file(file_path, output_path)
                        
                        if file_result["success"]:
                            results["processed_files"] += 1
                        else:
                            results["failed_files"] += 1
                            
                        # Store result
                        results["file_results"].append({
                            "file": file_path,
                            "success": file_result["success"],
                            "output": output_path if file_result["success"] else None,
                            "error": file_result.get("error", None)
                        })
                        
                    except Exception as e:
                        # Could not determine file type, skip
                        results["skipped_files"] += 1
                        logger.info(f"Skipping unsupported file: {file_path}")
                        results["file_results"].append({
                            "file": file_path,
                            "success": False,
                            "skipped": True,
                            "error": {"message": f"Unsupported file type: {str(e)}"}
                        })
            
            return results
            
        except Exception as e:
            error_result = handle_exception(e, f"Error during batch processing of {directory}")
            error_result["total_files"] = results["total_files"]
            error_result["processed_files"] = results["processed_files"]
            error_result["failed_files"] = results["failed_files"]
            error_result["skipped_files"] = results["skipped_files"]
            error_result["file_results"] = results["file_results"]
            return error_result


def main():
    """
    Command-line entry point for the catalog parser.
    """
    parser = argparse.ArgumentParser(description='Catalog Parser Tool')
    
    # File or directory to process
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-f', '--file', help='Path to catalog file to parse')
    input_group.add_argument('-d', '--directory', help='Directory containing catalog files to parse')
    
    # Output options
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('--json', action='store_true', help='Output in JSON format instead of CSV')
    
    # Excel/Numbers options
    parser.add_argument('--sheet-name', help='Sheet name for Excel/Numbers files')
    parser.add_argument('--sheet-index', type=int, default=0, help='Sheet index for Excel/Numbers files')
    
    # Batch processing options
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
    
    # Other options
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Create parser
    catalog_parser = CatalogParser(debug=args.debug)
    
    # Process file or directory
    if args.file:
        # Single file processing
        if args.output:
            output_file = args.output
        else:
            # Default output to same name with .csv extension
            output_file = os.path.splitext(args.file)[0] + ('.json' if args.json else '.csv')
            
        result = catalog_parser.parse_file(
            args.file, 
            output_file if not args.json or args.output else None,
            sheet_name=args.sheet_name,
            sheet_index=args.sheet_index
        )
        
        if result["success"]:
            print(f"Successfully parsed {result['record_count']} records from {args.file}")
            
            # Save as JSON if requested
            if args.json:
                catalog_parser.save_to_json(result["parsed_data"], output_file)
                print(f"Saved results to {output_file}")
        else:
            print(f"Error parsing {args.file}: {result['error']['message']}")
            return 1
    else:
        # Directory processing
        result = catalog_parser.batch_process(
            args.directory,
            args.output,
            recursive=args.recursive
        )
        
        if result["success"]:
            print(f"Batch processing summary:")
            print(f"  Total files:     {result['total_files']}")
            print(f"  Processed files: {result['processed_files']}")
            print(f"  Failed files:    {result['failed_files']}")
            print(f"  Skipped files:   {result['skipped_files']}")
        else:
            print(f"Error during batch processing: {result['error']['message']}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())