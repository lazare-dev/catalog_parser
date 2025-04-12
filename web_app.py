#!/usr/bin/env python3
"""
Web application interface for the catalog parser.
Can be run locally or hosted on Render.
"""

import os
import tempfile
import json
import uuid
import shutil
from typing import Dict, Any, List, Optional

from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename

from catalog_parser import CatalogParser
from utils.error_handler import init_logging
from config.settings import WEB_HOST, WEB_PORT, MAX_UPLOAD_SIZE, TEMP_DIR, OUTPUT_DIR

# Create Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE
app.config['UPLOAD_FOLDER'] = TEMP_DIR
app.config['OUTPUT_FOLDER'] = OUTPUT_DIR

# Create necessary directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)

# Initialize catalog parser
parser = CatalogParser(debug=True)

# Setup logging
init_logging()


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file part in the request.'
        })
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected.'
        })
    
    # Get form parameters
    sheet_name = request.form.get('sheet_name', None)
    sheet_index = int(request.form.get('sheet_index', 0))
    output_format = request.form.get('output_format', 'csv')
    
    try:
        # Create a unique directory for this upload
        upload_id = str(uuid.uuid4())
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Create output path
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], upload_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, os.path.splitext(filename)[0] + f'.{output_format}')
        
        # Parse the file
        result = parser.parse_file(
            filepath, 
            output_file if output_format == 'csv' else None,
            sheet_name=sheet_name, 
            sheet_index=sheet_index
        )
        
        # If JSON format requested, save as JSON
        if output_format == 'json' and result['success']:
            parser.save_to_json(result['parsed_data'], output_file)
        
        # Add download URL to result
        if result['success']:
            result['download_url'] = url_for('download_file', upload_id=upload_id, 
                                            filename=os.path.basename(output_file))
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/download/<upload_id>/<filename>')
def download_file(upload_id, filename):
    """Download the parsed file."""
    return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], upload_id), 
                               filename, as_attachment=True)


@app.route('/api/parse', methods=['POST'])
def api_parse():
    """API endpoint for parsing files."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file part in the request.'
        })
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected.'
        })
    
    # Get parameters
    sheet_name = request.form.get('sheet_name', None)
    sheet_index = int(request.form.get('sheet_index', 0))
    include_data = request.form.get('include_data', 'true').lower() == 'true'
    
    try:
        # Save the uploaded file to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
        temp_file.close()
        
        # Parse the file
        result = parser.parse_file(
            temp_file.name,
            None,  # Don't save output
            sheet_name=sheet_name,
            sheet_index=sheet_index
        )
        
        # Remove data if not requested to reduce response size
        if not include_data and 'parsed_data' in result:
            del result['parsed_data']
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# Create HTML templates
def create_templates():
    """Create necessary HTML templates for the web interface."""
    templates_dir = os.path.join(app.root_path, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create index.html
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catalog Parser</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .upload-form {
            max-width: 600px;
            margin: 0 auto;
        }
        .results {
            margin-top: 2rem;
            display: none;
        }
        .loader {
            display: none;
            text-align: center;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Catalog Parser</h1>
        <div class="upload-form">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Upload Catalog File</h5>
                </div>
                <div class="card-body">
                    <form id="upload-form">
                        <div class="mb-3">
                            <label for="file" class="form-label">Select File</label>
                            <input type="file" class="form-control" id="file" name="file" required>
                            <div class="form-text">Supported formats: Excel, CSV, Text, PDF, Numbers</div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="sheet_name" class="form-label">Sheet Name (Excel/Numbers)</label>
                            <input type="text" class="form-control" id="sheet_name" name="sheet_name" placeholder="Optional">
                        </div>
                        
                        <div class="mb-3">
                            <label for="sheet_index" class="form-label">Sheet Index (Excel/Numbers)</label>
                            <input type="number" class="form-control" id="sheet_index" name="sheet_index" value="0" min="0">
                            <div class="form-text">First sheet is 0</div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Output Format</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="output_format" id="output_csv" value="csv" checked>
                                <label class="form-check-label" for="output_csv">CSV</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="output_format" id="output_json" value="json">
                                <label class="form-check-label" for="output_json">JSON</label>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100">Parse Catalog</button>
                    </form>
                    
                    <div class="loader">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p>Parsing file, please wait...</p>
                    </div>
                </div>
            </div>
            
            <div class="results card mt-4">
                <div class="card-header">
                    <h5 class="card-title mb-0">Parsing Results</h5>
                </div>
                <div class="card-body">
                    <div id="success-result">
                        <div class="alert alert-success">
                            <h4 class="alert-heading">Success!</h4>
                            <p>File parsed successfully.</p>
                        </div>
                        
                        <div class="mb-3">
                            <strong>Records Parsed:</strong> <span id="record-count">0</span>
                        </div>
                        
                        <div class="mb-3">
                            <strong>File Type:</strong> <span id="file-type"></span>
                        </div>
                        
                        <div class="mb-3">
                            <strong>Headers:</strong> 
                            <div id="headers" class="border p-2 mt-1" style="max-height: 100px; overflow-y: auto;"></div>
                        </div>
                        
                        <div class="mb-3">
                            <a id="download-link" href="#" class="btn btn-success w-100">Download Result</a>
                        </div>
                    </div>
                    
                    <div id="error-result">
                        <div class="alert alert-danger">
                            <h4 class="alert-heading">Error</h4>
                            <p id="error-message"></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('upload-form');
            const loader = document.querySelector('.loader');
            const results = document.querySelector('.results');
            const successResult = document.getElementById('success-result');
            const errorResult = document.getElementById('error-result');
            
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Show loader
                form.style.display = 'none';
                loader.style.display = 'block';
                results.style.display = 'none';
                
                // Get form data
                const formData = new FormData(form);
                
                // Send request
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loader
                    loader.style.display = 'none';
                    results.style.display = 'block';
                    
                    if (data.success) {
                        // Show success result
                        successResult.style.display = 'block';
                        errorResult.style.display = 'none';
                        
                        // Fill in details
                        document.getElementById('record-count').textContent = data.record_count;
                        document.getElementById('file-type').textContent = data.file_type;
                        
                        // Set headers
                        const headersContainer = document.getElementById('headers');
                        headersContainer.innerHTML = '';
                        if (data.headers && data.headers.length > 0) {
                            const headersList = document.createElement('ul');
                            headersList.className = 'list-unstyled mb-0';
                            data.headers.forEach(header => {
                                const item = document.createElement('li');
                                item.textContent = header;
                                headersList.appendChild(item);
                            });
                            headersContainer.appendChild(headersList);
                        } else {
                            headersContainer.textContent = 'No headers found';
                        }
                        
                        // Set download link
                        const downloadLink = document.getElementById('download-link');
                        downloadLink.href = data.download_url;
                    } else {
                        // Show error result
                        successResult.style.display = 'none';
                        errorResult.style.display = 'block';
                        
                        // Set error message
                        document.getElementById('error-message').textContent = data.error || 'Unknown error occurred';
                    }
                    
                    // Show form again
                    form.style.display = 'block';
                })
                .catch(error => {
                    // Hide loader
                    loader.style.display = 'none';
                    results.style.display = 'block';
                    
                    // Show error result
                    successResult.style.display = 'none';
                    errorResult.style.display = 'block';
                    
                    // Set error message
                    document.getElementById('error-message').textContent = 'Network error: ' + error.message;
                    
                    // Show form again
                    form.style.display = 'block';
                });
            });
        });
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")


# Create templates when module is loaded
create_templates()


def main():
    """Run the web application."""
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)


if __name__ == "__main__":
    main()