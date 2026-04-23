from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import Company


class Candidate(models.Model):
    user_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidate_profiles',
        verbose_name="حساب المستخدم"
    )
    # Basic Info
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, null=True)

    # Professional Info
    current_title = models.CharField(max_length=255, blank=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    expected_salary = models.CharField(max_length=100, blank=True)
    availability = models.CharField(max_length=100, blank=True)
    skills        = models.TextField(blank=True)   # comma-separated
    bio           = models.TextField(blank=True)
    linkedin_url  = models.URLField(blank=True)
    github_url    = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Location
    location = models.CharField(max_length=255, blank=True)

    # CV
    cv_file = models.FileField(upload_to='cvs/', blank=True)

    # Notes
    notes = models.TextField(blank=True)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='candidates'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='candidates',
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    class Meta:
        ordering = ['-created_at']
        unique_together = ['company', 'phone']

    def __str__(self):
        return self.full_name


class CandidateNotification(models.Model):
    TYPE_CHOICES = (
        ('status_change', 'تغير الحالة'),
        ('interview', 'دعوة مقابلة'),
        ('offer', 'عرض وظيفي'),
        ('rejection', 'إشعار بالرفض'),
        ('system', 'إشعار نظام'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional link to application
    application = models.ForeignKey(
        'pipeline.Application',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
