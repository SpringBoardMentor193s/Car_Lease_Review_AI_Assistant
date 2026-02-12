"""
Main FastAPI application for Car Lease Review AI Assistant
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to sys.path to allow importing negotiation_assistant
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Load environment variables
load_dotenv(root_dir / ".env")
load_dotenv(root_dir / "negotiation_assistant" / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API components
from api.routes import router as contract_router
from negotiation_assistant.api.routes import router as negotiation_router

app = FastAPI(
    title="Car Lease Review AI Assistant",
    description="API for extracting and analyzing car lease contract facts and providing negotiation assistance",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(contract_router, prefix="/api/v1", tags=["contracts"])
app.include_router(negotiation_router, prefix="/api/v1/negotiation", tags=["negotiation"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Car Lease Review AI Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)