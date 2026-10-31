from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from institutions.models import Institution
from fdrs.models import FDR, FDRDocument
from verification.models import VerificationRecord
from notifications.models import Notification
from audit.models import AuditLog
import datetime
import decimal

User = get_user_model()

class FDRAndRBACAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Institution A (VJTI)
        self.inst_a = Institution.objects.create(
            name="VJTI Mumbai",
            aicte_id="1-109724121",
            state="Maharashtra",
            email="principal@vjti.ac.in",
            phone="+91-22-24198101",
            address="Matunga, Mumbai"
        )
        self.user_a = User.objects.create_user(
            username="vjti_user",
            email="principal@vjti.ac.in",
            password="SecurFlow@2026",
            role=User.Role.INSTITUTION,
            institution=self.inst_a
        )

        # Institution B (COEP)
        self.inst_b = Institution.objects.create(
            name="COEP Pune",
            aicte_id="1-109823451",
            state="Maharashtra",
            email="registrar@coep.ac.in",
            phone="+91-20-25507000",
            address="Shivajinagar, Pune"
        )
        self.user_b = User.objects.create_user(
            username="coep_user",
            email="registrar@coep.ac.in",
            password="SecurFlow@2026",
            role=User.Role.INSTITUTION,
            institution=self.inst_b
        )

        # AICTE Official
        self.official = User.objects.create_user(
            username="official1@aicte.gov.in",
            email="official1@aicte.gov.in",
            password="SecurFlow@2026",
            role=User.Role.OFFICIAL,
            is_staff=True
        )

        # Admin
        self.admin = User.objects.create_user(
            username="admin@aicte.gov.in",
            email="admin@aicte.gov.in",
            password="SecurFlow@2026",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Create an FDR belonging to Institution A
        self.fdr_a = FDR.objects.create(
            institution=self.inst_a,
            fdr_number="FDR-VJTI-001",
            bank_name="State Bank of India",
            branch="Matunga",
            amount=decimal.Decimal("2500000.00"),
            issue_date=datetime.date(2025, 1, 1),
            maturity_date=datetime.date(2028, 1, 1),
            lien_marked_aicte=True,
            purpose_approval_cycle="Approval 2025-26",
            status=FDR.Status.SUBMITTED
        )

    # -------------------------------------------------------------
    # RBAC ACCEPTANCE CRITERIA TESTS
    # -------------------------------------------------------------
    def test_institution_user_only_sees_own_fdrs(self):
        # Institution A sees FDR A
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get('/api/fdrs/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        fdr_numbers = [item['fdr_number'] for item in res_a.data['results']]
        self.assertIn("FDR-VJTI-001", fdr_numbers)

        # Institution B DOES NOT see FDR A
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get('/api/fdrs/')
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        fdr_numbers_b = [item['fdr_number'] for item in res_b.data['results']]
        self.assertNotIn("FDR-VJTI-001", fdr_numbers_b)

    def test_institution_b_cannot_retrieve_institution_a_fdr(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(f'/api/fdrs/{self.fdr_a.id}/')
        # Scoped queryset returns 404 for records outside user's institution
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_institution_b_cannot_modify_institution_a_fdr(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.patch(f'/api/fdrs/{self.fdr_a.id}/', {'amount': '3000000.00'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_official_can_see_all_institutions_fdrs(self):
        self.client.force_authenticate(user=self.official)
        response = self.client.get('/api/fdrs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fdr_numbers = [item['fdr_number'] for item in response.data['results']]
        self.assertIn("FDR-VJTI-001", fdr_numbers)

    # -------------------------------------------------------------
    # FDR CRUD & STATE AUDITING TESTS
    # -------------------------------------------------------------
    def test_create_fdr_and_audit_logging(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'fdr_number': 'FDR-VJTI-NEW',
            'bank_name': 'Punjab National Bank',
            'branch': 'Dadar',
            'amount': '1500000.00',
            'interest_rate': '7.25',
            'issue_date': '2025-02-01',
            'maturity_date': '2028-02-01',
            'lien_marked_aicte': True,
            'purpose_approval_cycle': 'Extension 2025-26',
        }
        response = self.client.post('/api/fdrs/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        fdr_id = response.data['id']

        # Verify auto-assigned institution and status
        created_fdr = FDR.objects.get(id=fdr_id)
        self.assertEqual(created_fdr.institution, self.inst_a)
        self.assertEqual(created_fdr.status, FDR.Status.SUBMITTED)

        # Check Audit Log written
        audit_log = AuditLog.objects.filter(entity_type='FDR', entity_id=str(fdr_id), action=AuditLog.Action.CREATE).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.actor, self.user_a)

    def test_maturity_date_must_be_after_issue_date(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'fdr_number': 'FDR-VJTI-INVALID',
            'bank_name': 'HDFC Bank',
            'branch': 'Mumbai',
            'amount': '1000000.00',
            'issue_date': '2025-05-01',
            'maturity_date': '2024-05-01', # Prior to issue date
            'lien_marked_aicte': True,
            'purpose_approval_cycle': 'Approval 2025-26',
        }
        response = self.client.post('/api/fdrs/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------
    # OFFICIAL VERIFICATION ACTIONS TESTS
    # -------------------------------------------------------------
    def test_official_can_approve_fdr(self):
        self.client.force_authenticate(user=self.official)
        payload = {
            'action': 'APPROVE',
            'remarks': 'All FDR parameters and AICTE pledge confirmed valid.',
            'mismatches': []
        }
        response = self.client.post(f'/api/fdrs/{self.fdr_a.id}/verify/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.fdr_a.refresh_from_db()
        self.assertEqual(self.fdr_a.status, FDR.Status.VERIFIED)

        # Verify VerificationRecord was created
        record = self.fdr_a.verification_records.first()
        self.assertIsNotNone(record)
        self.assertEqual(record.status, VerificationRecord.Status.APPROVED)
        self.assertEqual(record.official, self.official)

        # Verify Notification was dispatched
        notif = Notification.objects.filter(fdr=self.fdr_a, institution=self.inst_a).first()
        self.assertIsNotNone(notif)
        self.assertIn("Verified", notif.title)

        # Verify Audit Log
        verify_log = AuditLog.objects.filter(entity_type='FDR', entity_id=str(self.fdr_a.id), action=AuditLog.Action.VERIFY).first()
        self.assertIsNotNone(verify_log)

    def test_official_can_request_clarification(self):
        self.client.force_authenticate(user=self.official)
        payload = {
            'action': 'REQUEST_CLARIFICATION',
            'remarks': 'Bank letter scan is illegible. Please re-upload.',
            'mismatches': [{'field': 'bank_letter', 'issue': 'illegible'}]
        }
        response = self.client.post(f'/api/fdrs/{self.fdr_a.id}/verify/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.fdr_a.refresh_from_db()
        self.assertEqual(self.fdr_a.status, FDR.Status.NEEDS_CLARIFICATION)

    def test_institution_user_cannot_perform_verification(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {'action': 'APPROVE', 'remarks': 'Self approving attempt'}
        response = self.client.post(f'/api/fdrs/{self.fdr_a.id}/verify/', payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------
    # SECURE DOCUMENT UPLOAD TESTS
    # -------------------------------------------------------------
    def test_document_upload_success_and_checksum(self):
        self.client.force_authenticate(user=self.user_a)
        fake_pdf = SimpleUploadedFile(
            "fdr_copy.pdf",
            b"%PDF-1.4 Mock FDR Content for AICTE Submission",
            content_type="application/pdf"
        )
        response = self.client.post(
            f'/api/fdrs/{self.fdr_a.id}/documents/',
            {'file': fake_pdf, 'file_type': 'FDR_COPY'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('checksum', response.data['data'])
        self.assertEqual(len(response.data['data']['checksum']), 64) # SHA-256 length

        # Check Audit Log
        doc_id = response.data['data']['id']
        audit_log = AuditLog.objects.filter(entity_type='FDRDocument', entity_id=str(doc_id)).first()
        self.assertIsNotNone(audit_log)

    def test_document_upload_rejects_disallowed_extension(self):
        self.client.force_authenticate(user=self.user_a)
        bad_file = SimpleUploadedFile("script.exe", b"binary executable", content_type="application/x-msdownload")
        response = self.client.post(
            f'/api/fdrs/{self.fdr_a.id}/documents/',
            {'file': bad_file, 'file_type': 'OTHER'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
