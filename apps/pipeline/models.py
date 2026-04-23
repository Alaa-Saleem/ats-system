from django.db import models
from django.utils import timezone
from apps.candidates.models import Candidate
from apps.jobs.models import Job


class PipelineStage(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم المرحلة")
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    color = models.CharField(max_length=20, default="#6c757d", verbose_name="اللون")

    class Meta:
        ordering = ['order']
        verbose_name = "مرحلة التوظيف"
        verbose_name_plural = "مراحل التوظيف"

    def __str__(self):
        return self.name


class Application(models.Model):
    candidate = models.ForeignKey(Candidate, models.CASCADE, related_name='applications', verbose_name="المرشح")
    job = models.ForeignKey(Job, models.CASCADE, related_name='applications', verbose_name="الوظيفة")
    current_stage = models.ForeignKey(PipelineStage, models.PROTECT, related_name='applications', verbose_name="المرحلة الحالية")
    source = models.CharField(max_length=100, blank=True, verbose_name="المصدر")
    is_shortlisted = models.BooleanField(default=False, verbose_name="مختار مبدئياً")

    last_activity_at = models.DateTimeField(auto_now=True)
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
        unique_together = ['candidate', 'job']
        verbose_name = "تطبيق وظيفة"
        verbose_name_plural = "تطبيقات الوظائف"

    def __str__(self):
        return f"{self.candidate} - {self.job}"

    def avg_rating(self):
        ratings = list(self.ratings.values_list('score', flat=True))
        if not ratings:
            return 0
        return round(sum(ratings) / len(ratings), 1)


class ApplicationComment(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='pipeline_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.application}"


class ApplicationRating(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='pipeline_ratings')
    score = models.PositiveSmallIntegerField(default=0)  # 1-5

    class Meta:
        unique_together = ['application', 'rater']

    def __str__(self):
        return f"Rating {self.score} by {self.rater} on {self.application}"


class ApplicationAnswer(models.Model):
    """Stores a candidate's answer to a custom application field."""
    application  = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='custom_answers')
    field        = models.ForeignKey('jobs.JobCustomField', on_delete=models.CASCADE, related_name='answers')
    # Text answer for non-file fields
    text_answer  = models.TextField(blank=True)
    # File answer for file_upload / image_upload fields
    file_answer  = models.FileField(upload_to='application_files/', null=True, blank=True)

    def __str__(self):
        return f"Answer to '{self.field.label}' for {self.application}"

    @property
    def display_value(self):
        if self.field.field_type in ('file_upload', 'image_upload'):
            return self.file_answer.url if self.file_answer else '—'
        return self.text_answer or '—'
