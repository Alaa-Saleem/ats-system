from django.conf import settings
from django.db import models

from apps.accounts.models import Company


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ("create_job", "Create Job"),
        ("create_candidate", "Create Candidate"),
        ("shortlist", "Shortlist"),
        ("shortlisted", "Shortlisted"),
        ("removed_shortlist", "Removed Shortlist"),
        ("comment", "Comment"),
        ("rate", "Rate"),
        ("accept", "Accept"),
        ("reject", "Reject"),
        ("move_stage", "Move Stage"),
        ("link_candidate", "Link Candidate"),
        ("team_add", "Team Add"),
        ("team_update", "Team Update"),
        ("team_remove", "Team Remove"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="activity_logs")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} - {self.action}"
