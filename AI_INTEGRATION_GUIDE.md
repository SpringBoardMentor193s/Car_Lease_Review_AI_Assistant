# Quick Implementation Guide - AI Chatbot & SLA Extraction

## Overview

This guide shows you how to integrate:
1. **AI Price Negotiation Chatbot** - Uses JSON data to help users negotiate better car deals
2. **SLA Extraction** - Extracts contract terms from OCR text stored in JSON files

Full prompts and examples are in: [PROMPTS_DESIGN.md](PROMPTS_DESIGN.md)

---

## 1. Price Negotiation Chatbot Integration

### What It Does:
- Analyzes vehicle data, contract terms, and recalls from JSON storage
- Provides negotiation strategies and talking points
- Identifies overpriced fees and unfair terms
- Uses recalls as leverage for better deals

### Quick Setup:

```python
# Add to main.py
from openai import OpenAI  # or any LLM provider

# Initialize LLM client
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/chat/negotiate/{vin}")
async def negotiate_price(vin: str, message: str = Form(...)):
    """AI-powered price negotiation assistant"""
    
    # Load vehicle data from JSON
    vin = vin.upper().strip()
    json_path = f"{DATA_DIR}/{vin}.json"
    
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="VIN not found")
    
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # Build context for chatbot
    context = f"""
Vehicle: {data['nhtsa_vehicle_info'].get('Model Year')} {data['nhtsa_vehicle_info'].get('Make')} {data['nhtsa_vehicle_info'].get('Model')}
VIN: {vin}

Contract Details:
{data['documents'][0]['ocr_text'] if data.get('documents') else 'No contract uploaded yet'}

User Question: {message}
"""
    
    # Call LLM with negotiation prompt (see PROMPTS_DESIGN.md)
    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": NEGOTIATION_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
        temperature=0.7
    )
    
    return {
        "vin": vin,
        "user_message": message,
        "ai_response": response.choices[0].message.content
    }
```

### Example Request:

```bash
curl -X POST "http://localhost:8080/chat/negotiate/5YJSA1E14HF000001" \
  -F "message=The dealer wants $450/month with $3000 down. Is this a good deal?"
```

---

## 2. SLA Extraction from JSON

### What It Does:
- Extracts **11 critical parameters** from contract OCR text:
  1. Interest Rate/APR
  2. Lease term duration
  3. Monthly payment
  4. Down payment
  5. Residual value
  6. Mileage allowance & overage charges
  7. Early termination clause
  8. Purchase option (buyout price)
  9. Maintenance responsibilities
  10. Warranty and insurance coverage
  11. Penalties or late fee clauses
- Calculates **Contract Fairness Score** (0-100)
- Identifies red flags (excessive fees, unfair terms)
- Provides negotiation priority list
- Validates calculations and reasonableness

### Quick Setup:

```python
@app.post("/contract/{contract_id}/extract-sla")
async def extract_sla(contract_id: str):
    """Extract SLA details from contract using AI"""
    
    # Find contract in JSON files
    json_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    
    for json_file in json_files:
        json_path = os.path.join(DATA_DIR, json_file)
        with open(json_path, "r") as f:
            data = json.load(f)
            
            for idx, doc in enumerate(data.get("documents", [])):
                if doc.get("contract_id") == contract_id:
                    # Prepare input for LLM
                    extraction_input = {
                        "vin": data["vin"],
                        "vehicle": data["nhtsa_vehicle_info"],
                        "ocr_text": doc["ocr_text"]
                    }
                    
                    # Call LLM with SLA extraction prompt
                    response = llm_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": SLA_EXTRACTION_PROMPT},
                            {"role": "user", "content": json.dumps(extraction_input)}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    # Parse extracted SLA data
                    sla_data = json.loads(response.choices[0].message.content)
                    
                    # Save back to JSON
                    data["documents"][idx]["sla_data"] = sla_data
                    with open(json_path, "w") as wf:
                        json.dump(data, wf, indent=2)
                    
                    return {
                        "status": "success",
                        "contract_id": contract_id,
                        "fairness_score": sla_data["contract_fairness_score"]["overall_score"],
                        "rating": sla_data["contract_fairness_score"]["rating"],
                        "red_flags_count": len(sla_data["red_flags"]),
                        "sla_data": sla_data,
                        "negotiation_priorities": sla_data["contract_fairness_score"]["negotiation_priority"][:3]
                    }
    
    raise HTTPException(status_code=404, detail="Contract not found")
```

###

**Example Response:**
```json
{
  "status": "success",
  "contract_id": "abc-123-def",
  "fairness_score": 68,
  "rating": "Fair",
  "red_flags_count": 5,
  "negotiation_priorities": [
    "1. Reduce down payment from $7,500 to $2,500 (Save $5,000)",
    "2. Increase annual mileage to 12,000 miles",
    "3. Reduce monthly payment by $50 (Save $1,800)"
  ],
  "sla_data": {
    "sla_parameters": {...},
    "contract_fairness_score": {...},
    "red_flags": [...]
  }
}
``` Example Request:

```bash
curl -X POST "http://localhost:8080/contract/abc-123-def/extract-sla"
```

---

## 3. Environment Setup

Add to your `.env.local`:

