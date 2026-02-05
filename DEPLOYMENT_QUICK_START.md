# Quick Start: Deploy to Production in 1 Hour

## Option 1: Heroku (Recommended - Fastest)

### Step 1: Create Required Files

**Procfile:**
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**runtime.txt:**
```
python-3.12.0
```

### Step 2: Deploy
```bash
# Install Heroku CLI from: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create car-lease-ai-assistant

# Set environment variables
heroku config:set GROQ_API_KEY=your_groq_api_key_here
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-production-secret-key

# Deploy
git push heroku main

# Open app
heroku open
```

**Your API will be live at:** `https://car-lease-ai-assistant.herokuapp.com`

---

## Option 2: Azure (Best for Enterprise)

### Using Azure CLI:
```bash
# Install Azure CLI
# Create resource group
az group create --name CarLeaseAI --location eastus

# Create App Service plan
az appservice plan create --name CarLeaseAIPlan --resource-group CarLeaseAI --sku B1 --is-linux

# Create web app
az webapp create --resource-group CarLeaseAI --plan CarLeaseAIPlan --name car-lease-ai --runtime "PYTHON|3.12"

# Configure environment variables
az webapp config appsettings set --resource-group CarLeaseAI --name car-lease-ai --settings GROQ_API_KEY="your-key"

# Deploy
az webapp up --name car-lease-ai --resource-group CarLeaseAI
```

---

## Option 3: Railway (Modern Alternative)

1. Visit: https://railway.app
2. Click "Start a New Project"
3. Connect GitHub repository
4. Railway auto-detects Python
5. Add environment variables in dashboard
6. Deploy automatically

**Cost:** Free tier available, then $5/month

---

## Testing Production Deployment

```bash
# Test health endpoint
curl https://your-app-url.herokuapp.com/

# Test upload
curl -X POST https://your-app-url.herokuapp.com/upload \
  -F "vin=1HGCM82633A004352" \
  -F "file=@contract.pdf"

# Test negotiation
curl -X POST https://your-app-url.herokuapp.com/negotiate/1HGCM82633A004352 \
  -F "user_query=How can I save money?"
```

---

## GitHub Repository Setup

```bash
# Create .gitignore
cat > .gitignore << EOF
.env.local
__pycache__/
*.pyc
backend/uploads/
backend/vehicle_data/*.json
venv/
.vscode/
EOF

# Initialize Git
git init
git add .
git commit -m "Initial commit: AI lease negotiation assistant"

# Create repo on GitHub: https://github.com/new
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/car-lease-ai.git
git branch -M main
git push -u origin main
```

---

## What's Ready for Production

✅ **Already Production-Ready:**
- Document upload API
- OCR text extraction
- SLA extraction with AI
- Contract fairness scoring (0-100)
- Negotiation chatbot
- NHTSA VIN lookup
- Vehicle recall integration
- JSON storage system

⚠️ **Needs Before Production:**
- [ ] User authentication
- [ ] Rate limiting
- [ ] Error logging
- [ ] HTTPS/SSL
- [ ] Database backup strategy
- [ ] API monitoring

---

## Cost Estimates

| Service | Free Tier | Paid | Best For |
|---------|-----------|------|----------|
| **Heroku** | Yes (550 hrs/month) | $7/month | Quick start |
| **Railway** | Yes ($5 credit) | $5/month | Modern, easy |
| **Azure** | $200 credit | $10-50/month | Enterprise |
| **AWS** | Yes (12 months) | $5-20/month | Scalable |
| **Google Cloud** | $300 credit | $10-30/month | AI/ML features |

**Recommendation:** Start with Heroku free tier, upgrade as needed.

---

## Next: Mobile App Development

Once backend is deployed, build Flutter app:

```dart
// Configure API endpoint
const String API_BASE_URL = 'https://car-lease-ai-assistant.herokuapp.com';

// Upload contract from mobile
Future<void> uploadContract(String vin, File pdfFile) async {
  var request = http.MultipartRequest(
    'POST',
    Uri.parse('$API_BASE_URL/upload'),
  );
  request.fields['vin'] = vin;
  request.files.add(await http.MultipartFile.fromPath('file', pdfFile.path));
  
  var response = await request.send();
  // Handle response
}
```

**Mobile app timeline:** 2-3 weeks for full MVP
