#!/usr/bin/env python3
"""
Setup script for the Catalog Parser package.
"""

from setuptools import setup, find_packages

setup(
    name="catalog_parser",
    version="1.0.0",
    description="A tool for parsing and standardizing product catalogs from various formats",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openpyxl>=3.0.0",      # Excel files (.xlsx)
        "xlrd>=2.0.0",          # Excel files (.xls)
        "chardet>=4.0.0",       # Character encoding detection
        "python-magic>=0.4.0",  # File type detection
        "pdfplumber>=0.7.0",    # PDF text extraction
        "tabula-py>=2.3.0",     # PDF table extraction
        "flask>=2.0.0",         # Web application
        "waitress>=2.1.0",      # Production WSGI server
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "catalog-parser=catalog_parser:main",
            "catalog-parser-web=web_app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)