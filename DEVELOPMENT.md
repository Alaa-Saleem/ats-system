# Development Guide - Recruitment ATS

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Common Tasks](#common-tasks)

---

## Getting Started

### Initial Setup

1. **Install PostgreSQL**
   - Download from https://www.postgresql.org/download/
   - Install and remember your password
   - Create database: `createdb ats_db`

2. **Clone and Setup Project**
```bash
cd C:\Users\Ahmed\Desktop\rec
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy example env file
copy .env.example .env

# Edit .env and update:
# - DATABASE_PASSWORD (your PostgreSQL password)
# - SECRET_KEY (generate new one for production)
```

4. **Initialize Database**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata initial_stages
```

5. **Run Development Server**
```bash
python manage.py runserver
```

---

## Development Workflow

### Week 1: Foundation & Candidates

#### Day 1-2: Project Setup
```bash
# Create Django project
django-admin startproject config .

# Create apps
python manage.py startapp accounts
python manage.py startapp candidates
python manage.py startapp clients
python manage.py startapp jobs
python manage.py startapp pipeline
python manage.py startapp activities
python manage.py startapp dashboard

# Move apps to apps/ directory
mkdir apps
move accounts apps/
move candidates apps/
# ... repeat for all apps
```

#### Day 3-5: Candidate Module

**Models (apps/candidates/models.py):**
```python
from django.db import models
from django.contrib.auth.models import User

class Candidate(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    current_title = models.CharField(max_length=255, blank=True)
    years_experience = models.IntegerField(null=True, blank=True)
    expected_salary = models.CharField(max_length=100, blank=True)
    availability = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

class CandidateFile(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='cvs/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.full_name} - {self.file_name}"
```

**Views (apps/candidates/views.py):**
```python
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Candidate, CandidateFile

class CandidateListView(LoginRequiredMixin, ListView):
    model = Candidate
    template_name = 'candidates/candidate_list.html'
    context_object_name = 'candidates'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        
        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query) |
                Q(skills__icontains=query) |
                Q(notes__icontains=query)
            )
        
        return queryset.order_by('-created_at')

class CandidateCreateView(LoginRequiredMixin, CreateView):
    model = Candidate
    template_name = 'candidates/candidate_form.html'
    fields = ['full_name', 'phone', 'email', 'location', 'current_title', 
              'years_experience', 'expected_salary', 'availability', 'skills', 'notes']
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        
        # Handle CV upload
        if 'cv_file' in self.request.FILES:
            cv_file = self.request.FILES['cv_file']
            CandidateFile.objects.create(
                candidate=self.object,
                file=cv_file,
                file_name=cv_file.name,
                file_type=cv_file.content_type,
                file_size=cv_file.size
            )
        
        return response
```

**URLs (apps/candidates/urls.py):**
```python
from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.CandidateListView.as_view(), name='list'),
    path('create/', views.CandidateCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CandidateDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CandidateUpdateView.as_view(), name='edit'),
]
```

**Template (templates/candidates/candidate_list.html):**
```html
{% extends 'base.html' %}

