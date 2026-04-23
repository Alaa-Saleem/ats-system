from .models import ActivityLog


def log_activity(*, user, company, action, description):
    if not company:
        return None
    return ActivityLog.objects.create(
        user=user,
        company=company,
        action=action,
        description=description,
    )
