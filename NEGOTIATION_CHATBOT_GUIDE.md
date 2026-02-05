# AI Negotiation Chatbot - Usage Guide

## Overview

The AI-powered price negotiation chatbot helps users get the best deal on their car lease or purchase by analyzing vehicle data, recalls, and contract details from your JSON database.

## Setup

### 1. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create a new API key
4. Copy the API key

### 2. Configure Environment

Edit `.env.local` and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 3. Start the Server

```bash
cd backend
uvicorn main:app --reload --port 8080
```

## API Endpoints

### 1. Price Negotiation Chatbot

**Endpoint:** `POST /negotiate/{vin}`

**Description:** Get AI-powered negotiation advice for a specific vehicle

**Parameters:**
- `vin` (path): Vehicle Identification Number
- `user_query` (form, optional): Specific question about negotiation

**Example Request:**

```bash
curl -X POST "http://localhost:8080/negotiate/1HGCM82633A004352" \
  -F "user_query=How can I negotiate a better monthly payment?"
```

**Example Response:**

```json
{
  "status": "success",
  "vin": "1HGCM82633A004352",
  "vehicle": {
    "vin": "1HGCM82633A004352",
    "year": "2024",
    "make": "Honda",
    "model": "Accord",
    "trim": "EX"
  },
  "negotiation_advice": "📊 DEAL ANALYSIS - 2024 Honda Accord EX\n\n**Current Terms:**\n- Monthly Payment: $450\n- Down Payment: $3,000\n- Term: 36 months\n\n**🎯 NEGOTIATION OPPORTUNITIES:**\n\n1. **Down Payment Reduction** (Potential Savings: $1,500)\n   - Current: $3,000\n   - Target: $1,500\n   - Justification: Industry standard for this vehicle class\n   ...",
  "has_recalls": true,
  "recall_count": 2,
  "model_used": "llama3-70b-8192"
}
```

### 2. Extract SLA Parameters

**Endpoint:** `POST /contract/{contract_id}/extract-sla`

**Description:** Extract all 11 SLA parameters and calculate Contract Fairness Score (0-100)

**Parameters:**
- `contract_id` (path): Contract ID from upload response

**Example Request:**

```bash
curl -X POST "http://localhost:8080/contract/abc123-def456/extract-sla"
```

**Example Response:**

```json
{
  "contract_id": "abc123-def456",
  "vin": "1HGCM82633A004352",
  "filename": "lease_contract.pdf",
  "sla_extracted": true,
  "sla_data": {
    "interest_rate_apr": "4.9%",
    "lease_term_months": 36,
    "monthly_payment": "$450",
    "down_payment": "$3,000",
    "residual_value": "58% ($18,500)",
    "mileage_allowance": "12,000 miles/year, $0.25/excess mile",
    "acquisition_fee": "$795",
    "disposition_fee": "$395",
    "early_termination_penalty": "Remaining payments + $500",
    "wear_and_tear": "Normal wear acceptable",
    "purchase_option": "$18,500",
    "fairness_score": 72,
    "score_justification": "Good deal with competitive terms..."
  },
  "vehicle_info": {...}
}
```

## Complete Workflow Example

### Step 1: Upload Contract

```bash
curl -X POST "http://localhost:8080/upload" \
  -F "vin=1HGCM82633A004352" \
  -F "file=@/path/to/lease_contract.pdf"
```

Response:
```json
{
  "vin": "1HGCM82633A004352",
  "contract_id": "abc123-def456",
  "filename": "lease_contract.pdf",
  "nhtsa_fetched": true,
  "status": "uploaded"
}
```

### Step 2: Get Complete Vehicle Data

```bash
curl "http://localhost:8080/vehicle/1HGCM82633A004352/complete"
```

This returns:
- Vehicle specifications from NHTSA
- All recalls for the vehicle
- All uploaded documents with OCR text

### Step 3: Extract SLA Parameters

```bash
curl -X POST "http://localhost:8080/contract/abc123-def456/extract-sla"
```

This extracts:
- 11 required SLA parameters
- Contract Fairness Score (0-100)
- Red flags and warnings

### Step 4: Get Negotiation Advice

```bash
curl -X POST "http://localhost:8080/negotiate/1HGCM82633A004352" \
  -F "user_query=I want to reduce my monthly payment by $50"
```

This provides:
- Deal summary
- Prioritized negotiation opportunities
- Specific dollar amounts and percentages
- Talking points for each negotiation area
- Impact of recalls on negotiation leverage
- Step-by-step action plan

## Python Client Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8080"
VIN = "1HGCM82633A004352"

# 1. Upload contract
with open("lease_contract.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f},
        data={"vin": VIN}
    )
contract_id = response.json()["contract_id"]
print(f"Uploaded contract: {contract_id}")

# 2. Extract SLA
sla_response = requests.post(
    f"{BASE_URL}/contract/{contract_id}/extract-sla"
)
sla_data = sla_response.json()
print(f"Fairness Score: {sla_data['sla_data'].get('fairness_score')}/100")

