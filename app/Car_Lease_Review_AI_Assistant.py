from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.contracts import router as contracts_router
from app.database import init_db

app = FastAPI(
    title="Car Lease Review AI Assistant",
    description="Milestone 1 – Upload, OCR, DB Storage, Fetch APIs",
    version="1.0"
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(upload_router, prefix="/contracts")
app.include_router(contracts_router, prefix="/contracts")

@app.get("/")
def home():
    return {"message": "Backend is running"}
