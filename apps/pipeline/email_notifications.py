from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.utils import timezone

from .models import Application


def _send_email(to_emails, subject, text_body, html_body=None):
    recipients = [email for email in set(to_emails) if email]
    if not recipients:
        return
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    if html_body:
        msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=True)


def _candidate_email(application):
    return (application.candidate.email or "").strip()


def _hr_recipients(application):
    company = application.job.company
    recipients = []
    if getattr(company, "owner", None) and company.owner.email:
        recipients.append(company.owner.email)
    for member in company.users.filter(role="team_member").exclude(email="").values_list("email", flat=True):
        recipients.append(member)
    return recipients


def send_application_received_email(application):
    subject = f"Application Received - {application.job.title}"
    text = (
        f"Hello {application.candidate.full_name},\n\n"
        f"We received your application for: {application.job.title}.\n"
        "What happens next:\n"
        "- Our hiring team will review your profile.\n"
        "- If shortlisted, you will receive interview details by email.\n\n"
        "Thank you for applying."
    )
    _send_email([_candidate_email(application)], subject, text)


def send_hr_new_application_email(application):
    subject = f"New Application - {application.job.title}"
    text = (
        "A new candidate has applied.\n\n"
        f"Candidate: {application.candidate.full_name}\n"
        f"Job: {application.job.title}\n"
        f"Email: {application.candidate.email or '-'}\n"
        f"Phone: {application.candidate.phone or '-'}\n"
    )
    _send_email(_hr_recipients(application), subject, text)


def send_stage_email(application):
    stage_name = (application.current_stage.name or "").lower()
    candidate_name = application.candidate.full_name
    job_title = application.job.title
    candidate_email = _candidate_email(application)

    if not candidate_email:
        return

    if "review" in stage_name or "مراجعة" in stage_name:
        subject = f"Application Update - Under Review - {job_title}"
        text = (
            f"Hello {candidate_name},\n\n"
            f"Your application for {job_title} is now under review.\n"
            "We will contact you as soon as there is an update."
        )
    elif "interview" in stage_name or "مقابلة" in stage_name:
        subject = f"Interview Invitation - {job_title}"
        text = (
            f"Hello {candidate_name},\n\n"
            f"You have moved to the interview stage for {job_title}.\n"
            "Interview date: To be shared soon\n"
            "Interview time: To be shared soon\n"
            "Interview link: Will be sent by HR\n"
        )
    elif "reject" in stage_name or "مرفوض" in stage_name:
        subject = f"Application Update - {job_title}"
        text = (
            f"Hello {candidate_name},\n\n"
            f"Thank you for applying to {job_title}.\n"
            "After careful review, we will not proceed with this application.\n"
            "You are welcome to apply again for future roles."
        )
    elif "offer" in stage_name or "عرض" in stage_name:
        subject = f"Offer Letter - {job_title}"
        text = (
            f"Hello {candidate_name},\n\n"
            f"Congratulations! We are pleased to move you to the offer stage for {job_title}.\n"
            "Our HR team will send your offer details shortly."
        )
    elif "hired" in stage_name or "accept" in stage_name or "قبول" in stage_name:
        subject = f"Welcome Aboard - {job_title}"
        text = (
            f"Hello {candidate_name},\n\n"
            f"Congratulations! Your application for {job_title} has been marked as hired.\n"
            "Welcome to the team."
        )
    else:
        return

    _send_email([candidate_email], subject, text)


def send_no_response_reminders(days_without_response=5):
    cutoff = timezone.now() - timedelta(days=days_without_response)
    stale_apps = (
        Application.objects
        .select_related("job", "job__company")
        .filter(updated_at__lte=cutoff)
    )
    for app in stale_apps:
        recipients = _hr_recipients(app)
        subject = f"Reminder: Candidate Pending {days_without_response}+ Days - {app.job.title}"
        text = (
            f"Candidate {app.candidate.full_name} has not received updates for over "
            f"{days_without_response} days.\n"
            f"Job: {app.job.title}\n"
            f"Current stage: {app.current_stage.name}"
        )
        _send_email(recipients, subject, text)


def send_daily_summary_emails():
    today = timezone.now().date()
    stats = (
        Application.objects
        .filter(created_at__date=today)
        .values("job__company_id", "job__company__company_name")
        .annotate(applications_count=Count("id"))
    )

    for row in stats:
        company_apps = (
            Application.objects
            .filter(job__company_id=row["job__company_id"], updated_at__date=today)
            .select_related("current_stage")
        )
        interviews_count = sum(
            1 for app in company_apps if "interview" in app.current_stage.name.lower() or "مقابلة" in app.current_stage.name
        )

        company_name = row["job__company__company_name"]
        subject = f"Daily ATS Summary - {company_name}"
        text = (
            f"Date: {today.isoformat()}\n"
            f"New applications: {row['applications_count']}\n"
            f"Applications moved to interview: {interviews_count}\n"
        )
        company_app = Application.objects.filter(job__company_id=row["job__company_id"]).first()
        if not company_app:
            continue
        _send_email(_hr_recipients(company_app), subject, text)