# 3. Get negotiation advice
negotiate_response = requests.post(
    f"{BASE_URL}/negotiate/{VIN}",
    data={"user_query": "How can I get the best deal?"}
)
advice = negotiate_response.json()
print(advice["negotiation_advice"])
```

## JavaScript/Frontend Example

```javascript
// Upload contract
const formData = new FormData();
formData.append('vin', '1HGCM82633A004352');
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8080/upload', {
  method: 'POST',
  body: formData
});
const { contract_id } = await uploadResponse.json();

// Extract SLA
const slaResponse = await fetch(
  `http://localhost:8080/contract/${contract_id}/extract-sla`,
  { method: 'POST' }
);
const slaData = await slaResponse.json();
console.log('Fairness Score:', slaData.sla_data.fairness_score);

// Get negotiation advice
const negotiateData = new FormData();
negotiateData.append('user_query', 'How can I save money on this deal?');

const negotiateResponse = await fetch(
  `http://localhost:8080/negotiate/1HGCM82633A004352`,
  { method: 'POST', body: negotiateData }
);
const advice = await negotiateResponse.json();
console.log(advice.negotiation_advice);
```

## Features

### Negotiation Chatbot Features

✅ **Data-Driven Analysis**
- Uses NHTSA vehicle specifications
- Considers active recalls (leverage for negotiation)
- Analyzes OCR-extracted contract text
- References industry standards and market rates

✅ **Specific Recommendations**
- Dollar amounts for each negotiation area
- Percentage savings calculations
- Prioritized by potential savings
- Talking points and justification

✅ **Recall Impact**
- Identifies safety issues = stronger position
- Recent recalls = demand price reduction
- Multiple recalls = significant leverage

✅ **Red Flag Detection**
- Unusual fees and charges
- Excessive dealer markup
- Hidden costs
- Unfavorable terms

### SLA Extraction Features

✅ **11 Required Parameters**
1. Interest Rate / APR
2. Lease Term Duration
3. Monthly Payment
4. Down Payment
5. Residual Value
6. Mileage Allowance & Overage
7. Acquisition Fee
8. Disposition Fee
9. Early Termination Penalties
10. Wear and Tear Standards
11. Purchase Option Price

✅ **Contract Fairness Score (0-100)**
- 90-100: Excellent deal
- 70-89: Good deal
- 50-69: Fair deal
- 30-49: Below average
- 0-29: Poor deal

## LLM Model Information

**Model:** Llama 3 70B (via Groq)
- Fast inference (~100 tokens/second)
- High accuracy for financial document analysis
- Excellent reasoning for negotiation strategies
- Cost-effective compared to GPT-4

**Temperature Settings:**
- Negotiation advice: 0.7 (creative but focused)
- SLA extraction: 0.3 (precise and accurate)

## Troubleshooting

### Error: "GROQ_API_KEY not found"
- Make sure you've added `GROQ_API_KEY` to `.env.local`
- Restart the server after updating `.env.local`

### Error: "No documents found for this VIN"
- Upload a contract first using `POST /upload`
- Verify the VIN is correct (uppercase, no spaces)

### Error: "No OCR text available"
- OCR extraction failed or file is corrupted
- Try uploading the contract again
- Ensure the PDF/image is clear and readable

### Poor Negotiation Advice Quality
- Make sure the contract has been uploaded and OCR processed
- Provide a specific user_query for better targeted advice
- Verify NHTSA data was fetched successfully

## Best Practices

1. **Always upload the contract first** - The chatbot needs contract data to provide specific advice
2. **Ask specific questions** - Instead of "Help me negotiate", ask "How can I reduce my down payment?"
3. **Review the fairness score** - Extract SLA first to understand if the deal is already good
4. **Use recall information** - Vehicles with recalls have stronger negotiation leverage
5. **Follow the action plan** - The chatbot provides step-by-step negotiation strategies

## Data Storage

All data is stored in JSON files:
- Location: `backend/vehicle_data/{VIN}.json`
- Contains: NHTSA data, documents, OCR text, SLA data
- No database required - pure JSON storage

## Security Notes

- Never commit `.env.local` to version control
- Keep your GROQ_API_KEY secret
- Uploaded contracts are stored locally (not in cloud)
- OCR text is stored in JSON for analysis

## Next Steps

1. ✅ Set up Groq API key
2. ✅ Upload test contracts
3. ✅ Test SLA extraction
4. ✅ Test negotiation chatbot
5. 🔲 Integrate with frontend UI
6. 🔲 Add user authentication
7. 🔲 Deploy to production

## Support

For issues or questions:
- Check the API at `http://localhost:8080/docs` (FastAPI auto-generated docs)
- Review PROMPTS_DESIGN.md for prompt details
- See SLA_FAIRNESS_SCORE.md for scoring methodology
