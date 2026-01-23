# Car Lease Review AI Assistant - Fairness Score Engine

A comprehensive system for extracting and analyzing car lease contract facts to evaluate fairness.

## Features

- **PDF Text Extraction**: Extract SLA parameters from car lease PDFs using advanced text processing
- **Data Validation**: Robust validation using Pydantic models and JSON schemas
- **Database Storage**: SQLite-based storage for contract facts
- **REST API**: FastAPI-based web service for PDF uploads and data retrieval
- **Modular Architecture**: Clean separation of concerns with dedicated modules

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/v1/extract
Upload a PDF and extract contract facts.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file)

**Response:**
```json
{
  "record_id": 1,
  "extracted_data": {
    "apr": 5.99,
    "monthly_payment": 450.00,
    "lease_term_months": 36,
    ...
  },
  "status": "success",
  "message": "PDF processed successfully"
}
```

### GET /api/v1/contracts
Retrieve all stored contract facts.

**Response:**
```json
[
  {
    "id": 1,
    "apr": 5.99,
    "monthly_payment": 450.00,
    ...
  }
]
```

### GET /api/v1/contracts/{record_id}
Retrieve a specific contract by ID.

## PDF Processing

The system extracts the following SLA parameters from uploaded PDFs:

- Interest rate / APR
- Lease term duration
- Monthly payment
- Down payment
- Residual value
- Mileage allowance & overage charges
- Early termination clause
- Purchase option (buyout price)
- Maintenance responsibilities
- Warranty and insurance coverage
- Penalties or late fee clauses

## PDF Storage

By default, uploaded PDFs are saved in the `uploads/` directory for audit and compliance purposes. This can be disabled by setting `SAVE_ORIGINAL_PDFS = False` in `api/routes.py`.

## Architecture

- `api/`: FastAPI routes and schemas
- `engine/`: PDF extraction logic
- `models/`: Pydantic data models
- `database/`: SQLite database operations
- `pipelines/`: Orchestration of extraction process
- `schemas/`: JSON schemas for validation
- `scripts/`: Utility scripts

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Running Extraction Script
```bash
python scripts/run_extraction.py path/to/lease.pdf
```

### API Documentation
When the server is running, visit `http://localhost:8000/docs` for interactive API documentation.
