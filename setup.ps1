# Setup Script for Car Lease Review AI Assistant
# This script helps configure your environment for SLA extraction

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Car Lease Review AI Assistant - Setup" -ForegroundColor Cyan
Write-Host "SLA Extraction & Vehicle Data Integration" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.8+ from https://www.python.org" -ForegroundColor Red
    exit 1
}

# Check pip
Write-Host "`nChecking pip..." -ForegroundColor Yellow
$pipVersion = pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pip found: $pipVersion" -ForegroundColor Green
} else {
    Write-Host "✗ pip not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check for Groq API key
Write-Host "`nChecking Groq API configuration..." -ForegroundColor Yellow
$apiKey = $env:GROQ_API_KEY
if ($apiKey) {
    Write-Host "✓ GROQ_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "⚠ GROQ_API_KEY is not set" -ForegroundColor Yellow
    Write-Host "`nTo use LLM-based SLA extraction, you need a Groq API key:" -ForegroundColor White
    Write-Host "1. Visit https://console.groq.com/keys" -ForegroundColor White
    Write-Host "2. Create a new API key (free tier available)" -ForegroundColor White
    Write-Host "3. Set it in PowerShell:" -ForegroundColor White
    Write-Host '   $env:GROQ_API_KEY = "gsk_your-api-key-here"' -ForegroundColor Cyan
    Write-Host "`nOr add to your PowerShell profile for permanent setup:" -ForegroundColor White
    Write-Host '   notepad $PROFILE' -ForegroundColor Cyan
    Write-Host '   # Add: $env:GROQ_API_KEY = "gsk_your-api-key-here"' -ForegroundColor Cyan
    
    $response = Read-Host "`nDo you want to set it now? (y/n)"
    if ($response -eq 'y') {
        $apiKeyInput = Read-Host "Enter your Groq API key"
        if ($apiKeyInput) {
            $env:GROQ_API_KEY = $apiKeyInput
            Write-Host "✓ API key set for this session" -ForegroundColor Green
            Write-Host "  (Note: This is temporary. Add to profile for permanent setup)" -ForegroundColor Gray
        }
    }
}

# Check database configuration
Write-Host "`nChecking database configuration..." -ForegroundColor Yellow
$dbUrl = $env:DATABASE_URL
if ($dbUrl) {
    Write-Host "✓ DATABASE_URL is set" -ForegroundColor Green
} else {
    Write-Host "⚠ DATABASE_URL not set - will use default PostgreSQL connection" -ForegroundColor Yellow
    Write-Host "  Default: postgresql+asyncpg://postgres:password@localhost:5432/car_lease_db" -ForegroundColor Gray
}

# Check Tesseract OCR
Write-Host "`nChecking Tesseract OCR..." -ForegroundColor Yellow
$tesseractPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)
$tesseractFound = $false
foreach ($path in $tesseractPaths) {
    if (Test-Path $path) {
        Write-Host "✓ Tesseract found at: $path" -ForegroundColor Green
        $tesseractFound = $true
        break
    }
}
if (-not $tesseractFound) {
    Write-Host "⚠ Tesseract not found" -ForegroundColor Yellow
    Write-Host "  For PDF/image OCR, install from:" -ForegroundColor White
    Write-Host "  https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
}

# Check Poppler (for PDF processing)
Write-Host "`nChecking Poppler (PDF processing)..." -ForegroundColor Yellow
$popplerPaths = @(
    "C:\poppler\poppler-24.08.0\Library\bin",
    "C:\Program Files\poppler-24.08.0\Library\bin"
)
$popplerFound = $false
foreach ($path in $popplerPaths) {
    if (Test-Path $path) {
        Write-Host "✓ Poppler found at: $path" -ForegroundColor Green
        $popplerFound = $true
        break
    }
}
if (-not $popplerFound) {
    Write-Host "⚠ Poppler not found" -ForegroundColor Yellow
    Write-Host "  For PDF processing, install from:" -ForegroundColor White
    Write-Host "  https://github.com/oschwartz10612/poppler-windows/releases" -ForegroundColor Cyan
}

# Create necessary directories
Write-Host "`nCreating necessary directories..." -ForegroundColor Yellow
$dirs = @(
    "backend\uploads\contracts",
    "backend\vehicle_data",
    "logs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Already exists: $dir" -ForegroundColor Gray
    }
}

# Final summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Start the backend server:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Cyan
Write-Host "   uvicorn main:app --reload" -ForegroundColor Cyan

Write-Host "`n2. Run the test suite:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Cyan
Write-Host "   python test_end_to_end.py" -ForegroundColor Cyan

Write-Host "`n3. Access API documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`n4. Read the guides:" -ForegroundColor White
Write-Host "   - QUICKSTART_SLA.md (5-minute quick start)" -ForegroundColor Gray
Write-Host "   - SLA_EXTRACTION_GUIDE.md (complete documentation)" -ForegroundColor Gray
Write-Host "   - WEEK3_4_SUMMARY.md (implementation summary)" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup complete! Ready to extract SLAs." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
