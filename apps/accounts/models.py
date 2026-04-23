from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('company_owner', 'Company Owner'),
        ('team_member', 'Team Member'),
        ('candidate', 'Candidate'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_owner = models.BooleanField(default=False)
    TEAM_ROLE_CHOICES = (
        ('editor', _('محرر')),
        ('reviewer', _('مقيّم')),
        ('approver', _('صاحب قرار')),
    )
    team_role = models.CharField(_('دور الفريق'), max_length=20, choices=TEAM_ROLE_CHOICES, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # ── Profile fields ────────────────────────────────────────────────────────
    avatar   = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio      = models.TextField(blank=True)
    phone    = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)   # staff position/department


    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def company_profile(self):
        if hasattr(self, 'owned_company') and self.owned_company:
            return self.owned_company
        return self.company

    @property
    def profile_completion(self):
        """Returns 0-100 completion score based on filled profile fields."""
        score = 0
        if self.avatar:                            score += 15
        if self.get_full_name():                   score += 10
        if self.phone:                             score += 10
        if self.location:                          score += 10
        if self.bio:                               score += 10
        if self.email:                             score += 10
        # Candidate-specific via linked profile
        candidate = self.candidate_profiles.filter(company=None).first()
        if candidate:
            if candidate.current_title:            score += 10
            if candidate.years_of_experience:      score += 10
            if candidate.cv_file:                  score += 15
        else:
            score += 35   # non-candidate users get these points by default
        return min(score, 100)


class Company(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_company', null=True, blank=True)
    company_name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    company_size = models.CharField(max_length=50, blank=True)   # e.g. '1-10', '50-200'
    slug = models.SlugField(max_length=120, unique=True, blank=True)  # public URL

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.company_name) or f'company-{self.pk or ""}'
            slug = base
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return self.company_name

