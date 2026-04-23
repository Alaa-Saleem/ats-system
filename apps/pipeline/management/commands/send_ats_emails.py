from django.core.management.base import BaseCommand

from apps.pipeline.email_notifications import (
    send_daily_summary_emails,
    send_no_response_reminders,
)


class Command(BaseCommand):
    help = "Send ATS reminder and daily summary emails."

    def handle(self, *args, **options):
        send_no_response_reminders(days_without_response=5)
        send_daily_summary_emails()
        self.stdout.write(self.style.SUCCESS("ATS emails sent."))
