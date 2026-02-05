# SLA Extraction & Vehicle Data Integration Guide

## Overview

This system provides **automated SLA (Service Level Agreement) extraction** from car lease contracts using **Large Language Models (LLMs)** and integrates it with **NHTSA vehicle data** including recalls.

### Week 3-4 Deliverables ✓

✅ **LLM-based SLA Extraction**
- Designed comprehensive prompt for extracting financial terms, lease conditions, and policies
- Implemented OpenAI GPT-4 integration for structured data extraction
- Stores extracted data in PostgreSQL database (JSON format)
- Validates and normalizes extracted values

✅ **NHTSA API Integration**
- VIN lookup and vehicle specifications
- Recall information fetching
- Combined vehicle data responses

✅ **End-to-End Workflow**
- Upload contract → OCR → LLM extraction → Database storage
- Combined API endpoints for contract + vehicle data
- Complete testing suite

---

## Architecture

```
┌─────────────────┐
│  PDF Contract   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OCR Service   │ (Tesseract)
│  Extract Text   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Service    │ (OpenAI GPT-4)
│  Extract SLA    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   PostgreSQL    │ ←── │  NHTSA Service   │
│    Database     │     │ (Vehicle + Recalls)│
└─────────────────┘     └──────────────────┘
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependency added:**
- `openai>=1.12.0` - For LLM-based SLA extraction

### 2. Configure OpenAI API Key

You **must** set your OpenAI API key as an environment variable:

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY = "sk-your-api-key-here"
```

**Windows CMD:**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Permanent Setup (Windows):**
1. Search for "Environment Variables" in Windows
2. Add new System Variable: `OPENAI_API_KEY` = `sk-your-api-key-here`
3. Restart your terminal/IDE

**Get an API Key:**
- Go to https://platform.openai.com/api-keys
- Create a new secret key
- Copy and save it securely

### 3. Initialize Database

The database will auto-initialize on server startup. Tables include:
- `vehicles` - Vehicle specifications
- `vehicle_recalls` - Recall information
- `contracts` - Contract records
- `contract_sla` - Extracted SLA data
- `extractions` - LLM extraction tracking

### 4. Start the Backend Server

```bash
cd backend
uvicorn main:app --reload
```

Server will start at: `http://localhost:8000`

---

## API Endpoints

### 1. Upload Contract with VIN
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
  - vin: string (Vehicle Identification Number)
  - file: file (PDF or image of contract)

Response:
{
  "vin": "5YJSA1E14HF000001",
  "document_id": "uuid",
  "contract_id": "uuid",
  "vehicle_id": "uuid",
  "nhtsa_fetched": true,
  "database_stored": true,
  "status": "stored"
}
```

### 2. Extract SLA Data (LLM)
```http
POST /contract/{contract_id}/extract-sla

Response:
{
  "status": "success",
  "contract_id": "uuid",
  "sla_id": "uuid",
  "sla_data": {
    "apr_percent": 6.99,
    "money_factor": 0.00291,
    "term_months": 36,
    "monthly_payment": 1249.00,
    "down_payment": 5000.00,
    "msrp": 94990.00,
    "residual_value": 56994.00,
    "residual_percent_msrp": 60.0,
    "mileage_allowance_yr": 12000,
    "mileage_overage_fee": 0.30,
    "early_termination_fee": 7500.00,
    "disposition_fee": 595.00,
    "insurance_requirements": "Minimum $100,000/$300,000 liability...",
    "maintenance_resp": "Lessee responsible for routine maintenance...",
    "warranty_summary": "4-year/50,000-mile basic warranty...",
    "late_fee_policy": "Greater of $50 or 5% of payment",
    "other_terms": ["Gap insurance recommended", ...]
  }
}
```

### 3. Get Vehicle Info (NHTSA)
```http
GET /vehicle/{vin}

Response:
{
  "vin": "5YJSA1E14HF000001",
  "vehicle_info": {
    "Model Year": "2024",
    "Make": "Tesla",
    "Model": "Model S",
    "Body Class": "Sedan/Saloon",
    ...
  },
  "has_documents": true
}
```

### 4. Get Complete Vehicle Data (with Recalls)
```http
GET /vehicle/{vin}/complete

Response:
{
  "status": "success",
  "vin": "5YJSA1E14HF000001",
  "vehicle_info": {
    "year": 2024,
    "make": "Tesla",
    "model": "Model S",
    "trim": "Long Range"
  },
  "recalls": [
    {
      "recall_number": "23V-123",
      "component": "Air Bags",
      "summary": "...",
      "remedy": "..."
    }
  ],
  "recall_count": 2,
  "has_recalls": true
}
```

### 5. Get Complete Contract Data
```http
GET /contract/{contract_id}/complete

Response:
{
  "status": "success",
  "contract": {
    "contract_id": "uuid",
    "contract_type": "lease",
    "sla_data": { ... },
    "vehicle_id": "uuid"
  },
  "vehicle": {
    "vin": "5YJSA1E14HF000001",
    "year": 2024,
    "make": "Tesla",
    "model": "Model S",
    "recalls": [ ... ],
    "recall_count": 2
  }
}
```

---

## Testing

### Run End-to-End Tests

```bash
cd backend
python test_end_to_end.py
```

**Test Coverage:**
1. ✅ Contract upload with VIN
2. ✅ Vehicle data fetching from NHTSA
3. ✅ Recall information retrieval
4. ✅ LLM-based SLA extraction
5. ✅ Combined data retrieval
6. ✅ Database storage verification

### Manual Testing with cURL

**Upload Contract:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "vin=5YJSA1E14HF000001" \
  -F "file=@contract.pdf"
```

