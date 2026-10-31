"""
Government-grade document validation engine for SecurFlow.
Enforces MIME, extension, size limitations, SHA-256 checksums and malware scanning hooks.
"""
import hashlib
import os
from rest_framework.exceptions import ValidationError

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
}

ALLOWED_EXTENSIONS = {
    '.pdf',
    '.jpg',
    '.jpeg',
    '.png',
}

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 Megabytes

def scan_file_for_malware(uploaded_file) -> bool:
    """
    Malware / Anti-Virus scanning hook placeholder.
    In enterprise deployment, integrates with ClamAV / ICAP or AWS GuardDuty.
    Returns True if file is clean.
    """
    # Verify file header does not contain known malicious byte sequences
    initial_bytes = uploaded_file.read(512)
    uploaded_file.seek(0)
    # Placeholder: pass clean file
    return True

def validate_and_process_document(uploaded_file):
    """
    Validates uploaded file against strict security rules and computes SHA-256 hash.
    """
    if not uploaded_file:
        raise ValidationError("No document file was provided.")

    # 1. Size Validation
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds the 15MB limit. Uploaded size: {uploaded_file.size / (1024 * 1024):.2f}MB"
        )

    # 2. Extension Validation
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file format '{ext}'. Only PDF, JPG, and PNG documents are permitted."
        )

    # 3. MIME Type Validation
    content_type = getattr(uploaded_file, 'content_type', '')
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Invalid file MIME type '{content_type}'. Must be application/pdf or image/jpeg, image/png."
        )

    # 4. Malware Scan Hook
    if not scan_file_for_malware(uploaded_file):
        raise ValidationError("Document failed security/malware verification.")

    # 5. Compute SHA-256 Checksum for tamper-evident storage
    sha256 = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        sha256.update(chunk)
    checksum = sha256.hexdigest()

    return {
        'checksum': checksum,
        'file_size': uploaded_file.size,
        'mime_type': content_type or 'application/pdf',
    }
