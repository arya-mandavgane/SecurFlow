import datetime
import decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from institutions.models import Institution
from fdrs.models import FDR
from notifications.models import Notification, AlertRule
from notifications.scanner import run_maturity_scan
from renewals.models import RenewalRecord


class Phase6AlertsAndRenewalsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        today = datetime.date.today()

        # Institution
        self.institution = Institution.objects.create(
            name="College of Engineering Pune",
            aicte_id="1-1122334455",
            state="Maharashtra",
            city="Pune",
            email="principal@coep.ac.in",
            phone="020-25507000"
        )

        # Users
        self.inst_user = User.objects.create_user(
            username="coep_user",
            email="admin@coep.ac.in",
            password="Password123!",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )

        self.official_user = User.objects.create_user(
            username="official_scan",
            email="official_scan@aicte.gov.in",
            password="Password123!",
            role=User.Role.OFFICIAL
        )

        # FDR 1: Active, matures in 25 days -> Should become EXPIRING_SOON
        self.fdr_expiring = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-COEP-001",
            bank_name="Bank of Maharashtra",
            branch="Shivajinagar",
            amount=decimal.Decimal("3000000.00"),
            interest_rate=decimal.Decimal("7.10"),
            issue_date=today - datetime.timedelta(days=340),
            maturity_date=today + datetime.timedelta(days=25),
            lien_marked_aicte=True,
            purpose_approval_cycle="New Course PG",
            status=FDR.Status.ACTIVE
        )

        # FDR 2: Active, matured 5 days ago -> Should become EXPIRED
        self.fdr_expired = FDR.objects.create(
            institution=self.institution,
            fdr_number="FDR-COEP-002",
            bank_name="State Bank of India",
            branch="Pune Camp",
            amount=decimal.Decimal("2000000.00"),
            interest_rate=decimal.Decimal("6.90"),
            issue_date=today - datetime.timedelta(days=370),
            maturity_date=today - datetime.timedelta(days=5),
            lien_marked_aicte=True,
            purpose_approval_cycle="Extension of Approval",
            status=FDR.Status.ACTIVE
        )

    def test_maturity_scanner_and_idempotency(self):
        # 1. Run first scan
        res1 = run_maturity_scan()
        self.fdr_expiring.refresh_from_db()
        self.fdr_expired.refresh_from_db()

        self.assertEqual(self.fdr_expiring.status, FDR.Status.EXPIRING_SOON)
        self.assertEqual(self.fdr_expired.status, FDR.Status.EXPIRED)
        self.assertTrue(res1['notifications_created'] >= 2)

        count_after_scan1 = Notification.objects.filter(
            fdr__in=[self.fdr_expiring, self.fdr_expired],
            channel=Notification.Channel.IN_APP
        ).count()
        self.assertEqual(count_after_scan1, 2)

        # 2. Run scan second time (Idempotency test)
        res2 = run_maturity_scan()
        count_after_scan2 = Notification.objects.filter(
            fdr__in=[self.fdr_expiring, self.fdr_expired],
            channel=Notification.Channel.IN_APP
        ).count()

        # No duplicate notifications should be created!
        self.assertEqual(count_after_scan1, count_after_scan2)
        self.assertEqual(res2['notifications_created'], 0)

    def test_notification_endpoints(self):
        # Create a test notification
        notif = Notification.objects.create(
            institution=self.institution,
            fdr=self.fdr_expiring,
            title="Test Reminder",
            message="Please renew soon",
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT,
            is_read=False
        )

        self.client.force_authenticate(user=self.inst_user)

        # Check unread count
        res_count = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(res_count.status_code, status.HTTP_200_OK)
        self.assertEqual(res_count.data['data']['unread_count'], 1)

        # Mark single as read
        res_read = self.client.post(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(res_read.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # Mark all as read
        Notification.objects.create(
            institution=self.institution,
            fdr=self.fdr_expired,
            title="Another notification",
            message="Expired FDR",
            channel=Notification.Channel.IN_APP,
            is_read=False
        )
        res_all = self.client.post('/api/notifications/mark-all-read/')
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_all.data['data']['updated_count'], 1)

    def test_renewal_submission_and_chain(self):
        self.client.force_authenticate(user=self.inst_user)
        today = datetime.date.today()

        payload = {
            "original_fdr_id": self.fdr_expired.id,
            "renewal_type": RenewalRecord.RenewalType.RENEWAL,
            "reason": "Annual compliance renewal as mandated by AICTE",
            "fdr_number": "FDR-COEP-002-R1",
            "bank_name": "State Bank of India",
            "branch": "Pune Camp",
            "amount": "2000000.00",
            "interest_rate": "7.50",
            "issue_date": str(today),
            "maturity_date": str(today + datetime.timedelta(days=365)),
            "lien_marked_aicte": True
        }

        res = self.client.post('/api/renewals/submit/', data=payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_fdr_id = res.data['data']['new_fdr']['id']

        # Verify RenewalRecord created
        rec = RenewalRecord.objects.get(original_fdr=self.fdr_expired, new_fdr_id=new_fdr_id)
        self.assertEqual(rec.renewal_type, RenewalRecord.RenewalType.RENEWAL)

        # Verify Lineage Chain
        res_chain = self.client.get(f'/api/renewals/{new_fdr_id}/chain/')
        self.assertEqual(res_chain.status_code, status.HTTP_200_OK)
        lineage = res_chain.data['data']['lineage']
        self.assertEqual(len(lineage), 2)
        self.assertEqual(lineage[0]['fdr_number'], 'FDR-COEP-002')
        self.assertEqual(lineage[1]['fdr_number'], 'FDR-COEP-002-R1')

        # Official approves the renewed FDR -> Parent FDR status must update to RENEWED
        self.client.force_authenticate(user=self.official_user)
        verify_payload = {
            "action": "APPROVE",
            "remarks": "Renewal certificate verified against SBI bank branch advice."
        }
        res_verify = self.client.post(f'/api/fdrs/{new_fdr_id}/verify/', data=verify_payload, format='json')
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)

        self.fdr_expired.refresh_from_db()
        self.assertEqual(self.fdr_expired.status, FDR.Status.RENEWED)