{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col-md-6">
            <h2>Candidates</h2>
        </div>
        <div class="col-md-6 text-end">
            <a href="{% url 'candidates:create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Candidate
            </a>
        </div>
    </div>

    <!-- Search -->
    <div class="row mb-3">
        <div class="col-md-6">
            <form method="get" class="input-group">
                <input type="text" name="q" class="form-control" 
                       placeholder="Search by name, phone, email, skills..." 
                       value="{{ request.GET.q }}">
                <button class="btn btn-outline-secondary" type="submit">
                    <i class="fas fa-search"></i> Search
                </button>
            </form>
        </div>
    </div>

    <!-- Candidates Table -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>Current Title</th>
                        <th>Experience</th>
                        <th>Owner</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for candidate in candidates %}
                    <tr>
                        <td>
                            <a href="{% url 'candidates:detail' candidate.pk %}">
                                {{ candidate.full_name }}
                            </a>
                        </td>
                        <td>{{ candidate.phone }}</td>
                        <td>{{ candidate.email|default:"-" }}</td>
                        <td>{{ candidate.current_title|default:"-" }}</td>
                        <td>{{ candidate.years_experience|default:"-" }} years</td>
                        <td>{{ candidate.owner.get_full_name }}</td>
                        <td>{{ candidate.created_at|date:"Y-m-d" }}</td>
                        <td>
                            <a href="{% url 'candidates:edit' candidate.pk %}" 
                               class="btn btn-sm btn-outline-primary">Edit</a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="8" class="text-center">No candidates found</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Pagination -->
    {% if is_paginated %}
    <nav aria-label="Page navigation" class="mt-3">
        <ul class="pagination justify-content-center">
            {% if page_obj.has_previous %}
            <li class="page-item">
                <a class="page-link" href="?page=1">First</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
            </li>
            {% endif %}

            <li class="page-item active">
                <span class="page-link">Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
            </li>

            {% if page_obj.has_next %}
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">Last</a>
            </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
{% endblock %}
```

---

### Week 2: Clients & Jobs

Follow similar pattern as candidates:
1. Create models
2. Create views (List, Create, Update, Detail)
3. Create forms
4. Create templates
5. Add URLs
6. Test functionality

---

### Week 3: Pipeline & Activities

**Key Implementation - Application Model:**
```python
class Application(models.Model):
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE)
    job = models.ForeignKey('jobs.JobOrder', on_delete=models.CASCADE)
    current_stage = models.ForeignKey('PipelineStage', on_delete=models.PROTECT)
    source = models.CharField(max_length=100, blank=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['candidate', 'job']

    def change_stage(self, new_stage, user):
        """Change stage and log activity"""
        old_stage = self.current_stage
        self.current_stage = new_stage
        self.last_activity_at = timezone.now()
        self.save()

        # Auto-log activity
        Activity.objects.create(
            application=self,
            type='stage_change',
            description=f'Stage changed from {old_stage.name} to {new_stage.name}',
            created_by=user
        )
```

---

## Code Standards

### Python/Django Standards

1. **Follow PEP 8**
   - Use 4 spaces for indentation
   - Max line length: 100 characters
   - Use meaningful variable names

2. **Model Conventions**
   - Use singular names (Candidate, not Candidates)
   - Add `__str__` method to all models
   - Use `related_name` for foreign keys
   - Add `created_at` and `updated_at` to all models

3. **View Conventions**
   - Use class-based views when possible
   - Add `LoginRequiredMixin` to all views
   - Use `get_queryset()` for filtering
   - Add docstrings to complex methods

4. **Template Conventions**
   - Extend from `base.html`
   - Use template inheritance
   - Use `{% load static %}` for static files
   - Add CSRF token to all forms

---

## Testing Guidelines

### Unit Tests Example

```python
# apps/candidates/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Candidate

class CandidateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_candidate(self):
        candidate = Candidate.objects.create(
            full_name='John Doe',
            phone='+1234567890',
            email='john@example.com',
            owner=self.user
        )
        self.assertEqual(candidate.full_name, 'John Doe')
        self.assertEqual(str(candidate), 'John Doe')
        
    def test_phone_unique(self):
        Candidate.objects.create(
            full_name='John Doe',
            phone='+1234567890',
            owner=self.user
        )
        
        with self.assertRaises(Exception):
            Candidate.objects.create(
                full_name='Jane Doe',
                phone='+1234567890',  # Duplicate
                owner=self.user
            )
```

### Run Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test apps.candidates

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Common Tasks

### Create New Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic
```

### Load Fixtures
```bash
python manage.py loaddata initial_stages
```

### Create Fixtures
```bash
python manage.py dumpdata pipeline.PipelineStage --indent 2 > fixtures/initial_stages.json
```

### Database Shell
```bash
python manage.py dbshell
```

### Django Shell
```bash
python manage.py shell
```

### Clear Database (Development Only!)
```bash
python manage.py flush
```

---

## Troubleshooting

### Common Issues

**Issue: Database connection error**
```
Solution: Check .env file, ensure PostgreSQL is running
```

**Issue: Migration conflicts**
```bash
# Reset migrations (development only!)
python manage.py migrate --fake app_name zero
python manage.py migrate app_name
```

**Issue: Static files not loading**
```bash
python manage.py collectstatic --clear
```

**Issue: File upload not working**
```python
# Check settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Check urls.py (development)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Performance Tips

1. **Database Indexes**
   - Add indexes to frequently searched fields
   - Use `select_related()` for foreign keys
   - Use `prefetch_related()` for many-to-many

2. **Query Optimization**
   ```python
   # Bad
   for candidate in Candidate.objects.all():
       print(candidate.owner.username)  # N+1 queries
   
   # Good
   for candidate in Candidate.objects.select_related('owner'):
       print(candidate.owner.username)  # 1 query
   ```

3. **Caching**
   - Cache expensive queries
   - Use template fragment caching
   - Cache static pages

---

## Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up static files serving
- [ ] Set up media files storage
- [ ] Configure database backups
- [ ] Set up SSL certificate
- [ ] Configure email backend
- [ ] Set up logging
- [ ] Run security checks: `python manage.py check --deploy`
- [ ] Create superuser
- [ ] Load initial data

---

## Resources

- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Bootstrap Documentation: https://getbootstrap.com/docs/
- Django Best Practices: https://django-best-practices.readthedocs.io/

---

**Happy Coding! 🚀**
