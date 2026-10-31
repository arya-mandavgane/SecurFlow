import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="SecurFlow AI Assistant & RAG Service",
    description="Microservice powering AICTE Guideline Search and Authorized FDR Status Assistance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    features: list[str]

@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "healthy",
        "service": "securflow-ai-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "features": [
            "pgvector_rag_retrieval",
            "aicte_guidelines_qa",
            "rbac_fdr_status_assistant",
            "summarization_hook"
        ]
    }

@app.get("/")
def root():
    return {
        "service": "SecurFlow AI Assistant Service",
        "docs": "/docs",
        "health": "/health"
    }
