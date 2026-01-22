from fastapi import FastAPI
from app.database import engine, Base
from app.routers import analysis, chat

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Car Lease Review AI Assistant")

app.include_router(analysis.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Car Lease Review AI Assistant API"}
