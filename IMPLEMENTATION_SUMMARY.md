# AI Negotiation Chatbot - Implementation Summary

## ✅ What Was Implemented

### 1. LLM Service (`backend/services/llm_service.py`)
A comprehensive AI service that provides:

**Price Negotiation Chatbot**
- Analyzes vehicle data from JSON storage
- Uses NHTSA specifications and recall information
- Extracts contract terms from OCR text
- Provides specific dollar amounts and savings percentages
- Generates talking points and negotiation strategies
- Considers recall impact on negotiation leverage

**SLA Extraction**
- Extracts 11 required contract parameters
- Calculates Contract Fairness Score (0-100)
- Compares terms against industry standards
- Identifies red flags and unfavorable terms

**Key Features:**
✅ Uses Groq API with Llama 3 70B model (fast & accurate)
✅ Temperature-tuned for different tasks (0.7 for negotiation, 0.3 for extraction)
✅ Comprehensive error handling
✅ Smart context building from JSON database

### 2. Negotiation API Endpoint (`POST /negotiate/{vin}`)

**Input:**
- `vin`: Vehicle Identification Number
- `user_query` (optional): Specific negotiation question

**Output:**
```json
{
  "status": "success",
  "vin": "1HGCM82633A004352",
  "vehicle": {
    "year": "2024",
    "make": "Honda",
    "model": "Accord"
  },
  "negotiation_advice": "Detailed AI-generated advice...",
  "has_recalls": true,
  "recall_count": 2,
  "model_used": "llama3-70b-8192"
}
```

**What It Does:**
1. Fetches complete vehicle data from JSON storage
2. Retrieves NHTSA vehicle info and recalls
3. Gets uploaded contract documents and OCR text
4. Sends comprehensive context to LLM
5. Returns structured negotiation recommendations

### 3. Enhanced SLA Extraction Endpoint (`POST /contract/{contract_id}/extract-sla`)

**Improvements:**
- Now uses AI to extract parameters (not manual parsing)
- Returns Contract Fairness Score
- Automatically saves SLA data to JSON
- Updates document with `sla_extracted: true`

**Output:**
```json
{
  "contract_id": "abc123",
  "vin": "1HGCM82633A004352",
  "filename": "lease_contract.pdf",
  "sla_extracted": true,
  "sla_data": {
    "interest_rate_apr": "4.9%",
    "monthly_payment": "$450",
    "fairness_score": 72,
    "...": "11 total parameters"
  }
}
```

### 4. Updated Dependencies

**Added to `requirements.txt`:**
```
groq>=0.4.0  # LLM API integration
```

**Updated `.env.local`:**
```env
GROQ_API_KEY=your-groq-api-key-here
```

### 5. Documentation

Created comprehensive guides:

1. **[NEGOTIATION_CHATBOT_GUIDE.md](NEGOTIATION_CHATBOT_GUIDE.md)**
   - Complete API usage guide
   - Request/response examples
   - Python and JavaScript client code
   - Workflow examples
   - Troubleshooting guide

2. **Updated [README.md](README.md)**
   - Removed outdated PostgreSQL references
   - Added AI chatbot features
   - Updated architecture diagram
   - Added usage examples
   - Included example outputs

3. **[test_negotiation.py](test_negotiation.py)**
   - Comprehensive test suite
   - 5 different test scenarios
   - Server connectivity check
   - Interactive testing mode

## 🎯 How to Use

### Quick Start (3 Steps)

**1. Get Groq API Key**
```
Visit: https://console.groq.com/keys
Sign up and create an API key (free tier available)
```

**2. Configure Environment**
```bash
# Edit .env.local
GROQ_API_KEY=gsk_your_actual_key_here
```

**3. Start Server & Test**
```bash
# Terminal 1: Start server
cd backend
uvicorn main:app --reload --port 8080

# Terminal 2: Run tests
python test_negotiation.py
```

### Example Usage

**Basic Negotiation (No Specific Query):**
```bash
curl -X POST "http://localhost:8080/negotiate/1HGCM82633A004352"
```

**Specific Negotiation Question:**
```bash
curl -X POST "http://localhost:8080/negotiate/1HGCM82633A004352" \
  -F "user_query=How can I reduce my monthly payment from ₹22,000?"
```

**Extract SLA from Contract:**
```bash
# Get contract ID first
curl "http://localhost:8080/vehicle/1HGCM82633A004352/complete"

# Then extract SLA
curl -X POST "http://localhost:8080/contract/{contract_id}/extract-sla"
```

## 📊 What Data Is Used

The chatbot analyzes data from your JSON database:

### From `backend/vehicle_data/{VIN}.json`:
```json
{
  "vin": "1HGCM82633A004352",
  "nhtsa_vehicle_info": {
    "Make": "Honda",
    "Model": "City VX",
    "ModelYear": "2022",
    "BodyClass": "Sedan",
    "EngineConfiguration": "4-cylinder",
    "...": "30+ data points"
  },
  "documents": [
    {
      "document_id": "...",
      "filename": "lease_contract.pdf",
      "ocr_text": "Full contract text extracted by Tesseract",
      "sla_extracted": false
    }
  ]
}
```

### From NHTSA API (fetched automatically):
```json
{
  "recalls": [
    {
      "Component": "ENGINE",
      "Summary": "Recall description...",
      "Consequence": "Safety impact..."
    }
  ]
}
```

## 🤖 AI Model Details

**Provider:** Groq  
**Model:** llama3-70b-8192  
**Why Groq?**
- ⚡ Fast inference (100+ tokens/second)
- 💰 Cost-effective (free tier available)
- 🎯 Accurate for financial analysis
- 📝 Excellent reasoning capabilities

