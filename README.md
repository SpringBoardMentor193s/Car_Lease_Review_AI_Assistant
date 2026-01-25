# Car Lease / Loan Contract Review & Negotiation AI Assistant

## Project Overview
This project is an AI-powered system that analyzes car lease and loan contracts using OCR, Large Language Models (Gemini), and public vehicle data APIs. It extracts key SLA terms, verifies vehicle information, and provides intelligent negotiation advice through a conversational AI assistant.

## Key Features
- OCR-based contract text extraction (Tesseract)
- LLM-powered SLA extraction using Google Gemini
- VIN verification using NHTSA public API
- AI-driven negotiation chatbot
- REST APIs exposed using FastAPI (Flutter-ready backend)

## Architecture
PDF Contract  
→ OCR (Tesseract)  
→ SQLite Database  
→ Gemini LLM (SLA Extraction)  
→ NHTSA API (Vehicle Data)  
→ Gemini LLM (Negotiation Chatbot)  
→ FastAPI → Flutter App

## Tech Stack
- Python, FastAPI
- Google Gemini (GenAI SDK)
- Tesseract OCR
- SQLite
- NHTSA Vehicle API

## API Endpoints
- `POST /process-contract` – Process contract PDF and extract SLA + vehicle data
- `POST /chat` – AI-powered negotiation assistant

