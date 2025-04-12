# PowerShell script to set up the Catalog Parser project structure

# Create virtual environment and activate it
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv .venv
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Green
$directories = @(
    "config",
    "parsers",
    "utils",
    "logs",
    "temp",
    "output",
    "resources",
    "tests"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "Created directory: $dir" -ForegroundColor Cyan
}

# Create config files
Write-Host "Creating config files..." -ForegroundColor Green
$configFiles = @(
    "config\__init__.py",
    "config\field_mappings.py",
    "config\settings.py",
    "config\target_fields.py"
)

foreach ($file in $configFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "Created file: $file" -ForegroundColor Cyan
}

# Create parser files
Write-Host "Creating parser files..." -ForegroundColor Green
$parserFiles = @(
    "parsers\__init__.py",
    "parsers\base_parser.py",
    "parsers\csv_parser.py",
    "parsers\excel_parser.py",
    "parsers\numbers_parser.py",
    "parsers\pdf_parser.py",
    "parsers\text_parser.py"
)

foreach ($file in $parserFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "Created file: $file" -ForegroundColor Cyan
}

# Create utility files
Write-Host "Creating utility files..." -ForegroundColor Green
$utilFiles = @(
    "utils\__init__.py",
    "utils\column_mapper.py",
    "utils\error_handler.py",
    "utils\file_detector.py",
    "utils\manufacturer_detector.py",
    "utils\price_utils.py"
)

foreach ($file in $utilFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "Created file: $file" -ForegroundColor Cyan
}

# Create main files
Write-Host "Creating main files..." -ForegroundColor Green
$mainFiles = @(
    "__init__.py",
    "catalog_parser.py",
    "web_app.py",
    "build_macos_app.py",
    "setup.py",
    "requirements.txt",
    "Dockerfile",
    "render.yaml",
    "README.md",
    ".gitignore"
)

foreach ($file in $mainFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "Created file: $file" -ForegroundColor Cyan
}

# Create test files
Write-Host "Creating test files..." -ForegroundColor Green
$testFiles = @(
    "tests\__init__.py",
    "tests\test_csv_parser.py",
    "tests\test_excel_parser.py",
    "tests\test_field_mapping.py"
)

foreach ($file in $testFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "Created file: $file" -ForegroundColor Cyan
}

# Create __init__.py files for package structure
Write-Host "Creating __init__.py files for package structure..." -ForegroundColor Green
New-Item -ItemType File -Path "tests\__init__.py" -Force | Out-Null

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Green
pip install -U pip
pip install openpyxl xlrd chardet python-magic pdfplumber tabula-py flask waitress gunicorn

# Save installed packages to requirements.txt
Write-Host "Generating requirements.txt..." -ForegroundColor Green
pip freeze > requirements.txt

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Project structure has been created." -ForegroundColor Green
Write-Host "Virtual environment is activated. Use 'deactivate' to exit." -ForegroundColor Yellow