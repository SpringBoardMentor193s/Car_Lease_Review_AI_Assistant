"""
SLA Extractor Module
Handles file text extraction and SLA analysis using Ollama
"""

import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import ollama


def extract_text_from_file(filepath):
    """Extract text content from uploaded file"""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    try:
        # Configure Tesseract executable path from environment if provided
        tesseract_cmd = os.getenv('TESSERACT_CMD')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # default Windows install path (user provided): adjust if needed
            default_paths = [
                r"C:\Program Files\tesseract-5.5.2\tesseract.exe",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            ]
            for p in default_paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break

        if ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            # Try to extract embedded text first using PyMuPDF
            try:
                doc = fitz.open(filepath)
                text_pages = []
                for page in doc:
                    text = page.get_text()
                    text_pages.append(text)
                full_text = "\n".join(text_pages).strip()
                if full_text:
                    return full_text
                # If no text, render pages to images and OCR
                ocr_text = []
                for page in doc:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    page_text = pytesseract.image_to_string(img)
                    ocr_text.append(page_text)
                return "\n".join(ocr_text).strip()
            except Exception:
                return f"[PDF file: {os.path.basename(filepath)}] (failed to extract)"
        elif ext in ['.jpg', '.jpeg', '.png']:
            # Use OCR on images
            try:
                img = Image.open(filepath)
                text = pytesseract.image_to_string(img)
                return text.strip()
            except Exception:
                return f"[Image file: {os.path.basename(filepath)}]"
        else:
            # For other file types, return basic info
            return f"[File: {os.path.basename(filepath)}]"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def process_with_ollama(text, filename):
    """Process text with Ollama to extract SLA information"""
    try:
        prompt = (
            "Analyze the following contract or document content from file '" + filename + "' and extract SLA-related information and risks.\n\n"
            "Content:\n" + text + "\n\n"
            "Please provide a structured JSON object with the following fields:\n\n"
            "- `sla_parameters`: an object mapping SLA metric names to their values and short explanations (e.g., availability: \"99.9% - monthly uptime\", response_time: \"24 hours - support response\").\n"
            "- `red_flags`: a list of short strings describing any risky clauses, unusual obligations, one-sided terms, missing protections, or compliance concerns.\n"
            "- `contract_fairness_score`: a numeric score from 0 to 100 assessing overall fairness to the customer (100 = very fair). Provide a brief `score_explanation` string explaining the score.\n"
            "- `summary`: a short textual summary (2-4 sentences) of the contract's key points.\n\n"
            "Return only valid JSON (no surrounding commentary). Example structure:\n"
            "{\n"
            "  \"sla_parameters\": {\"availability\": \"99.9% - monthly uptime\", \"response_time\": \"24h\"},\n"
            "  \"red_flags\": [\"Unlimited liability clause\", \"Automatic renewal without notice\"],\n"
            "  \"contract_fairness_score\": 42,\n"
            "  \"score_explanation\": \"Several one-sided clauses and limited liability reduce fairness.\",\n"
            "  \"summary\": \"Short summary here.\"\n"
            "}\n"
        )

        response = ollama.chat(
            model='llama3.2',
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )
        
        return response['message']['content']
    except Exception as e:
        return f"Error processing with Ollama: {str(e)}"