```bash
# LLM API Key (choose one)
OPENAI_API_KEY=sk-your-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-key-here
# or
GOOGLE_API_KEY=your-google-key-here
```

Install LLM SDK:

```bash
# For OpenAI
pip install openai

# For Anthropic (Claude)
pip install anthropic

# For Google (Gemini)
pip install google-generativeai
```

---

## 4. System Prompts Reference

### Negotiation Chatbot Prompt (abbreviated):

```python
NEGOTIATI these 11 required parameters:**
1. Interest Rate/APR
2. Lease Term Duration
3. Monthly Payment
4. Down Payment
5. Residual Value
6. Mileage Allowance & Overage Charges
7. Early Termination Clause
8. Purchase Option (Buyout Price)
9. Maintenance Responsibilities
10. Warranty and Insurance Coverage
11. Penalties or Late Fee Clauses

**Calculate Contract Fairness Score (0-100):**
- Score 6 categories: interest rate, payment structure, mileage, fees, flexibility, transparency
- Identify red flags by severity (critical, high, medium, low)
- Provide negotiation priorities ordered by savings potential
- Give overall rating: Excellent (90-100), Good (75-89), Fair (60-74), Poor (40-59), Very Poor (0-39)

**Return valid JSON with:**
- sla_parameters (all 11 items with assessments)
- red_flags (severity, issue, impact, recommendation)
- contract_fairness_score (overall score, category scores, strengths, weaknesses, negotiation priorities)
- structured_summary (key terms, recommended action)
**Response format:**
1. Deal Summary
2. Negotiation Opportunities (with $ savings)
3. Red Flags
4. Step-by-step negotiation script
5. Total potential savings
"""
```

### SLA Extraction Prompt (abbreviated):

```python
SLA_EXTRACTION_PROMPT = """
Extract all Service Level Agreement details from the car lease/purchase contract OCR text.

**Extract:**
- Financial terms (APR, monthly payment, down payment, MSRP, cap cost)
- Lease terms (term length, mileage, residual value)
- Fees (acquisition, documentation, disposition, early termination)
- Insurance and warranty requirements
- Additional terms and20-$0.30 per contract (one-time, with fairness scoring)

**OpenAI GPT-3.5 Turbo:**
- Negotiation: ~$0.002 per chat message
- SLA Extraction: ~$0.015-$0.02cial_terms: {...}, lease_terms: {...}, fees: {...}, red_flags: [...]}
"""
```

---

## 5. Testing

### Test Negotiation Chatbot:

```python
# Make sure you have a VIN with uploaded contract
response = requests.post(
    "http://localhost:8080/chat/negotiate/5YJSA1E14HF000001",
    data={"message": "Should I negotiate the down payment?"}
)
print(response.json()["ai_response"])
```

### Test SLA Extraction:

```python
# Upload a contract first, then extract SLA
response = requests.post(
    "http://localhost:8080/contract/your-contract-id/extract-sla"
)
print(response.json()["sla_data"])
```

---

## 6. Cost C
#   fairness_score: 68,
#   rating: "Fair",
#   sla_data: {
#     sla_parameters: {...11 parameters...},
#     contract_fairness_score: {...},
#     red_flags: [...]
#   }
# 

**OpenAI GPT-4:**
- NegSLA_FAIRNESS_SCORE.md](SLA_FAIRNESS_SCORE.md)** - Quick reference for 11 parameters & scoring
- **[PROMPTS_DESIGN.md](PROMPTS_DESIGN.md)** - Complete prompt library with examples
- SLA Extraction: ~$0.15 per contract (one-time)

**OpenAI GPT-3.5 Turbo:**
- Negotiation: ~$0.002 per chat message
- SLA Extraction: ~$0.01 per contract

**Optimization Tips:**
- Use GPT-3.5 for simple queries, GPT-4 for complex negotiation
- Cache vehicle data to reduce tokens
- Limit OCR text to relevant sections (first 10,000 chars)

---

## 7. Next Steps

1. ✅ Review [PROMPTS_DESIGN.md](PROMPTS_DESIGN.md) for complete prompts
2. ✅ Choose your LLM provider (OpenAI, Anthropic, Google)
3. ✅ Add the endpoints to `backend/main.py`
4. ✅ Set up API key in `.env.local`
5. ✅ Test with sample contracts
6. ✅ Integrate with frontend

---

## Example Complete Workflow

```bash
# 1. Upload contract
curl -X POST "http://localhost:8080/upload" \
  -F "vin=5YJSA1E14HF000001" \
  -F "file=@lease_contract.pdf"
# Returns: {"contract_id": "abc-123"}

# 2. Extract SLA terms
curl -X POST "http://localhost:8080/contract/abc-123/extract-sla"
# Returns: {sla_data: {monthly_payment: 450, down_payment: 3000, ...}}

# 3. Start negotiation chat
curl -X POST "http://localhost:8080/chat/negotiate/5YJSA1E14HF000001" \
  -F "message=I want to save $2000. What should I negotiate?"
# Returns: {ai_response: "Here's your negotiation strategy..."}
```

---

For full prompt details, implementation examples, and best practices, see:
- **[PROMPTS_DESIGN.md](PROMPTS_DESIGN.md)** - Complete prompt library
