from django.core.management.base import BaseCommand
from notifications.scanner import run_maturity_scan

class Command(BaseCommand):
    help = 'Executes daily maturity scan, updates EXPIRING_SOON/EXPIRED statuses, and dispatches reminders.'

    def handle(self, *args, **options):
        self.stdout.write("Starting AICTE FDR Maturity Scan...")
        results = run_maturity_scan()
        self.stdout.write(
            self.style.SUCCESS(
                f"Scan Complete: {results['fdrs_scanned']} FDRs scanned, "
                f"{results['statuses_updated']} statuses updated, "
                f"{results['notifications_created']} in-app alerts created, "
                f"{results['emails_dispatched']} emails dispatched."
            )
        )
