#!/usr/bin/env python3
"""
Configuration file defining the target fields for the standardized output.
This file can be easily updated to add, remove, or modify target fields.
"""

# Standard target fields that all catalogs will be mapped to
TARGET_FIELDS = [
    "SKU",
    "Short Description",
    "Long Description",
    "Model",
    "Category Group",
    "Category",
    "Manufacturer",
    "Manufacturer SKU",
    "Image URL",
    "Document Name",
    "Document URL",
    "Unit Of Measure",
    "Buy Cost",
    "Trade Price",
    "MSRP GBP",
    "MSRP USD",
    "MSRP EUR",
    "Discontinued"
]

# Field groups for special handling
PRICE_FIELDS = [
    "Buy Cost",
    "Trade Price",
    "MSRP GBP",
    "MSRP USD",
    "MSRP EUR"
]

REQUIRED_FIELDS = [
    "SKU",
    "Short Description",
    "Manufacturer"
]

# Default values for fields
DEFAULT_VALUES = {
    "Discontinued": False,
    "Long Description": ""
}