**Temperature Settings:**
- Negotiation: 0.7 (creative but focused suggestions)
- SLA Extraction: 0.3 (precise parameter extraction)

**Token Limits:**
- Negotiation advice: 2000 tokens (~1500 words)
- SLA extraction: 2000 tokens

## 🎨 Chatbot Capabilities

### What It Can Do:

✅ **Analyze Current Deal:**
- Current monthly payment
- Down payment amount
- Total cost over lease term
- Interest rate / money factor

✅ **Identify Negotiation Opportunities:**
- Down payment reduction suggestions
- Monthly payment optimization
- Fee elimination strategies
- Better term recommendations

✅ **Provide Specific Numbers:**
- Dollar amounts for each opportunity
- Percentage savings
- Total potential savings
- Target values to propose

✅ **Leverage Recalls:**
- Uses recall data as negotiation leverage
- Suggests price reductions for safety issues
- Recommends extended warranties
- Identifies multiple recall patterns

✅ **Generate Talking Points:**
- Professional negotiation scripts
- Data-driven arguments
- Industry standard references
- Counter-offer strategies

### What Makes It Smart:

1. **Context-Aware**: Uses complete vehicle data, not just contract
2. **Data-Driven**: References industry standards and market rates
3. **Recall-Conscious**: Factors in safety recalls for leverage
4. **Specific**: Provides exact dollar amounts, not vague advice
5. **Actionable**: Gives step-by-step negotiation scripts

## 📈 Example Outputs

### Negotiation Advice Sample:
```
📊 DEAL ANALYSIS - 2022 Honda City VX

**Current Terms:**
- Monthly Payment: ₹22,000
- Down Payment: ₹1,50,000
- Term: 36 months
- Total Cost: ₹9,42,000

🎯 NEGOTIATION OPPORTUNITIES:

1. Down Payment Reduction (Potential Savings: ₹50,000)
   - Current: ₹1,50,000
   - Target: ₹1,00,000
   - Reason: Industry standard is ₹1,00,000 for this segment
   - Talking Point: "I've researched comparable deals and ₹1,50,000 
     is above market. I'm comfortable with ₹1,00,000 down."

2. Monthly Payment Reduction (Potential Savings: ₹1,08,000 over term)
   - Current: ₹22,000/month
   - Target: ₹19,000/month
   - Reason: Market rate for this model is ₹19,500/month
   - Talking Point: "The market rate is around ₹19,500. Can we 
     adjust to ₹19,000?"

🚩 RED FLAGS:
- Mileage overage charge (₹8/km) is slightly high
- Standard rate is ₹5-6/km in Indian market

💰 TOTAL POTENTIAL SAVINGS: ₹1,58,000
```

### SLA Extraction Sample:
```json
{
  "interest_rate_apr": "Not specified (lease agreement)",
  "lease_term_months": 36,
  "monthly_payment": "₹22,000",
  "down_payment": "₹1,50,000",
  "residual_value": "₹6,50,000 (estimated 45% of original value)",
  "mileage_allowance": "12,000 km/year, ₹8/excess km",
  "acquisition_fee": "Included in down payment",
  "disposition_fee": "Not mentioned",
  "early_termination_penalty": "2% per month late fee",
  "wear_and_tear": "Lessee responsible for maintenance",
  "purchase_option": "₹6,50,000",
  "fairness_score": 68,
  "justification": "Fair deal - standard terms for Indian market..."
}
```

## 🔄 Integration Flow

```
User → Upload Contract (with VIN)
  ↓
Backend → OCR Extraction (Tesseract)
  ↓
Backend → NHTSA Lookup (Vehicle Data + Recalls)
  ↓
Backend → Save to JSON Database
  ↓
User → Request Negotiation Advice
  ↓
Backend → Build Context from JSON
  ↓
LLM Service → Groq API (Llama 3 70B)
  ↓
LLM Service → Generate Recommendations
  ↓
User → Receive Specific Advice with Dollar Amounts
```

## ✅ Testing Checklist

- [x] LLM service created with Groq integration
- [x] Negotiation endpoint implemented
- [x] SLA extraction endpoint updated
- [x] Dependencies added to requirements.txt
- [x] Environment variables configured
- [x] Documentation created
- [x] Test suite implemented
- [x] README updated
- [ ] **Groq API key configured** (User needs to add this)
- [ ] **Server tested** (Run: `python test_negotiation.py`)

## 🚀 Next Steps

### Immediate (Setup):
1. Get Groq API key from https://console.groq.com/keys
2. Add key to `.env.local`
3. Run `python test_negotiation.py` to verify setup

### Short-term (Testing):
4. Upload real contract PDFs
5. Test negotiation advice quality
6. Verify SLA extraction accuracy
7. Test with different vehicle types

### Medium-term (Enhancement):
8. Build frontend UI for chatbot
9. Add conversation history
10. Support multi-turn dialogue
11. Add more negotiation strategies

### Long-term (Production):
12. Deploy to cloud (AWS/Azure/GCP)
13. Add user authentication
14. Implement rate limiting
15. Add analytics and logging

## 💡 Tips for Best Results

1. **Upload complete contracts** - More data = better advice
2. **Ask specific questions** - "How can I reduce the down payment?" vs "Help me"
3. **Check fairness score first** - Know if you already have a good deal
4. **Use recall information** - Vehicles with recalls have more leverage
5. **Test with real data** - The chatbot learns from actual contract patterns

## 📞 Support

- FastAPI Docs: http://localhost:8080/docs
- Groq Documentation: https://console.groq.com/docs
- Issues: Check server logs for errors
- Testing: Run `python test_negotiation.py` for diagnostics

---

**Status:** ✅ Implementation Complete  
**Ready to Use:** Add GROQ_API_KEY and start the server!
