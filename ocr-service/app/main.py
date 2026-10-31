import json
import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from .jobs import job_store

app = FastAPI(
    title="SecurFlow OCR & Document Processing Service",
    description="Microservice providing PyMuPDF + OCR extraction & mismatch validation for Fixed Deposit Receipts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "securflow-ocr-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pipeline": [
            "digital_vs_scanned_pdf_detector",
            "pymupdf_parser",
            "structured_field_extractor",
            "confidence_scorer",
            "mismatch_validator",
            "job_retry_queue"
        ]
    }

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    submitted_data: Optional[str] = Form(None)
):
    """
    Asynchronously parses FDR PDF/image, extracts structured fields with confidence scores,
    and runs cross-validation against submitted institutional form data.
    """
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    parsed_submitted: Dict[str, Any] = {}
    if submitted_data:
        try:
            parsed_submitted = json.loads(submitted_data)
        except json.JSONDecodeError:
            parsed_submitted = {}

    job_result = job_store.create_job(
        filename=file.filename or "uploaded_fdr.pdf",
        file_bytes=file_bytes,
        submitted_data=parsed_submitted
    )
    return job_result

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Queries current processing state, extraction output, and flagged mismatches for an OCR job.
    """
    job = job_store.get_job_response(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' does not exist."
        )
    return job

@app.post("/jobs/{job_id}/retry")
def retry_job(job_id: str):
    """
    Retries extraction for a failed or low-confidence job.
    """
    job = job_store.retry_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' does not exist."
        )
    return job
