# Car Lease Review AI Assistant - Fairness Score Engine

A comprehensive system for extracting and analyzing car lease contract facts to evaluate fairness.

## Features

- **PDF Text Extraction**: Extract SLA parameters from car lease PDFs using advanced text processing
- **Data Validation**: Robust validation using Pydantic models and JSON schemas
- **Database Storage**: SQLite-based storage for contract facts
- **REST API**: FastAPI-based web service for PDF uploads and data retrieval
- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Online Dynamic Pricing (Optional)**: Live buyout benchmark support via external market API

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

## Online Pricing Configuration (No Hardcoded Region Multipliers)

Set these environment variables to enable live, location-specific buyout benchmarking:

```bash
MARKET_PRICE_API_URL=https://your-pricing-service.example.com/benchmark
MARKET_PRICE_API_KEY=your_key_if_required
MARKET_PRICE_API_KEY_HEADER=x-api-key
MARKET_PRICE_TIMEOUT_SEC=8
```

Expected API response formats:

1. Direct stats:
```json
{ "mean": 17200, "std": 2800, "min": 12000, "max": 22500 }
```

2. Price list/listings:
```json
{ "prices": [16500, 17250, 18100, 16900] }
```
or
```json
{ "listings": [{ "price": 16500 }, { "price": 17250 }] }
```

If online pricing is unavailable, the engine automatically falls back to contract-economics-based dynamic estimation.

### MarketCheck Provider Setup

If you want to use MarketCheck directly (without your own aggregator service), set:

```bash
MARKET_PRICING_PROVIDER=marketcheck
MARKET_PRICE_API_KEY=your_marketcheck_api_key
MARKET_PRICE_API_SECRET=your_marketcheck_api_secret
MARKETCHECK_USE_OAUTH=true
MARKETCHECK_SEARCH_URL=https://api.marketcheck.com/v2/search/car/active
MARKETCHECK_OAUTH_URL=https://api.marketcheck.com/oauth2/token
```

Notes:
- If OAuth token fetch fails, the client falls back to `api_key` query auth.
- Best results require `vin` or (`vehicle_year` + `vehicle_make` + `vehicle_model`) plus location (`lessee_city`+`lessee_state` or `lessee_zip`).
