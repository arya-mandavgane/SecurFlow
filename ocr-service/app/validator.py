"""
Validation engine comparing OCR extracted fields against submitted form data.
Flags severity-coded mismatches, missing lien clauses, and low-confidence fields.
"""
from typing import Dict, Any, List

def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    return str(text).strip().lower().replace('-', '').replace('/', '').replace(' ', '')

def validate_extracted_vs_submitted(extracted: Dict[str, Any], submitted: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates extracted OCR data against institution submission.
    Returns list of mismatch objects:
    [
        {
            "field": "amount",
            "submitted": "2500000.00",
            "ocr_found": "2000000.00",
            "severity": "CRITICAL",
            "issue": "Deposit amount discrepancy"
        }
    ]
    """
    mismatches = []

    if not submitted:
        return mismatches

    # 1. Amount Verification
    if 'amount' in submitted and submitted['amount']:
        try:
            sub_amt = float(submitted['amount'])
            ext_amt = float(extracted.get('amount', 0))
            if ext_amt > 0 and abs(sub_amt - ext_amt) > 0.01:
                mismatches.append({
                    "field": "amount",
                    "submitted": f"INR {sub_amt:,.2f}",
                    "ocr_found": f"INR {ext_amt:,.2f}",
                    "severity": "CRITICAL",
                    "issue": "Deposit amount in document does not match submitted value."
                })
        except (ValueError, TypeError):
            pass

    # 2. FDR Number Verification
    if 'fdr_number' in submitted and submitted['fdr_number']:
        sub_num = normalize_text(submitted['fdr_number'])
        ext_num = normalize_text(extracted.get('fdr_number', ''))
        if ext_num and sub_num != ext_num and (sub_num not in ext_num and ext_num not in sub_num):
            mismatches.append({
                "field": "fdr_number",
                "submitted": str(submitted['fdr_number']),
                "ocr_found": str(extracted.get('fdr_number', '')),
                "severity": "HIGH",
                "issue": "FDR Number printed on document does not match application."
            })

    # 3. Bank Name Verification
    if 'bank_name' in submitted and submitted['bank_name']:
        sub_bank = normalize_text(submitted['bank_name'])
        ext_bank = normalize_text(extracted.get('bank_name', ''))
        if ext_bank and sub_bank not in ext_bank and ext_bank not in sub_bank:
            mismatches.append({
                "field": "bank_name",
                "submitted": str(submitted['bank_name']),
                "ocr_found": str(extracted.get('bank_name', '')),
                "severity": "HIGH",
                "issue": "Issuing bank identified by OCR differs from submitted bank."
            })

    # 4. Maturity Date Verification
    if 'maturity_date' in submitted and submitted['maturity_date']:
        sub_mat = str(submitted['maturity_date']).strip()
        ext_mat = str(extracted.get('maturity_date', '')).strip()
        if ext_mat and normalize_text(sub_mat) != normalize_text(ext_mat):
            mismatches.append({
                "field": "maturity_date",
                "submitted": sub_mat,
                "ocr_found": ext_mat,
                "severity": "HIGH",
                "issue": "Maturity date discrepancy between document and form."
            })

    # 5. AICTE Lien / Pledge Verification
    sub_lien = bool(submitted.get('lien_marked_aicte', True))
    ext_lien = bool(extracted.get('lien_marked_aicte', False))
    if sub_lien and not ext_lien:
        mismatches.append({
            "field": "lien_marked_aicte",
            "submitted": "AICTE Lien Pledged",
            "ocr_found": "No AICTE Lien Clause Detected",
            "severity": "CRITICAL",
            "issue": "Mandatory AICTE joint lien clause was not found in document text."
        })

    # 6. Confidence Score Checks
    conf_scores = extracted.get('confidence_scores', {})
    for field_name, score in conf_scores.items():
        if field_name != 'overall' and score > 0 and score < 0.70:
            mismatches.append({
                "field": field_name,
                "submitted": str(submitted.get(field_name, 'N/A')),
                "ocr_found": str(extracted.get(field_name, 'Low Confidence')),
                "severity": "MEDIUM",
                "issue": f"OCR extraction confidence for {field_name} is below threshold ({int(score*100)}%). Manual inspection recommended."
            })

    return mismatches
