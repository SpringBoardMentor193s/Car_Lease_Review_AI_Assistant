# Backend - File Upload & AI Analysis API

Flask-based REST API for file upload and processing with Ollama.

## Quick Start

1. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure Ollama is running:
   ```bash
   ollama serve
   ollama pull llama3.2
   ```

### OCR Prerequisites (Tesseract)

This project uses `pytesseract` and `PyMuPDF` to perform OCR on PDFs and images. You must install the Tesseract OCR engine separately.

- Windows: Download and install from https://github.com/tesseract-ocr/tesseract/releases. Add the Tesseract `tesseract.exe` path to your `PATH` environment variable (e.g., `C:\Program Files\Tesseract-OCR`).
- macOS (Homebrew): `brew install tesseract`
- Linux (Debian/Ubuntu): `sudo apt-get install tesseract-ocr`

If Tesseract is not in your PATH, set the path in Python before using OCR, for example:

```py
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

When Tesseract is installed, the backend will automatically try to extract text from PDFs (embedded text first, then OCR) and images.

4. Run the server:
   ```bash
   python app.py
   ```

Server will start on `http://localhost:3000`

## API Endpoints

- `POST /upload` - Upload and process file
- `GET /files` - List all processed files
- `GET /files/<id>` - Get file details
- `GET /health` - Check service health

## Configuration

Modify these variables in `app.py`:
- `UPLOAD_FOLDER`: Where uploaded files are stored
- `PROCESSED_FOLDER`: Where processed data is stored
- `ALLOWED_EXTENSIONS`: Supported file types
- `MAX_CONTENT_LENGTH`: Maximum file size
- Ollama model in `process_with_ollama()` function
