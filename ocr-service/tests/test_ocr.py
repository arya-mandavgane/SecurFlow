import io
import fitz
from fastapi.testclient import TestClient
from app.main import app
from app.extractor import extract_raw_text, extract_structured_fields, detect_pdf_type
from app.validator import validate_extracted_vs_submitted
from app.jobs import job_store

client = TestClient(app)

def create_sample_digital_pdf(text_content: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text_content, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_digital_pdf_field_extraction():
    sample_text = """
    STATE BANK OF INDIA
    FIXED DEPOSIT RECEIPT
    FDR Number: FDR-2025-MH-998877
    Branch: Matunga East, Mumbai
    Deposit Amount: Rs. 2,500,000.00
    Interest Rate: 7.10% p.a.
    Issue Date: 15/01/2025
    Maturity Date: 15/01/2028
    Lien Clause: Lien marked in favour of Member Secretary, AICTE New Delhi
    """
    pdf_bytes = create_sample_digital_pdf(sample_text)
    raw_text, doc_type = extract_raw_text(pdf_bytes, "sample_fdr.pdf")
    assert doc_type == "digital"
    assert "STATE BANK OF INDIA" in raw_text

    extracted = extract_structured_fields(raw_text, doc_type)
    assert extracted["fdr_number"] == "FDR-2025-MH-998877"
    assert extracted["bank_name"] == "State Bank of India"
    assert extracted["amount"] == 2500000.0
    assert extracted["interest_rate"] == 7.10
    assert extracted["lien_marked_aicte"] is True
    assert extracted["confidence_scores"]["amount"] > 0.90
    assert extracted["confidence_scores"]["fdr_number"] > 0.90

def test_mismatch_and_missing_lien_detection():
    extracted = {
        "fdr_number": "FDR-2025-MH-998877",
        "bank_name": "State Bank of India",
        "amount": 2000000.0, # 20 Lakhs in document
        "maturity_date": "15/01/2028",
        "lien_marked_aicte": False, # No lien detected
        "confidence_scores": {"overall": 0.88}
    }
    submitted = {
        "fdr_number": "FDR-2025-MH-998877",
        "bank_name": "State Bank of India",
        "amount": "2500000.00", # 25 Lakhs submitted
        "maturity_date": "15/01/2028",
        "lien_marked_aicte": True, # Institutional claim
    }

    mismatches = validate_extracted_vs_submitted(extracted, submitted)
    mismatch_fields = [m["field"] for m in mismatches]
    
    # 1. Amount mismatch flagged CRITICAL
    assert "amount" in mismatch_fields
    amt_issue = next(m for m in mismatches if m["field"] == "amount")
    assert amt_issue["severity"] == "CRITICAL"

    # 2. Missing AICTE Lien flagged CRITICAL
    assert "lien_marked_aicte" in mismatch_fields
    lien_issue = next(m for m in mismatches if m["field"] == "lien_marked_aicte")
    assert lien_issue["severity"] == "CRITICAL"

def test_api_extract_endpoint_and_job_lifecycle():
    sample_text = """
    PUNJAB NATIONAL BANK
    Term Deposit Advice / FDR
    FDR Number: FDR-2025-DL-554433
    Deposit Amount: INR 1,500,000.00
    Maturity Date: 01/02/2028
    Pledged to AICTE
    """
    pdf_bytes = create_sample_digital_pdf(sample_text)
    
    # POST /extract
    response = client.post(
        "/extract",
        files={"file": ("pnb_fdr.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"submitted_data": '{"fdr_number": "FDR-2025-DL-554433", "amount": "1500000.00", "bank_name": "Punjab National Bank", "lien_marked_aicte": true}'}
    )
    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]
    assert data["status"] == "COMPLETED"
    assert data["extracted_data"]["bank_name"] == "Punjab National Bank"
    assert data["extracted_data"]["amount"] == 1500000.0
    assert len(data["mismatches"]) == 0

    # GET /jobs/{id}
    status_res = client.get(f"/jobs/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["job_id"] == job_id

    # POST /jobs/{id}/retry
    retry_res = client.post(f"/jobs/{job_id}/retry")
    assert retry_res.status_code == 200
    assert retry_res.json()["retries"] == 1
