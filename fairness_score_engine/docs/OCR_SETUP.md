# OCR Setup Guide for Scanned PDF Support

This guide explains how to set up OCR (Optical Character Recognition) for extracting text from scanned or image-based PDFs.

## Prerequisites

The PDF extractor now supports two extraction methods:
1. **pdfplumber** - For digitally-created PDFs (default, no extra setup needed)
2. **Tesseract OCR** - For scanned/image-based PDFs (requires installation)

## Installation

### 1. Install Python Dependencies

```bash
pip install pytesseract pdf2image Pillow
```

### 2. Install Tesseract OCR

#### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR\`)
3. Note the installation path for configuration

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### macOS
```bash
brew install tesseract
```

### 3. Install Poppler (required by pdf2image)

#### Windows
1. Download from: https://github.com/osber/poppler-windows/releases
2. Extract to a folder (e.g., `C:\poppler`)
3. Add `C:\poppler\bin` to your system PATH

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install poppler-utils
```

#### macOS
```bash
brew install poppler
```

## Usage

### Basic Usage (Auto-detection)
The extractor automatically falls back to OCR if pdfplumber doesn't find meaningful text:

```python
from engine.pdf_extractor import PDFExtractor

# Without specifying tesseract path (works on Linux/macOS if in PATH)
extractor = PDFExtractor()
data = extractor.extract_from_pdf("lease_agreement.pdf")

# With tesseract path (required on Windows)
extractor = PDFExtractor(tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
data = extractor.extract_from_pdf("scanned_lease.pdf")
```

### Force OCR Mode
To force OCR extraction (useful for testing or when auto-detection fails):

```python
data = extractor.extract_from_pdf("document.pdf", use_ocr=True)
```

### Using with ExtractPipeline

```python
from pipelines.extract_pipeline import ExtractPipeline

# Initialize with tesseract path
pipeline = ExtractPipeline(
    db_path="contract_facts.db",
    tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
)

# Run extraction (auto-detects if OCR is needed)
record_id = pipeline.run("scanned_lease.pdf")

# Force OCR mode
record_id = pipeline.run("scanned_lease.pdf", use_ocr=True)
```

## Troubleshooting

### "tesseract is not installed or it's not in your PATH"
- **Windows**: Specify the full path to tesseract.exe in the constructor
- **Linux/macOS**: Ensure tesseract is installed and in your PATH

### "Unable to get page count. Is poppler installed?"
- Install poppler and ensure it's in your PATH (see installation steps above)

### Poor OCR Quality
- Ensure the scanned PDF has good resolution (300 DPI recommended)
- The extractor automatically converts images to grayscale for better accuracy
- For very poor quality scans, consider pre-processing the PDF

## How It Works

1. **Auto-detection**: First attempts extraction with pdfplumber
2. **Fallback**: If less than 10 words are found, automatically switches to OCR
3. **OCR Process**:
   - Converts PDF pages to images at 300 DPI
   - Preprocesses images (grayscale conversion)
   - Runs Tesseract with LSTM engine for best accuracy
4. **Field Extraction**: Regex patterns extract SLA parameters from the text
