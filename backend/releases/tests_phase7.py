import datetime
import decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from institutions.models import Institution
from fdrs.models import FDR
from releases.models import ReleaseRequest
from notifications.models import Notification


class Phase7ReleaseWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        today = datetime.date.today()

        # Institution
        self.institution = Institution.objects.create(
            name="VJTI Mumbai",
            aicte_id="1-4567890123",
            state="Maharashtra",
            city="Mumbai",
            email="principal@vjti.ac.in"
        )

        # Users
        self.inst_user = User.objects.create_user(
            username="vjti_admin",
            email="vjti@vjti.ac.in",
            password="Password123!",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )

        self.official_user = User.objects.create_user(
            username="aicte_evaluator",
            email="evaluator@aicte.gov.in",
            password="Password123!",
            role=User.Role.OFFICIAL,
            designation="Regional Officer, Western Regional Office"
        )

        # Eligible FDR (VERIFIED)
        self.fdr_eligible = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-VJTI-REL-01",
            bank_name="State Bank of India",
            branch="Matunga",
            amount=decimal.Decimal("5000000.00"),
            interest_rate=decimal.Decimal("7.20"),
            issue_date=today - datetime.timedelta(days=1800), # 5 years ago
            maturity_date=today + datetime.timedelta(days=30),
            lien_marked_aicte=True,
            purpose_approval_cycle="Establishment Obligation",
            status=FDR.Status.VERIFIED
        )

        # Ineligible FDR (SUBMITTED - not yet verified)
        self.fdr_ineligible = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-VJTI-REL-02",
            bank_name="Canara Bank",
            branch="Dadar",
            amount=decimal.Decimal("2500000.00"),
            interest_rate=decimal.Decimal("7.00"),
            issue_date=today - datetime.timedelta(days=10),
            maturity_date=today + datetime.timedelta(days=365),
            lien_marked_aicte=True,
            purpose_approval_cycle="Extension of Approval",
            status=FDR.Status.SUBMITTED
        )

    def test_release_eligibility_validation(self):
        self.client.force_authenticate(user=self.inst_user)

        # 1. Attempt to request release for ineligible (SUBMITTED) FDR -> MUST FAIL (400)
        res_fail = self.client.post('/api/releases/', {
            "fdr_id": self.fdr_ineligible.id,
            "reason": "Requesting release prematurely before verification"
        })
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not eligible for release', str(res_fail.data))

        # 2. Request release for eligible (VERIFIED) FDR -> MUST SUCCEED (201)
        res_ok = self.client.post('/api/releases/', {
            "fdr_id": self.fdr_eligible.id,
            "reason": "All academic obligations and 5-year lock-in period successfully completed."
        })
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)
        rel_id = res_ok.data['data']['id']

        self.fdr_eligible.refresh_from_db()
        self.assertEqual(self.fdr_eligible.status, FDR.Status.RELEASE_REQUESTED)

        # 3. Duplicate release request attempt -> MUST FAIL (400)
        res_dup = self.client.post('/api/releases/', {
            "fdr_id": self.fdr_eligible.id,
            "reason": "Second request for same deposit"
        })
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_official_decision_workflow_and_pdf_generation(self):
        # Create release request
        self.client.force_authenticate(user=self.inst_user)
        res_req = self.client.post('/api/releases/', {
            "fdr_id": self.fdr_eligible.id,
            "reason": "Mandatory 5-year lockin completed for approval"
        })
        rel_id = res_req.data['data']['id']

        # Official evaluates
        self.client.force_authenticate(user=self.official_user)

        # Cannot download letter before approval
        res_dl_early = self.client.get(f'/api/releases/{rel_id}/download-letter/')
        self.assertEqual(res_dl_early.status_code, status.HTTP_400_BAD_REQUEST)

        # Official approves
        decision_payload = {
            "action": "APPROVED",
            "official_remarks": "Compliance verified with regional bureau. Obligation period satisfied.",
            "checklist": {
                "cycle_completed": True,
                "no_pending_compliance": True,
                "lockin_satisfied": True
            }
        }
        res_dec = self.client.post(f'/api/releases/{rel_id}/decision/', data=decision_payload, format='json')
        self.assertEqual(res_dec.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dec.data['data']['status'], 'APPROVED')
        self.assertTrue(bool(res_dec.data['data']['refund_order_number']))

        # Official downloads Release Order PDF
        res_pdf = self.client.get(f'/api/releases/{rel_id}/download-letter/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pdf['content-type'], 'application/pdf')
        self.assertTrue(len(res_pdf.content) > 1000)
        self.assertTrue(b'%PDF' in res_pdf.content[:10])

        # Official executes release (mark as RELEASED)
        res_rel = self.client.post(f'/api/releases/{rel_id}/decision/', data={
            "action": "RELEASED",
            "official_remarks": "Lien discharged and credit instruction conveyed to SBI Matunga branch."
        }, format='json')
        self.assertEqual(res_rel.status_code, status.HTTP_200_OK)
        self.assertEqual(res_rel.data['data']['status'], 'RELEASED')

        self.fdr_eligible.refresh_from_db()
        self.assertEqual(self.fdr_eligible.status, FDR.Status.RELEASED)
        self.assertFalse(self.fdr_eligible.lien_marked_aicte)

    def test_invalid_state_transition_blocked(self):
        self.client.force_authenticate(user=self.inst_user)
        res_req = self.client.post('/api/releases/', {
            "fdr_id": self.fdr_eligible.id,
            "reason": "Lockin over"
        })
        rel_id = res_req.data['data']['id']

        self.client.force_authenticate(user=self.official_user)
        # Reject the request
        self.client.post(f'/api/releases/{rel_id}/decision/', {
            "action": "REJECTED",
            "official_remarks": "Pending vigilance case."
        }, format='json')

        # Attempt invalid jump from REJECTED to RELEASED -> MUST FAIL (400)
        res_inv = self.client.post(f'/api/releases/{rel_id}/decision/', {
            "action": "RELEASED",
            "official_remarks": "Bypassing review"
        }, format='json')
        self.assertEqual(res_inv.status_code, status.HTTP_400_BAD_REQUEST)
