import datetime
import re
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail

from fdrs.models import FDR
from .models import Notification, AlertRule
from audit.utils import log_audit_event
from django.utils import timezone


DEFAULT_REMINDER_DAYS = [90, 60, 30, 15, 7, 0]

DEFAULT_EMAIL_TEMPLATE = """
Dear Principal / Authorised Signatory,
{{institution}}

This is an official AICTE compliance advisory regarding your Security Deposit Fixed Deposit Receipt (FDR):

FDR Number: {{fdr_number}}
Issuing Bank: {{bank_name}} (Branch: {{branch}})
Principal Amount: INR {{amount}}
Maturity Date: {{maturity_date}}
Days Remaining: {{days_left}} days

{% if days_left <= 0 %}
URGENT: This FDR has EXPIRED as of {{maturity_date}}. You are required to submit an active renewal or replacement deposit receipt immediately to avoid compliance action.
{% else %}
Please ensure timely renewal of this deposit receipt before the maturity date. AICTE lien must be maintained continuously as per Approval Process Handbook (APH) regulations.
{% endif %}

Portal Action Link: http://127.0.0.1:3000/renewals-releases

Yours faithfully,
Approval Bureau,
All India Council for Technical Education (AICTE), New Delhi
"""


def render_template(template_str: str, context: dict) -> str:
    res = template_str
    for key, val in context.items():
        res = res.replace(f"{{{{{key}}}}}", str(val))
    # Simple block cleanup
    if context.get('days_left', 1) <= 0:
        res = re.sub(r'\{% if days_left <= 0 %\}(.*?)\{% else %\}.*?\{% endif %\}', r'\1', res, flags=re.DOTALL)
    else:
        res = re.sub(r'\{% if days_left <= 0 %\}.*?\{% else %\}(.*?)\{% endif %\}', r'\1', res, flags=re.DOTALL)
    return res.strip()


def run_maturity_scan(request=None) -> dict:
    """
    Scans all FDR maturity dates, updates status (EXPIRING_SOON, EXPIRED),
    and generates idempotent notifications and email dispatches.
    """
    today = datetime.date.today()

    active_rules = list(AlertRule.objects.filter(is_active=True).order_by('-days_before_maturity'))
    if active_rules:
        reminder_thresholds = [r.days_before_maturity for r in active_rules]
        rule_map = {r.days_before_maturity: r for r in active_rules}
    else:
        reminder_thresholds = DEFAULT_REMINDER_DAYS
        rule_map = {}

    # Find FDRs that are eligible for status update or reminder
    candidate_fdrs = FDR.objects.filter(
        status__in=[
            FDR.Status.ACTIVE,
            FDR.Status.VERIFIED,
            FDR.Status.EXPIRING_SOON,
            FDR.Status.SUBMITTED,
            FDR.Status.UNDER_REVIEW
        ]
    ).select_related('institution')

    fdrs_scanned = 0
    statuses_updated = 0
    notifications_created = 0
    emails_dispatched = 0

    for fdr in candidate_fdrs:
        fdrs_scanned += 1
        days_left = (fdr.maturity_date - today).days

        # 1. Status Transition check
        new_status = None
        if days_left <= 0 and fdr.status != FDR.Status.EXPIRED:
            new_status = FDR.Status.EXPIRED
        elif 0 < days_left <= 90 and fdr.status in [FDR.Status.ACTIVE, FDR.Status.VERIFIED]:
            new_status = FDR.Status.EXPIRING_SOON

        if new_status and fdr.status != new_status:
            old_status = fdr.status
            fdr.status = new_status
            fdr.save(update_fields=['status', 'updated_at'])
            statuses_updated += 1

            if request:
                log_audit_event(
                    request=request,
                    action=AuditLog.Action.STATUS_CHANGE,
                    entity_type='FDR',
                    entity_id=fdr.id,
                    before_state={'status': old_status},
                    after_state={'status': new_status, 'trigger': 'maturity_scanner', 'days_left': days_left}
                )

        # 2. Check if a reminder interval matches
        # We find the highest threshold <= days_left, or if days_left <= 0, the 0 milestone
        matched_milestone = None
        for threshold in sorted(reminder_thresholds, reverse=True):
            if days_left <= threshold:
                matched_milestone = threshold

        if matched_milestone is None and days_left > max(reminder_thresholds):
            continue

        milestone_key = matched_milestone if matched_milestone is not None else 0

        # Idempotency check: has a notification for this FDR and this milestone window been sent within the last 5 days?
        # A milestone reminder is unique per (fdr, milestone)
        window_start = today - datetime.timedelta(days=6)
        existing_notif = Notification.objects.filter(
            fdr=fdr,
            notification_type=Notification.Type.MATURITY_REMINDER,
            created_at__date__gte=window_start,
            title__icontains=f"{milestone_key} Days" if milestone_key > 0 else "Expired"
        ).exists()

        if existing_notif:
            continue

        # Prepare Notification text
        if milestone_key <= 0:
            title = f"CRITICAL: FDR #{fdr.fdr_number} Expired (Maturity: {fdr.maturity_date})"
            short_msg = f"Your FDR #{fdr.fdr_number} of INR {float(fdr.amount):,.2f} at {fdr.bank_name} expired on {fdr.maturity_date}. Submit renewal immediately."
        else:
            title = f"Maturity Reminder: FDR #{fdr.fdr_number} ({milestone_key} Days Left)"
            short_msg = f"FDR #{fdr.fdr_number} of INR {float(fdr.amount):,.2f} at {fdr.bank_name} matures on {fdr.maturity_date} ({days_left} days remaining)."

        # 1. Create In-App Notification
        Notification.objects.create(
            institution=fdr.institution,
            fdr=fdr,
            title=title,
            message=short_msg,
            notification_type=Notification.Type.MATURITY_REMINDER,
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT,
            sent_at=timezone.now()
        )
        notifications_created += 1

        # 2. Render & Dispatch Email
        rule = rule_map.get(milestone_key)
        template_text = rule.email_template if (rule and rule.email_template) else DEFAULT_EMAIL_TEMPLATE
        context = {
            'institution': fdr.institution.name,
            'fdr_number': fdr.fdr_number,
            'bank_name': fdr.bank_name,
            'branch': fdr.branch,
            'amount': f"{float(fdr.amount):,.2f}",
            'maturity_date': str(fdr.maturity_date),
            'days_left': max(days_left, 0)
        }
        email_body = render_template(template_text, context)
        recipient_email = fdr.institution.email or 'compliance@aicte-india.org'

        try:
            send_mail(
                subject=f"[AICTE Security Deposit] {title}",
                message=email_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@securflow.aicte.gov.in'),
                recipient_list=[recipient_email],
                fail_silently=True
            )
            emails_dispatched += 1
            email_status = Notification.SentStatus.SENT
        except Exception:
            email_status = Notification.SentStatus.FAILED

        # Record email log in Notification model
        Notification.objects.create(
            institution=fdr.institution,
            fdr=fdr,
            title=f"Email: {title}",
            message=email_body,
            notification_type=Notification.Type.MATURITY_REMINDER,
            channel=Notification.Channel.EMAIL,
            sent_status=email_status,
            sent_at=timezone.now()
        )

    return {
        'fdrs_scanned': fdrs_scanned,
        'statuses_updated': statuses_updated,
        'notifications_created': notifications_created,
        'emails_dispatched': emails_dispatched
    }
