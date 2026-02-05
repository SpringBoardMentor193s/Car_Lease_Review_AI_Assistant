# Quick Start: SLA Extraction & Vehicle Data Integration

This guide will get you up and running in 5 minutes.

## Prerequisites

- Python 3.8+ installed
- PostgreSQL running (or use JSON-only mode)
- Groq API key ([Get one free here](https://console.groq.com/keys))

## Step 1: Install Dependencies

```powershell
cd d:\infosys\Car_Lease_Review_AI_Assistant
pip install -r requirements.txt
```

## Step 2: Set Groq API Key

**PowerShell (Windows):**
```powershell
$env:GROQ_API_KEY = "gsk_your-api-key-here"
```

**Permanent (Add to PowerShell Profile):**
```powershell
# Edit profile
notepad $PROFILE

# Add this line:
$env:GROQ_API_KEY = "gsk_your-api-key-here"
```

## Step 3: Start the Backend

```powershell
cd backend
uvicorn main:app --reload
```

✅ Server running at: http://localhost:8000

## Step 4: Run Tests

**Open a new terminal:**
```powershell
cd backend
python test_end_to_end.py
```

The test will:
1. Create a sample contract
2. Upload it with a VIN
3. Fetch vehicle data from NHTSA
4. Extract SLA data using Groq LLM
5. Retrieve combined data
6. Display all results

## Step 5: Try It Yourself

### Upload a Real Contract

```powershell
# Using curl (install from https://curl.se/windows/)
curl -X POST "http://localhost:8000/upload" `
  -F "vin=5YJSA1E14HF000001" `
  -F "file=@path/to/contract.pdf"
```

### View in Browser

Open: http://localhost:8000/docs

This shows the interactive API documentation (Swagger UI).

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Upload contract with VIN |
| `/contract/{id}/extract-sla` | POST | Extract SLA with LLM |
| `/vehicle/{vin}/complete` | GET | Get vehicle + recalls |
| `/contract/{id}/complete` | GET | Get contract + SLA + vehicle |

## Example Response

**After SLA Extraction:**
```json
{
  "status": "success",
  "sla_data": {
    "apr_percent": 6.99,
    "monthly_payment": 1249.00,
    "term_months": 36,
    "down_payment": 5000.00,
    "msrp": 94990.00,
    "residual_value": 56994.00,
    "mileage_allowance_yr": 12000,
    "mileage_overage_fee": 0.30
  }
}
```

## Troubleshooting

**"GROQ_API_KEY not set"**
→ Set the environment variable (Step 2)

**"Connection refused"**
→ Start the backend server (Step 3)

**"No module named 'groq'"**
→ Run `pip install -r requirements.txt`

## What's Next?

1. ✅ Test with your own PDF contracts
2. ✅ Review extracted data accuracy
3. ✅ Check database for stored records
4. ✅ Integrate with your frontend
5. ✅ Deploy to production

## Full Documentation

See [SLA_EXTRACTION_GUIDE.md](SLA_EXTRACTION_GUIDE.md) for:
- Complete API reference
- Database schema details
- Cost estimations
- Accuracy tuning
- Production deployment

---

**Need Help?** Check the full guide or review [backend/test_end_to_end.py](backend/test_end_to_end.py) for working examples.
