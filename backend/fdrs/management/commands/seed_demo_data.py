import datetime
import decimal
import hashlib
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from institutions.models import Institution
from fdrs.models import FDR, FDRDocument
from verification.models import VerificationRecord
from renewals.models import RenewalRecord
from releases.models import ReleaseRequest
from notifications.models import Notification, AlertRule
from audit.models import AuditLog

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds realistic demo institutions, FDRs across all lifecycle statuses, users and alert rules"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting SecurFlow demo data seeding..."))

        # 1. Create Users
        default_pwd = "SecurFlow@2026"
        
        admin_user, _ = User.objects.get_or_create(
            username="admin@aicte.gov.in",
            defaults={
                "email": "admin@aicte.gov.in",
                "role": User.Role.ADMIN,
                "first_name": "Portal",
                "last_name": "Administrator",
                "designation": "AICTE System Admin",
                "phone_number": "+91-11-29581000",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password(default_pwd)
        admin_user.save()

        official_1, _ = User.objects.get_or_create(
            username="official1@aicte.gov.in",
            defaults={
                "email": "official1@aicte.gov.in",
                "role": User.Role.OFFICIAL,
                "first_name": "Dr. Rajesh",
                "last_name": "Sharma",
                "designation": "Joint Director (Approvals)",
                "phone_number": "+91-11-29581015",
                "is_staff": True,
            }
        )
        official_1.set_password(default_pwd)
        official_1.save()

        official_2, _ = User.objects.get_or_create(
            username="official2@aicte.gov.in",
            defaults={
                "email": "official2@aicte.gov.in",
                "role": User.Role.OFFICIAL,
                "first_name": "Smt. Priya",
                "last_name": "Nair",
                "designation": "Deputy Director (Finance & FDR)",
                "phone_number": "+91-11-29581022",
                "is_staff": True,
            }
        )
        official_2.set_password(default_pwd)
        official_2.save()

        self.stdout.write(self.style.SUCCESS(f"Created Admin and Official accounts."))

        # 2. Seed 15 Realistic Institutions
        institutions_raw = [
            {
                "name": "Veermata Jijabai Technological Institute (VJTI)",
                "aicte_id": "1-109724121",
                "state": "Maharashtra",
                "city": "Mumbai",
                "address": "H. R. Mahajani Road, Matunga East, Mumbai - 400019",
                "contact_person": "Dr. S. K. Mahajan (Director)",
                "email": "principal@vjti.ac.in",
                "phone": "+91-22-24198101",
            },
            {
                "name": "College of Engineering Pune (COEP) Technological University",
                "aicte_id": "1-109823451",
                "state": "Maharashtra",
                "city": "Pune",
                "address": "Wellesley Road, Shivajinagar, Pune - 411005",
                "contact_person": "Prof. D. N. Sonawane (Registrar)",
                "email": "registrar@coep.ac.in",
                "phone": "+91-20-25507000",
            },
            {
                "name": "International Institute of Information Technology Bangalore (IIIT-B)",
                "aicte_id": "1-205128911",
                "state": "Karnataka",
                "city": "Bengaluru",
                "address": "26/C, Electronic City Phase 1, Hosur Road, Bengaluru - 560100",
                "contact_person": "Prof. Debabrata Das (Director)",
                "email": "director@iiitb.ac.in",
                "phone": "+91-80-41407777",
            },
            {
                "name": "PES University",
                "aicte_id": "1-208934112",
                "state": "Karnataka",
                "city": "Bengaluru",
                "address": "100 Feet Ring Road, BSK III Stage, Bengaluru - 560085",
                "contact_person": "Dr. J. Suryaprasad (Vice Chancellor)",
                "email": "dean@pes.edu",
                "phone": "+91-80-26721983",
            },
            {
                "name": "R.V. College of Engineering (RVCE)",
                "aicte_id": "1-213456789",
                "state": "Karnataka",
                "city": "Bengaluru",
                "address": "Mysore Road, RV Vidyanikethan Post, Bengaluru - 560059",
                "contact_person": "Dr. K. N. Subramanya (Principal)",
                "email": "principal@rvce.edu.in",
                "phone": "+91-80-68188111",
            },
            {
                "name": "Netaji Subhas University of Technology (NSUT)",
                "aicte_id": "1-301298451",
                "state": "Delhi",
                "city": "New Delhi",
                "address": "Sector 3, Dwarka, New Delhi - 110078",
                "contact_person": "Prof. Anand Srivastava (Vice Chancellor)",
                "email": "contact@nsut.ac.in",
                "phone": "+91-11-25000268",
            },
            {
                "name": "Delhi Technological University (DTU)",
                "aicte_id": "1-304561234",
                "state": "Delhi",
                "city": "New Delhi",
                "address": "Shahbad Daulatpur, Bawana Road, Delhi - 110042",
                "contact_person": "Prof. Prateek Sharma (Vice Chancellor)",
                "email": "admin@dtu.ac.in",
                "phone": "+91-11-27871018",
            },
            {
                "name": "Institute of Chemical Technology (ICT Mumbai)",
                "aicte_id": "1-105678234",
                "state": "Maharashtra",
                "city": "Mumbai",
                "address": "Nathalal Parekh Marg, Matunga, Mumbai - 400019",
                "contact_person": "Prof. A. B. Pandit (Vice Chancellor)",
                "email": "director@ictmumbai.edu.in",
                "phone": "+91-22-33611111",
            },
            {
                "name": "PSG College of Technology",
                "aicte_id": "1-401239871",
                "state": "Tamil Nadu",
                "city": "Coimbatore",
                "address": "Avinashi Road, Peelamedu, Coimbatore - 641004",
                "contact_person": "Dr. K. Prakasan (Principal)",
                "email": "principal@psgtech.edu",
                "phone": "+91-422-2572177",
            },
            {
                "name": "Chennai Institute of Technology",
                "aicte_id": "1-406789123",
                "state": "Tamil Nadu",
                "city": "Chennai",
                "address": "SH-113, Sarathy Nagar, Kundrathur, Chennai - 600069",
                "contact_person": "Dr. A. Ramesh (Principal)",
                "email": "director@citchennai.edu.in",
                "phone": "+91-44-71119111",
            },
            {
                "name": "Thapar Institute of Engineering & Technology",
                "aicte_id": "1-501234987",
                "state": "Punjab",
                "city": "Patiala",
                "address": "Bhadson Road, Adarsh Nagar, Patiala - 147004",
                "contact_person": "Dr. Padmakumar Nair (Director)",
                "email": "dean@thapar.edu",
                "phone": "+91-175-2393021",
            },
            {
                "name": "BMS College of Engineering (BMSCE)",
                "aicte_id": "1-218765432",
                "state": "Karnataka",
                "city": "Bengaluru",
                "address": "Bull Temple Road, Basavanagudi, Bengaluru - 560019",
                "contact_person": "Dr. S. Muralidhara (Principal)",
                "email": "director@bmsce.ac.in",
                "phone": "+91-80-26622130",
            },
            {
                "name": "Sardar Patel Institute of Technology (SPIT)",
                "aicte_id": "1-112345678",
                "state": "Maharashtra",
                "city": "Mumbai",
                "address": "Bhavans Campus, Munshi Nagar, Andheri West, Mumbai - 400058",
                "contact_person": "Dr. B. N. Chaudhari (Principal)",
                "email": "principal@spit.ac.in",
                "phone": "+91-22-26707440",
            },
            {
                "name": "Keshav Memorial Institute of Technology (KMIT)",
                "aicte_id": "1-602345678",
                "state": "Telangana",
                "city": "Hyderabad",
                "address": "3-5-1026, Narayanguda, Hyderabad - 500029",
                "contact_person": "Dr. Neil Gogte (Director)",
                "email": "director@kmit.in",
                "phone": "+91-40-23261404",
            },
            {
                "name": "L.D. College of Engineering (LDCE)",
                "aicte_id": "1-701234567",
                "state": "Gujarat",
                "city": "Ahmedabad",
                "address": "Opp Gujarat University, Navrangpura, Ahmedabad - 380015",
                "contact_person": "Dr. Rajul K. Gajjar (Principal)",
                "email": "principal@ldce.ac.in",
                "phone": "+91-79-26306752",
            },
        ]

        institution_objects = []
        for inst_data in institutions_raw:
            inst, _ = Institution.objects.get_or_create(
                aicte_id=inst_data["aicte_id"],
                defaults=inst_data
            )
            institution_objects.append(inst)

            # Create an institution user for each
            inst_user, _ = User.objects.get_or_create(
                username=inst.email,
                defaults={
                    "email": inst.email,
                    "role": User.Role.INSTITUTION,
                    "first_name": inst.contact_person.split()[0],
                    "last_name": inst.name[:30],
                    "institution": inst,
                    "phone_number": inst.phone,
                    "designation": "Authorized Institute Representative",
                    "is_active": True,
                }
            )
            inst_user.set_password(default_pwd)
            inst_user.save()

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(institution_objects)} Institutions and login users."))

        # 3. Seed Alert Rules
        alert_rules_data = [
            ("90-Day Early Renewal Alert", 90, "FDR maturity approaching in 90 days. Initiate renewal process."),
            ("60-Day Renewal Reminder", 60, "FDR maturity approaching in 60 days. Bank renewal certificate required."),
            ("30-Day Urgent Renewal Notice", 30, "URGENT: FDR will mature within 30 days. Prevent compliance breach."),
            ("15-Day Final Escalation Warning", 15, "CRITICAL: 15 days remaining before FDR maturity deadline."),
            ("7-Day AICTE Notice", 7, "IMMEDIATE ACTION: 7 days until FDR maturity."),
            ("Maturity Day Expiry Alert", 0, "FDR has reached maturity today. Immediate submission of renewed receipt required."),
        ]
        for name, days, template in alert_rules_data:
            AlertRule.objects.get_or_create(
                days_before_maturity=days,
                defaults={
                    "name": name,
                    "alert_type": "MATURITY_ALERT",
                    "channel": Notification.Channel.EMAIL,
                    "is_active": True,
                    "email_template": template
                }
            )
        self.stdout.write(self.style.SUCCESS("Seeded Alert Rules."))

        # 4. Seed 60 Realistic FDRs across all lifecycle statuses
        banks = [
            ("State Bank of India", "SBI Main Branch, Fort Mumbai"),
            ("Punjab National Bank", "PNB Parliament Street, New Delhi"),
            ("Canara Bank", "Canara Bank MG Road, Bengaluru"),
            ("Bank of Baroda", "BoB Alkapuri Branch, Vadodara"),
            ("HDFC Bank", "HDFC K.G. Marg, New Delhi"),
            ("ICICI Bank", "ICICI Bandra Kurla Complex, Mumbai"),
            ("Union Bank of India", "UBI Nariman Point, Mumbai"),
            ("Indian Bank", "Indian Bank Rajaji Salai, Chennai"),
        ]

        approval_cycles = [
            "AICTE Extension of Approval 2024-25",
            "Establishment of New Technical Institute 2023-24",
            "Introduction of Emerging Tech / AI & ML Courses 2024-25",
            "Increase in Approved Intake (PG Programs) 2023-24",
            "Integrated Campus Approval Cycle 2022-27",
        ]

        # Status distribution mapping totaling 60 FDRs
        status_distribution = [
            (FDR.Status.SUBMITTED, 8),
            (FDR.Status.UNDER_REVIEW, 6),
            (FDR.Status.VERIFIED, 8),
            (FDR.Status.REJECTED, 4),
            (FDR.Status.NEEDS_CLARIFICATION, 5),
            (FDR.Status.ACTIVE, 12),
            (FDR.Status.EXPIRING_SOON, 8),
            (FDR.Status.EXPIRED, 5),
            (FDR.Status.RENEWED, 5),
            (FDR.Status.RELEASE_REQUESTED, 4),
            (FDR.Status.RELEASED, 3), # wait, 8+6+8+4+5+12+8+5+5+4+3 = 68 -> perfect, covers all >= 60
        ]

        today = timezone.now().date()
        fdr_counter = 1001

        created_fdrs = []
        for status, count in status_distribution:
            for idx in range(count):
                inst = institution_objects[(fdr_counter) % len(institution_objects)]
                bank_name, branch = banks[(fdr_counter) % len(banks)]
                cycle = approval_cycles[(fdr_counter) % len(approval_cycles)]
                fdr_num = f"FDR-{today.year}-{inst.state[:2].upper()}-{fdr_counter}"
                
                # Vary amount realistically between ₹5 Lakhs and ₹1 Crore
                amount_options = [500000, 1000000, 1500000, 2500000, 3500000, 5000000, 10000000]
                amount = decimal.Decimal(amount_options[(fdr_counter) % len(amount_options)])
                interest_rate = decimal.Decimal("6.75") + decimal.Decimal(str((fdr_counter % 15) * 0.1))

                # Calculate issue and maturity dates based on status
                if status == FDR.Status.EXPIRED:
                    issue_date = today - datetime.timedelta(days=1100 + (idx * 30))
                    maturity_date = today - datetime.timedelta(days=10 + (idx * 15))
                elif status == FDR.Status.EXPIRING_SOON:
                    issue_date = today - datetime.timedelta(days=1060)
                    days_left = [7, 14, 21, 28, 45, 60, 75, 88][idx % 8]
                    maturity_date = today + datetime.timedelta(days=days_left)
                elif status in (FDR.Status.SUBMITTED, FDR.Status.UNDER_REVIEW, FDR.Status.NEEDS_CLARIFICATION):
                    issue_date = today - datetime.timedelta(days=15 + (idx * 5))
                    maturity_date = today + datetime.timedelta(days=1095) # 3-year FDR
                elif status == FDR.Status.RELEASED:
                    issue_date = today - datetime.timedelta(days=1825) # 5-year FDR
                    maturity_date = today - datetime.timedelta(days=30)
                else: # ACTIVE, VERIFIED, REJECTED, RENEWED, RELEASE_REQUESTED
                    issue_date = today - datetime.timedelta(days=180 + (idx * 30))
                    maturity_date = today + datetime.timedelta(days=500 + (idx * 60))

                lien_marked = status not in (FDR.Status.REJECTED, FDR.Status.NEEDS_CLARIFICATION)

                # Mock OCR extracted data
                extracted_data = {
                    "fdr_number": fdr_num,
                    "bank_name": bank_name,
                    "branch": branch,
                    "amount": float(amount),
                    "interest_rate": float(interest_rate),
                    "issue_date": str(issue_date),
                    "maturity_date": str(maturity_date),
                    "lien_in_favour_of": "Member Secretary, AICTE New Delhi" if lien_marked else "None / General",
                    "confidence_scores": {
                        "fdr_number": 0.98,
                        "bank_name": 0.97,
                        "amount": 0.99,
                        "dates": 0.95,
                        "lien": 0.92 if lien_marked else 0.84,
                    }
                }

                fdr, created = FDR.objects.get_or_create(
                    fdr_number=fdr_num,
                    defaults={
                        "institution": inst,
                        "bank_name": bank_name,
                        "branch": branch,
                        "amount": amount,
                        "interest_rate": interest_rate,
                        "issue_date": issue_date,
                        "maturity_date": maturity_date,
                        "lien_marked_aicte": lien_marked,
                        "purpose_approval_cycle": cycle,
                        "status": status,
                        "extracted_data": extracted_data,
                        "remarks": f"Demo record seeded for AICTE lifecycle test - {status}"
                    }
                )
                created_fdrs.append(fdr)

                # Seed associated document
                dummy_content = f"SecurFlow AICTE Mock Document - {fdr_num}\nBank: {bank_name}\nAmount: INR {amount}".encode('utf-8')
                doc_hash = hashlib.sha256(dummy_content).hexdigest()
                doc, _ = FDRDocument.objects.get_or_create(
                    fdr=fdr,
                    file_name=f"{fdr_num}_Scanned_Copy.pdf",
                    defaults={
                        "file_type": FDRDocument.DocType.FDR_COPY,
                        "checksum": doc_hash,
                        "file_size": 245100 + (fdr_counter * 10),
                        "mime_type": "application/pdf",
                    }
                )

                # Seed Verification Record for reviewed / verified / clarification / rejected FDRs
                if status in (FDR.Status.VERIFIED, FDR.Status.REJECTED, FDR.Status.NEEDS_CLARIFICATION, FDR.Status.ACTIVE):
                    ver_status = VerificationRecord.Status.APPROVED
                    remarks_text = "All FDR details and AICTE lien clause verified successfully."
                    mismatches_list = []

                    if status == FDR.Status.REJECTED:
                        ver_status = VerificationRecord.Status.REJECTED
                        remarks_text = "Lien in favour of AICTE is absent. FDR is in single institute name without joint pledging."
                        mismatches_list = [
                            {"field": "lien_marked_aicte", "expected": True, "found": False, "severity": "CRITICAL"}
                        ]
                    elif status == FDR.Status.NEEDS_CLARIFICATION:
                        ver_status = VerificationRecord.Status.CLARIFICATION_REQUESTED
                        remarks_text = "Maturity date on the uploaded bank advice differs from the online application form."
                        mismatches_list = [
                            {"field": "maturity_date", "submitted": str(maturity_date), "ocr_found": str(maturity_date - datetime.timedelta(days=1)), "severity": "MEDIUM"}
                        ]

                    VerificationRecord.objects.get_or_create(
                        fdr=fdr,
                        defaults={
                            "official": official_1 if idx % 2 == 0 else official_2,
                            "status": ver_status,
                            "remarks": remarks_text,
                            "mismatches": mismatches_list,
                            "is_automated_draft": False,
                        }
                    )

                # Seed Release Requests
                if status in (FDR.Status.RELEASE_REQUESTED, FDR.Status.RELEASED):
                    rel_status = ReleaseRequest.Status.RELEASED if status == FDR.Status.RELEASED else ReleaseRequest.Status.REQUESTED
                    inst_user = inst.users.first() or admin_user
                    ReleaseRequest.objects.get_or_create(
                        fdr=fdr,
                        defaults={
                            "requested_by": inst_user,
                            "reason": "Fulfilled required 5-year lock-in period after successful completion of accreditation cycle.",
                            "status": rel_status,
                            "official_remarks": "Approved by Regional Committee after thorough verification of no dues." if status == FDR.Status.RELEASED else "",
                            "decided_by": official_2 if status == FDR.Status.RELEASED else None,
                            "decision_date": timezone.now() if status == FDR.Status.RELEASED else None,
                            "refund_order_number": f"AICTE/RO/REL/2026/{fdr_counter}" if status == FDR.Status.RELEASED else "",
                        }
                    )

                # Seed Audit Log
                AuditLog.objects.create(
                    actor=official_1 if status in (FDR.Status.VERIFIED, FDR.Status.ACTIVE) else admin_user,
                    action=AuditLog.Action.CREATE if status == FDR.Status.SUBMITTED else AuditLog.Action.STATUS_CHANGE,
                    entity_type="FDR",
                    entity_id=str(fdr.id),
                    before_state={"status": "INITIAL"},
                    after_state={"status": fdr.status, "fdr_number": fdr.fdr_number, "amount": str(fdr.amount)},
                    ip_address="127.0.0.1",
                    user_agent="SecurFlow Seeder Engine / 1.0"
                )

                # Seed Notification
                if status in (FDR.Status.EXPIRING_SOON, FDR.Status.EXPIRED, FDR.Status.NEEDS_CLARIFICATION):
                    Notification.objects.create(
                        institution=inst,
                        fdr=fdr,
                        title=f"Action Required for FDR #{fdr.fdr_number}",
                        message=f"FDR #{fdr.fdr_number} ({bank_name}) has status: {fdr.get_status_display()}.",
                        notification_type=Notification.Type.MATURITY_REMINDER if status != FDR.Status.NEEDS_CLARIFICATION else Notification.Type.CLARIFICATION,
                        channel=Notification.Channel.IN_APP,
                        sent_status=Notification.SentStatus.SENT,
                        sent_at=timezone.now(),
                    )

                fdr_counter += 1

        # Link some renewed FDRs to parent FDRs and create RenewalRecords
        renewed_fdrs = [f for f in created_fdrs if f.status == FDR.Status.RENEWED]
        active_fdrs = [f for f in created_fdrs if f.status == FDR.Status.ACTIVE]
        for idx, r_fdr in enumerate(renewed_fdrs):
            if idx < len(active_fdrs):
                parent = active_fdrs[idx]
                r_fdr.parent_fdr = parent
                r_fdr.save()
                RenewalRecord.objects.get_or_create(
                    original_fdr=parent,
                    new_fdr=r_fdr,
                    defaults={
                        "renewal_type": RenewalRecord.RenewalType.RENEWAL,
                        "reason": f"Maturity reached on original FDR #{parent.fdr_number}. Renewed for 3 years.",
                        "renewal_date": today - datetime.timedelta(days=60),
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(created_fdrs)} FDRs across all lifecycle statuses, plus documents, verification records, release requests, notifications and audit logs!"))
