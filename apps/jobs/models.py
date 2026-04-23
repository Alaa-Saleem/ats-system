from django.db import models
from django.utils import timezone
from apps.accounts.models import Company


class Job(models.Model):

    JOB_TYPE_CHOICES = (
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('remote', 'Remote'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    )

    STATUS_CHOICES = (
        ('open', 'Active'),
        ('closed', 'Closed'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField()
    location = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True, default='')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

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

    def __str__(self):
        return self.title

    @property
    def is_accepting_applications(self):
        """Returns True if job is open AND deadline hasn't passed."""
        from django.utils import timezone
        if self.status != 'open':
            return False
        if self.application_deadline:
            return self.application_deadline >= timezone.now().date()
        return True


class JobCustomField(models.Model):
    """A custom field attached to a job, shown on the application form."""

    FIELD_TYPES = [
        ('text',         'نص قصير'),
        ('textarea',     'نص طويل'),
        ('select',       'قائمة اختيار'),
        ('checkbox',     'نعم / لا'),
        ('date',         'تاريخ'),
        ('number',       'رقم'),
        ('file_upload',  'ملف (PDF, DOC, DOCX)'),
        ('image_upload', 'صورة (JPG, PNG, GIF)'),
    ]

    job         = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='custom_fields')
    label       = models.CharField(max_length=200, verbose_name='اسم الحقل')
    field_type  = models.CharField(max_length=30, choices=FIELD_TYPES, default='text')
    options     = models.TextField(
        blank=True,
        help_text='للقائمة المنسدلة فقط: أدخل الخيارات مفصولة بفاصلة. مثال: خيار1,خيار2,خيار3'
    )
    is_required = models.BooleanField(default=False, verbose_name='إلزامي')
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.job.title} — {self.label}"

    def get_options_list(self):
        """Return options as a cleaned list (for select fields)."""
        return [o.strip() for o in self.options.split(',') if o.strip()]
