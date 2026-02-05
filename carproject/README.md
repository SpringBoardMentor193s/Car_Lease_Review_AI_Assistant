# Car Project OCR + Web Demo

This project provides a document OCR service (images + PDFs) that runs entirely within your Python virtual environment, and a simple Flask webpage to upload a file and view extracted text.

## Setup

1. Activate your venv (already activated as per your terminal):

```powershell
venv\scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables (create a local .env, do not commit it):

```powershell
copy .env.example .env
```

## Run the web app

Use module mode so package imports work:

```powershell
python -m app.main
```

Then open http://127.0.0.1:5000 in your browser.

## Features

- OCR images or PDFs via EasyOCR and pypdfium2.
- Automatically saves extracted text to data/ocr as timestamped .txt files.
- Runs SLA field extraction (APR, lease term, payments, mileage, etc.) and displays clause snippets.
- Detects VINs in text, decodes details via NHTSA vPIC, and renders a VIN details table.
- Negotiation assistant that uses OpenRouter (free models) with SLA + VIN JSON payloads.
- Toggle panels for OCR and SLA results to keep the view clean.
- Debug mode: paste text or upload a .txt file to run SLA extraction without performing OCR.

## Notes
- OCR uses EasyOCR (no external executables needed).
- PDFs are rendered to images using pypdfium2 before OCR.
- Set OPENROUTER_API_KEY to enable the negotiation assistant. Optional: OPENROUTER_MODEL, OPENROUTER_SITE_URL, OPENROUTER_APP_NAME.
- OPENROUTER_MODEL must be a free model (suffix :free).
- Uploaded files are saved under app/uploads.
