"""
Main FastAPI application for Car Lease Review AI Assistant
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API components
from api.routes import router

app = FastAPI(
    title="Car Lease Review AI Assistant",
    description="API for extracting and analyzing car lease contract facts",
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
app.include_router(router, prefix="/api/v1", tags=["contracts"])

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
    uvicorn.run(app, host="0.0.0.0", port=8000)