import datetime
import decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from institutions.models import Institution
from fdrs.models import FDR, FDRDocument
from verification.models import VerificationRecord
from audit.models import AuditLog


class Phase5OfficialVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Institution
        self.institution = Institution.objects.create(
            name="Delhi Institute of Advanced Technology",
            aicte_id="1-9988776655",
            state="Delhi",
            city="New Delhi",
            contact_person="Dr. A. Verma",
            email="info@diat.edu.in",
            phone="011-23456789"
        )

        # Create Users
        self.inst_user = User.objects.create_user(
            username="inst_user",
            email="inst@diat.edu.in",
            password="Password123!",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )

        self.official_user = User.objects.create_user(
            username="official_aicte",
            email="official@aicte.gov.in",
            password="Password123!",
            role=User.Role.OFFICIAL,
            designation="Assistant Director"
        )

        # Create FDRs with different states
        today = datetime.date.today()
        self.fdr1 = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-DEL-001",
            bank_name="State Bank of India",
            branch="Connaught Place",
            amount=decimal.Decimal("2500000.00"),
            interest_rate=decimal.Decimal("7.25"),
            issue_date=today - datetime.timedelta(days=100),
            maturity_date=today + datetime.timedelta(days=20), # expiring in 20 days
            lien_marked_aicte=True,
            purpose_approval_cycle="Extension of Approval 2024-25",
            status=FDR.Status.SUBMITTED,
            extracted_data={
                "discrepancies": [
                    {"field": "amount", "severity": "CRITICAL", "issue": "Amount mismatch between form and certificate"}
                ],
                "overall_confidence": 0.82
            }
        )

        self.fdr2 = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-DEL-002",
            bank_name="Punjab National Bank",
            branch="Karol Bagh",
            amount=decimal.Decimal("1500000.00"),
            interest_rate=decimal.Decimal("6.75"),
            issue_date=today - datetime.timedelta(days=200),
            maturity_date=today + datetime.timedelta(days=180),
            lien_marked_aicte=True,
            purpose_approval_cycle="New Course Addition",
            status=FDR.Status.VERIFIED
        )

    def test_official_stats_endpoint(self):
        # Institution user should be forbidden
        self.client.force_authenticate(user=self.inst_user)
        res_inst = self.client.get('/api/fdrs/official-stats/')
        self.assertEqual(res_inst.status_code, status.HTTP_403_FORBIDDEN)

        # Official user can access stats
        self.client.force_authenticate(user=self.official_user)
        res = self.client.get('/api/fdrs/official-stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']

        kpis = data['kpis']
        self.assertEqual(kpis['total_fdrs'], 2)
        self.assertEqual(kpis['pending_verification'], 1)
        self.assertEqual(kpis['verified'], 1)
        self.assertEqual(kpis['expiring_30_days'], 1)

        self.assertTrue(len(data['status_distribution']) >= 2)
        self.assertTrue(len(data['state_distribution']) >= 1)
        self.assertTrue(len(data['bank_distribution']) >= 2)

    def test_verification_queue_priority_and_filtering(self):
        self.client.force_authenticate(user=self.official_user)
        res = self.client.get('/api/fdrs/verification-queue/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data['data']
        self.assertEqual(len(items), 1)

        # FDR1 has CRITICAL discrepancy and 20 days to maturity -> HIGH priority
        item = items[0]
        self.assertEqual(item['fdr_number'], 'FDR-DEL-001')
        self.assertEqual(item['priority'], 'HIGH')
        self.assertTrue(item['has_critical_discrepancy'])

        # Filter by priority
        res_high = self.client.get('/api/fdrs/verification-queue/?priority=HIGH')
        self.assertEqual(len(res_high.data['data']), 1)

        res_low = self.client.get('/api/fdrs/verification-queue/?priority=LOW')
        self.assertEqual(len(res_low.data['data']), 0)

    def test_smart_verification_with_field_overrides(self):
        self.client.force_authenticate(user=self.official_user)

        # Official verifies FDR and corrects the amount via field override
        payload = {
            'action': 'APPROVE',
            'remarks': 'Certificate verified directly with bank branch manager. Corrected amount confirmed.',
            'mismatches': [],
            'field_overrides': {
                'amount': '2600000.00'
            }
        }
        res = self.client.post(f'/api/fdrs/{self.fdr1.id}/verify/', data=payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.fdr1.refresh_from_db()
        self.assertEqual(self.fdr1.status, FDR.Status.VERIFIED)
        self.assertEqual(self.fdr1.amount, decimal.Decimal('2600000.00'))

        # Check VerificationRecord
        v_record = self.fdr1.verification_records.first()
        self.assertIsNotNone(v_record)
        self.assertEqual(v_record.status, VerificationRecord.Status.APPROVED)
        self.assertEqual(v_record.official, self.official_user)

        # Check Audit Log recorded the override
        audit_entry = AuditLog.objects.filter(entity_type='FDR', entity_id=str(self.fdr1.id)).last()
        self.assertIsNotNone(audit_entry)

    def test_ai_summary_hook(self):
        self.client.force_authenticate(user=self.official_user)
        res = self.client.post(f'/api/fdrs/{self.fdr1.id}/ai-summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(data['fdr_id'], self.fdr1.id)
        self.assertEqual(data['recommendation'], 'REQUEST_CLARIFICATION') # Due to critical mismatch
        self.assertIn('critical', data['summary'].lower())

    def test_institution_fdr_history_endpoint(self):
        self.client.force_authenticate(user=self.official_user)
        res = self.client.get(f'/api/institutions/{self.institution.id}/fdrs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(data['summary']['total_fdrs'], 2)
        self.assertEqual(len(data['fdrs']), 2)

    def test_fdr_audit_trail_endpoint(self):
        self.client.force_authenticate(user=self.official_user)
        res = self.client.get(f'/api/fdrs/{self.fdr1.id}/audit-trail/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(res.data['data'], list))