**Extract SLA:**
```bash
curl -X POST "http://localhost:8000/contract/{contract-id}/extract-sla"
```

**Get Vehicle Data:**
```bash
curl "http://localhost:8000/vehicle/5YJSA1E14HF000001/complete"
```

---

## LLM Prompt Design

The SLA extraction prompt is engineered to extract:

### Financial Terms
- APR (Annual Percentage Rate)
- Money Factor (for leases)
- Monthly Payment
- Down Payment / Due at Signing
- Total Fees
- MSRP, Cap Cost, Cap Cost Reduction

### Lease Terms
- Term Length (months)
- Residual Value & Percentage
- Annual Mileage Allowance
- Mileage Overage Fee

### Fees & Penalties
- Early Termination Fee
- Disposition Fee
- Purchase Option Price
- Late Fee Policy

### Requirements
- Insurance Requirements
- Maintenance Responsibility
- Warranty Summary
- Other Important Terms

### Prompt Features
- **Structured output:** JSON format matching database schema
- **Validation rules:** Numeric ranges and type checking
- **Error handling:** Null values for missing data
- **Low temperature (0.1):** Consistent, factual extraction
- **JSON mode:** Guaranteed valid JSON response

---

## Database Schema

### contract_sla table
```sql
CREATE TABLE contract_sla (
  id UUID PRIMARY KEY,
  contract_id UUID REFERENCES contracts(id),
  apr_percent NUMERIC(6,3),
  money_factor NUMERIC(10,6),
  term_months INT,
  monthly_payment NUMERIC(12,2),
  down_payment NUMERIC(12,2),
  fees_total NUMERIC(12,2),
  residual_value NUMERIC(12,2),
  residual_percent_msrp NUMERIC(6,3),
  msrp NUMERIC(12,2),
  cap_cost NUMERIC(12,2),
  cap_cost_reduction NUMERIC(12,2),
  mileage_allowance_yr INT,
  mileage_overage_fee NUMERIC(8,4),
  early_termination_fee NUMERIC(12,2),
  disposition_fee NUMERIC(12,2),
  purchase_option_price NUMERIC(12,2),
  insurance_requirements TEXT,
  maintenance_resp TEXT,
  warranty_summary TEXT,
  late_fee_policy TEXT,
  other_terms JSONB,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

### extractions table (tracking)
```sql
CREATE TABLE extractions (
  id UUID PRIMARY KEY,
  contract_id UUID REFERENCES contracts(id),
  model_name VARCHAR(120),
  prompt_version VARCHAR(60),
  status extraction_status,  -- pending, running, completed, failed
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  raw_output JSONB,
  error_message TEXT
);
```

---

## Cost Estimation

### OpenAI API Costs (GPT-4o-mini)

**Current Model:** `gpt-4o-mini`
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**Per Contract:**
- Average contract: ~3,000 tokens input
- Average extraction: ~500 tokens output
- **Cost: ~$0.0008 per contract** (less than 1 cent)

**Monthly Volume (1000 contracts):**
- Total cost: **~$0.80/month**

**Upgrade to GPT-4o (for higher accuracy):**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- **Cost: ~$0.012 per contract** (1.2 cents)
- Monthly (1000 contracts): **~$12/month**

---

## Accuracy & Validation

### Extraction Accuracy
- Model extracts exact numbers from contract text
- Validates numeric ranges (APR 0-50%, monthly payment $0-$10k, etc.)
- Uses low temperature (0.1) for consistent results
- Retries on JSON parse errors

### Data Validation
- Type checking (integers, decimals, strings)
- Range validation for all numeric fields
- Null handling for missing information
- No estimation or guessing - only exact extraction

### Testing Recommendations
1. Test with 10-20 sample contracts
2. Compare extracted values to actual contract
3. Calculate accuracy percentage
4. Fine-tune prompt if accuracy < 95%
5. Consider upgrading to GPT-4o if needed

---

## Troubleshooting

### "OPENAI_API_KEY not set"
**Solution:** Set the environment variable as shown in Setup section

### "Failed to parse LLM response"
**Possible causes:**
- Contract text too complex
- Response not in JSON format
- Model hallucination

**Solutions:**
- Check OCR quality (text should be readable)
- Retry the extraction
- Upgrade to GPT-4o model
- Review and improve prompt

### "No OCR text found"
**Solution:** Upload and process document first using `/upload` endpoint

### "Vehicle not found"
**Solution:** Ensure VIN is valid 17-character format

---

## Next Steps

### Production Readiness
- [ ] Add user authentication
- [ ] Implement rate limiting
- [ ] Add extraction confidence scores
- [ ] Create admin dashboard for reviewing extractions
- [ ] Set up monitoring and logging
- [ ] Add webhooks for async processing

### Feature Enhancements
- [ ] Support for loan contracts (not just leases)
- [ ] Multi-page contract handling
- [ ] Compare multiple offers
- [ ] Generate negotiation recommendations
- [ ] Add market pricing data integration
- [ ] Export reports (PDF, Excel)

### Accuracy Improvements
- [ ] Build validation dataset (100+ contracts)
- [ ] Implement human-in-the-loop review
- [ ] Add clause-level extraction (not just document-level)
- [ ] Train custom extraction model
- [ ] Implement correction feedback loop

---

## Contact & Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation
3. Run test suite to verify setup
4. Check console logs for detailed error messages

---

## License

See LICENSE file for details.

---

**Status:** ✅ Week 3-4 Deliverables Complete
- LLM-based SLA extraction working
- NHTSA vehicle data integration complete
- End-to-end workflow functional
- Database storage implemented
- Test suite available
