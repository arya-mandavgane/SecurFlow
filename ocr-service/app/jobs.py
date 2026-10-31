"""
Job management store for asynchronous OCR extraction tasks.
Tracks status, progress, extracted data, errors, and retry cycles.
"""
import uuid
import datetime
from typing import Dict, Any, Optional
from .extractor import extract_raw_text, extract_structured_fields
from .validator import validate_extracted_vs_submitted

class JobStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, filename: str, file_bytes: bytes, submitted_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        job = {
            "job_id": job_id,
            "filename": filename,
            "file_bytes": file_bytes,
            "submitted_data": submitted_data or {},
            "status": JobStatus.PENDING,
            "created_at": now,
            "updated_at": now,
            "retries": 0,
            "extracted_data": {},
            "mismatches": [],
            "error": None
        }
        self._jobs[job_id] = job
        
        # Execute extraction immediately
        self.process_job(job_id)
        return self.get_job_response(job_id)

    def process_job(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return

        job["status"] = JobStatus.PROCESSING
        job["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            # 1. Extract text and detect document type
            raw_text, doc_type = extract_raw_text(job["file_bytes"], job["filename"])
            
            # 2. Extract structured fields
            extracted = extract_structured_fields(raw_text, doc_type)
            
            # 3. Validate against submitted data
            mismatches = validate_extracted_vs_submitted(extracted, job["submitted_data"])

            job["status"] = JobStatus.COMPLETED
            job["extracted_data"] = extracted
            job["mismatches"] = mismatches
            job["error"] = None
        except Exception as e:
            job["status"] = JobStatus.FAILED
            job["error"] = str(e)

        job["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def get_job_response(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        # Return serializable copy omitting raw bytes
        return {
            "job_id": job["job_id"],
            "filename": job["filename"],
            "status": job["status"],
            "retries": job["retries"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "extracted_data": job["extracted_data"],
            "mismatches": job["mismatches"],
            "error": job["error"]
        }

    def retry_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        job["retries"] += 1
        self.process_job(job_id)
        return self.get_job_response(job_id)

job_store = JobStore()
