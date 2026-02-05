# 🚗 Car Lease Review AI Assistant

An AI-powered application that helps consumers understand, review, and negotiate car lease/loan contracts using Large Language Models (LLMs). Get expert negotiation advice, extract contract terms, and identify potential savings—all powered by AI.

## ✨ Key Features

### 🤖 AI-Powered Price Negotiation Chatbot
- **Data-Driven Analysis**: Uses NHTSA vehicle data, recalls, and contract terms
- **Specific Recommendations**: Get dollar amounts and percentage savings for each negotiation opportunity
- **Recall Leverage**: Identifies how recalls strengthen your negotiation position
- **Red Flag Detection**: Spots unusual fees, excessive charges, and unfavorable terms
- **Step-by-Step Action Plan**: Provides talking points and negotiation strategies

### 📄 Smart SLA Extraction
- **11 Required Parameters**: Interest Rate, Term, Monthly Payment, Down Payment, Residual Value, Mileage, Fees, and more
- **Contract Fairness Score**: 0-100 score indicating deal quality (90-100 = Excellent, 0-29 = Poor)
- **Automated Analysis**: AI extracts terms from OCR'd contract text
- **Industry Comparison**: Compares your terms against market standards

### 🔍 Vehicle Intelligence
- **NHTSA Integration**: Automatic vehicle data lookup by VIN
- **Recall Tracking**: Real-time safety recall information
- **OCR Processing**: Extract text from PDF/image contracts
- **JSON Storage**: Simple, lightweight data storage (no database required)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Car_Lease_Review_AI_Assistant
pip install -r requirements.txt
```

### 2. Configure API Key

Get your Groq API key from [console.groq.com/keys](https://console.groq.com/keys)

Edit `.env.local`:
```env
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 3. Start the Server

```bash
cd backend
uvicorn main:app --reload --port 8080
```

**Access the API at:** http://localhost:8080/docs

### 4. Test the Chatbot

```bash
python test_negotiation.py
```

## 📖 Documentation

- **[NEGOTIATION_CHATBOT_GUIDE.md](NEGOTIATION_CHATBOT_GUIDE.md)** - Complete API usage guide with examples
- **[PROMPTS_DESIGN.md](PROMPTS_DESIGN.md)** - LLM prompt engineering details
- **[SLA_FAIRNESS_SCORE.md](SLA_FAIRNESS_SCORE.md)** - Scoring methodology
- **[AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md)** - Integration instructions

## 🎯 Usage Examples

### Upload a Contract
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "vin=1HGCM82633A004352" \
  -F "file=@contract.pdf"
```

### Get Negotiation Advice
```bash
curl -X POST "http://localhost:8080/negotiate/1HGCM82633A004352" \
  -F "user_query=How can I reduce my monthly payment?"
```

### Extract SLA Parameters
```bash
curl -X POST "http://localhost:8080/contract/{contract_id}/extract-sla"
```

## 🏗️ Architecture

```
Car_Lease_Review_AI_Assistant/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── llm_service.py      # AI negotiation & SLA extraction
│   │   ├── ocr_service.py      # Tesseract OCR integration
│   │   └── nhtsa_service.py    # Vehicle data API
│   ├── vehicle_data/           # JSON storage (no database!)
│   └── uploads/contracts/      # Uploaded contract files
├── test_negotiation.py         # Test suite
├── .env.local                  # Configuration (API keys)
└── requirements.txt            # Python dependencies
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **LLM**: Groq (Llama 3 70B) - Fast & accurate
- **OCR**: Tesseract
- **Vehicle Data**: NHTSA API
- **Storage**: JSON files (lightweight, no database)
- **Server**: Uvicorn

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/upload` | POST | Upload contract + fetch vehicle data |
| `/negotiate/{vin}` | POST | Get AI negotiation advice |
| `/contract/{id}/extract-sla` | POST | Extract SLA + fairness score |
| `/vehicle/{vin}` | GET | Get NHTSA vehicle info |
| `/vehicle/{vin}/recalls` | GET | Get vehicle recalls |
| `/vehicle/{vin}/complete` | GET | Complete vehicle data + documents |

## 🎓 How It Works

1. **Upload**: User uploads a lease/loan contract PDF
2. **OCR**: Tesseract extracts text from the document
3. **NHTSA Lookup**: Automatic vehicle data fetch by VIN
4. **AI Analysis**: LLM analyzes contract terms, market rates, and recalls
5. **Recommendations**: Provides specific negotiation strategies with dollar amounts
6. **Fairness Score**: Rates the contract 0-100 based on industry standards

## 🔐 Security & Privacy

- All data stored locally in JSON files
- Contracts never sent to third-party services (except Groq LLM for analysis)
- GROQ_API_KEY kept in `.env.local` (never commit to git)
- No database, no cloud storage required

## 🧪 Testing

Run the complete test suite:
```bash
python test_negotiation.py
```

This tests:
- ✅ Server connectivity
- ✅ Vehicle data retrieval
- ✅ Negotiation chatbot
- ✅ SLA extraction
- ✅ Fairness scoring

## 📝 Example Output

### Negotiation Advice
```
📊 DEAL ANALYSIS - 2024 Honda Accord EX

**Current Terms:**
- Monthly Payment: $450
- Down Payment: $3,000
- Term: 36 months

🎯 NEGOTIATION OPPORTUNITIES:

1. Down Payment Reduction (Potential Savings: $1,500)
   - Current: $3,000
   - Target: $1,500
   - Talking Point: "Industry standard is $1,500 for this class"

2. Monthly Payment Reduction (Potential Savings: $1,080)
   - Current: $450/month
   - Target: $420/month
   - Talking Point: "Market rate for this trim is $410"

💰 TOTAL POTENTIAL SAVINGS: $2,580
```

### Fairness Score
```
Contract Fairness Score: 72/100 (Good Deal)

Justification:
- Interest rate of 4.9% is competitive
- Monthly payment aligned with market
- Down payment slightly high
- Mileage allowance is standard
- No unusual fees detected
```

## 🚧 Roadmap

- ✅ AI negotiation chatbot
- ✅ SLA extraction with fairness scoring
- ✅ NHTSA vehicle data integration
- ✅ OCR processing
- ⬜ Frontend web interface
- ⬜ Mobile app (iOS/Android)
- ⬜ User authentication
- ⬜ Cloud deployment
- ⬜ Multi-language support

## 🤝 Contributing

This is a learning project demonstrating AI integration in automotive finance. Contributions welcome!

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **NHTSA API**: Vehicle data and recalls
- **Groq**: Fast LLM inference
- **Tesseract OCR**: Text extraction
- **FastAPI**: Modern Python web framework
