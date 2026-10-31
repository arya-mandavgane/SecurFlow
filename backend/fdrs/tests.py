from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from institutions.models import Institution
from fdrs.models import FDR, FDRDocument
from verification.models import VerificationRecord
from renewals.models import RenewalRecord
from releases.models import ReleaseRequest
from notifications.models import Notification, AlertRule
from audit.models import AuditLog
import datetime
import decimal

User = get_user_model()

class Phase1DataModelTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Indian Institute of Technology Bombay",
            aicte_id="1-999999999",
            state="Maharashtra",
            city="Mumbai",
            address="Powai, Mumbai - 400076",
            contact_person="Director Office",
            email="office@iitb.ac.in",
            phone="+91-22-25722545"
        )
        self.user = User.objects.create_user(
            username="testuser@iitb.ac.in",
            email="testuser@iitb.ac.in",
            password="TestPassword@2026",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )

    def test_user_roles(self):
        self.assertTrue(self.user.is_institution)
        self.assertFalse(self.user.is_official)
        self.assertFalse(self.user.is_admin_user)
        self.assertEqual(self.user.institution, self.institution)

    def test_fdr_lifecycle_and_creation(self):
        fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-TEST-001",
            bank_name="State Bank of India",
            branch="Powai",
            amount=decimal.Decimal("2500000.00"),
            interest_rate=decimal.Decimal("7.10"),
            issue_date=datetime.date(2025, 1, 1),
            maturity_date=datetime.date(2028, 1, 1),
            lien_marked_aicte=True,
            purpose_approval_cycle="Extension of Approval 2025-26",
            status=FDR.Status.SUBMITTED
        )
        self.assertEqual(fdr.status, FDR.Status.SUBMITTED)
        self.assertEqual(str(fdr), "FDR-TEST-001 - State Bank of India (₹2,500,000.00) [Submitted]")

        # Create FDR document
        doc = FDRDocument.objects.create(
            fdr=fdr,
            file_name="fdr_copy.pdf",
            file_type=FDRDocument.DocType.FDR_COPY,
            uploaded_by=self.user,
            checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size=102400
        )
        self.assertEqual(doc.fdr, fdr)
        self.assertEqual(fdr.documents.count(), 1)

    def test_verification_record(self):
        fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-TEST-002",
            bank_name="Punjab National Bank",
            branch="Delhi Main",
            amount=decimal.Decimal("1500000.00"),
            issue_date=datetime.date(2025, 1, 1),
            maturity_date=datetime.date(2028, 1, 1),
            status=FDR.Status.UNDER_REVIEW
        )
        record = VerificationRecord.objects.create(
            fdr=fdr,
            status=VerificationRecord.Status.APPROVED,
            remarks="Verified all parameters against original document",
            mismatches=[]
        )
        self.assertEqual(fdr.verification_records.first(), record)
        self.assertEqual(record.status, VerificationRecord.Status.APPROVED)

    def test_renewal_record(self):
        orig_fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-ORIG-001",
            bank_name="Canara Bank",
            branch="Bangalore",
            amount=decimal.Decimal("1000000.00"),
            issue_date=datetime.date(2022, 1, 1),
            maturity_date=datetime.date(2025, 1, 1),
            status=FDR.Status.EXPIRED
        )
        new_fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-NEW-001",
            bank_name="Canara Bank",
            branch="Bangalore",
            amount=decimal.Decimal("1000000.00"),
            issue_date=datetime.date(2025, 1, 1),
            maturity_date=datetime.date(2028, 1, 1),
            parent_fdr=orig_fdr,
            status=FDR.Status.RENEWED
        )
        renewal = RenewalRecord.objects.create(
            original_fdr=orig_fdr,
            new_fdr=new_fdr,
            renewal_type=RenewalRecord.RenewalType.RENEWAL,
            renewal_date=datetime.date(2025, 1, 1)
        )
        self.assertEqual(renewal.original_fdr, orig_fdr)
        self.assertEqual(renewal.new_fdr, new_fdr)
        self.assertEqual(new_fdr.parent_fdr, orig_fdr)

    def test_release_request(self):
        fdr = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-REL-001",
            bank_name="HDFC Bank",
            branch="Nariman Point",
            amount=decimal.Decimal("5000000.00"),
            issue_date=datetime.date(2020, 1, 1),
            maturity_date=datetime.date(2025, 1, 1),
            status=FDR.Status.ACTIVE
        )
        req = ReleaseRequest.objects.create(
            fdr=fdr,
            requested_by=self.user,
            reason="Completed 5-year lock-in period successfully.",
            status=ReleaseRequest.Status.REQUESTED
        )
        self.assertEqual(req.status, ReleaseRequest.Status.REQUESTED)
        self.assertEqual(fdr.release_requests.first(), req)

    def test_audit_log(self):
        log = AuditLog.objects.create(
            actor=self.user,
            action=AuditLog.Action.CREATE,
            entity_type="FDR",
            entity_id="999",
            before_state={},
            after_state={"amount": "2500000"},
            ip_address="127.0.0.1"
        )
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.action, AuditLog.Action.CREATE)

    def test_health_check_endpoint(self):
        client = Client()
        response = client.get('/api/health/')
        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['service'], 'securflow-backend')
        self.assertEqual(data['version'], '1.0.0')
        self.assertEqual(data['components']['database'], 'connected')
