try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func

from .scanner import run_maturity_scan

@shared_task
def scan_fdr_maturities_task():
    """
    Celery Beat scheduled job to run daily maturity scanning.
    """
    return run_maturity_scan()
