# AI-LLM Based Car Lease / Loan Contract Review Assistant

## 📖 Project Description
This project is a backend-based AI assistant that helps users upload car lease or loan contracts and extract important information using OCR. The system is designed to assist in reviewing and analyzing contract terms in a structured manner.

---

## 🎯 Objectives
- Upload car lease or loan contract documents
- Extract text from scanned PDFs or images using OCR
- Prepare extracted text for AI-based analysis
- Identify important contract clauses in later milestones

---

## 🧩 Technologies Used
- Python
- Flask
- Tesseract OCR
- PDF2Image
- PIL (Pillow)

---

## 📂 Project Structure
CarLeaseAI/
│
├── backend/
│ ├── app.py
│ ├── ocr.py
│
├── uploads/
│ └── uploaded contract files
│
├── README.md
---

## ✅ Milestone-1: Contract Upload & OCR
### Implemented Features:
- Flask backend server setup
- Contract upload interface using HTTP POST
- Storage of uploaded contracts in uploads folder
- OCR integration using Tesseract
- Display of extracted contract text

### Output:
- Successfully uploaded contract
- Extracted readable text from the contract
---

## ▶️ How to Run the Project
1. Open Command Prompt in backend folder
2. Run the server:
python app.py

css
Copy code
3. Open browser and go to:
http://127.0.0.1:5000/upload
4. Upload a contract PDF or image

---

## 🔮 Future Scope (Milestone-2)
- AI/LLM based clause extraction
- Risk identification in contracts
- Negotiation suggestions
- Structured JSON output

---
