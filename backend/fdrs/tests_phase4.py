import io
import datetime
import decimal
import fitz
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from institutions.models import Institution
from fdrs.models import FDR, FDRDocument
from fdrs.tasks import process_fdr_document_ocr
from verification.models import VerificationRecord
from audit.models import AuditLog

User = get_user_model()

class OCRBackendIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="VJTI Mumbai",
            aicte_id="1-109724121",
            state="Maharashtra"
        )
        self.user = User.objects.create_user(
            username="principal@vjti.ac.in",
            password="SecurFlow@2026",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )
        self.fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-2025-SBI-1001",
            bank_name="State Bank of India",
            branch="Matunga",
            amount=decimal.Decimal("2500000.00"),
            issue_date=datetime.date(2025, 1, 1),
            maturity_date=datetime.date(2028, 1, 1),
            lien_marked_aicte=True,
            purpose_approval_cycle="AICTE 2025-26",
            status=FDR.Status.SUBMITTED
        )

        # Create realistic digital PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (50, 72),
            "STATE BANK OF INDIA\nFIXED DEPOSIT RECEIPT\nFDR Number: FDR-2025-SBI-1001\n"
            "Deposit Amount: Rs. 2,500,000.00\nIssue Date: 01/01/2025\nMaturity Date: 01/01/2028\n"
            "Lien marked in favour of Member Secretary, AICTE New Delhi",
            fontsize=11
        )
        self.pdf_bytes = doc.tobytes()
        doc.close()

        self.fdr_doc = FDRDocument.objects.create(
            fdr=self.fdr,
            file=SimpleUploadedFile("fdr_certificate.pdf", self.pdf_bytes, content_type="application/pdf"),
            file_name="fdr_certificate.pdf",
            file_type=FDRDocument.DocType.FDR_COPY,
            uploaded_by=self.user,
            checksum="testchecksum123456",
            file_size=len(self.pdf_bytes),
            mime_type="application/pdf"
        )

    def test_process_fdr_document_ocr_task(self):
        # Run Celery task synchronously
        result = process_fdr_document_ocr(self.fdr_doc.id)
        self.assertTrue(result["success"])

        # Refresh FDR from DB
        self.fdr.refresh_from_db()
        self.assertEqual(self.fdr.status, FDR.Status.UNDER_REVIEW)
        self.assertIn("fdr_number", self.fdr.extracted_data)
        self.assertEqual(self.fdr.extracted_data["fdr_number"], "FDR-2025-SBI-1001")
        self.assertEqual(self.fdr.extracted_data["bank_name"], "State Bank of India")

        # Verify automated draft VerificationRecord was created
        draft_records = VerificationRecord.objects.filter(fdr=self.fdr, is_automated_draft=True)
        self.assertTrue(draft_records.exists())
        draft = draft_records.first()
        self.assertIn("Automated AI-OCR Document Analysis", draft.remarks)

        # Verify audit log
        ocr_audit = AuditLog.objects.filter(entity_type='FDR', entity_id=str(self.fdr.id), action=AuditLog.Action.VERIFY).first()
        self.assertIsNotNone(ocr_audit)

    def test_retrigger_ocr_api_endpoint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/fdrs/{self.fdr.id}/retrigger-ocr/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("extracted_data", response.data["data"])
