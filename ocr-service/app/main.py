import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="SecurFlow OCR & Document Processing Service",
    description="Microservice providing PyMuPDF + PaddleOCR extraction & field mismatch validation for FDRs",
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
    pipeline: list[str]

@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "healthy",
        "service": "securflow-ocr-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pipeline": [
            "digital_vs_scanned_pdf_detector",
            "pymupdf_parser",
            "paddleocr_engine",
            "structured_field_extractor",
            "confidence_scorer",
            "mismatch_validator"
        ]
    }

@app.get("/")
def root():
    return {
        "service": "SecurFlow OCR Extraction Service",
        "docs": "/docs",
        "health": "/health"
    }
