# دليل التنفيذ خطوة بخطوة - نظام ATS
# Step-by-Step Implementation Guide - Recruitment ATS

هذا الدليل سيأخذك خطوة بخطوة من الصفر حتى تشغيل نظام ATS كامل في 4 أسابيع.

---

## 📅 الأسبوع الأول: الإعداد الأساسي ووحدة المرشحين
## Week 1: Foundation & Candidates Module

---

### اليوم 1: إعداد البيئة التطويرية
### Day 1: Development Environment Setup

#### الخطوة 1.1: تثبيت المتطلبات الأساسية

**1. تثبيت Python (إذا لم يكن مثبتاً)**
```bash
# تحقق من وجود Python
python --version

# يجب أن يكون الإصدار 3.11 أو أحدث
# إذا لم يكن مثبتاً، حمله من: https://www.python.org/downloads/
```

**2. تثبيت PostgreSQL**
```bash
# حمل PostgreSQL من: https://www.postgresql.org/download/windows/
# أثناء التثبيت:
# - اختر كلمة مرور قوية واحفظها
# - احفظ رقم المنفذ (افتراضي: 5432)
# - ثبت pgAdmin 4 (أداة إدارة قاعدة البيانات)
```

**3. إنشاء قاعدة البيانات**
```bash
# افتح Command Prompt كمسؤول
# انتقل إلى مجلد PostgreSQL bin
cd "C:\Program Files\PostgreSQL\15\bin"

# أنشئ قاعدة البيانات
createdb -U postgres ats_db

# أدخل كلمة المرور عندما يُطلب منك
```

#### الخطوة 1.2: إعداد المشروع

**1. إنشاء بيئة افتراضية**
```bash
# انتقل إلى مجلد المشروع
cd C:\Users\Ahmed\Desktop\rec

# أنشئ البيئة الافتراضية
python -m venv venv

# فعّل البيئة الافتراضية
venv\Scripts\activate

# يجب أن ترى (venv) في بداية السطر الآن
```

**2. تثبيت المكتبات المطلوبة**
```bash
# تأكد من أن البيئة الافتراضية مفعلة
pip install --upgrade pip

# ثبت Django والمكتبات
pip install -r requirements.txt

# تحقق من التثبيت
python -m django --version
```

**3. إعداد ملف البيئة**
```bash
# انسخ ملف المثال
copy .env.example .env

# افتح .env في محرر نصوص وعدّل:
# - DATABASE_PASSWORD: ضع كلمة مرور PostgreSQL الخاصة بك
# - SECRET_KEY: احتفظ بها كما هي للتطوير (غيّرها في الإنتاج)
```

#### الخطوة 1.3: إنشاء مشروع Django

**1. إنشاء المشروع الأساسي**
```bash
# أنشئ مشروع Django
django-admin startproject config .

# لاحظ النقطة في النهاية - مهمة جداً!
# هذا ينشئ المشروع في المجلد الحالي
```

**2. اختبار التشغيل الأولي**
```bash
# شغّل السيرفر
python manage.py runserver

# افتح المتصفح واذهب إلى: http://localhost:8000
# يجب أن ترى صفحة Django الترحيبية
# اضغط Ctrl+C لإيقاف السيرفر
```

---

### اليوم 2: إنشاء التطبيقات والنماذج الأساسية
### Day 2: Creating Apps and Basic Models

#### الخطوة 2.1: إنشاء التطبيقات

**1. إنشاء مجلد التطبيقات**
```bash
# أنشئ مجلد apps
mkdir apps

# أنشئ ملف __init__.py لجعله package
type nul > apps\__init__.py
```

**2. إنشاء جميع التطبيقات**
```bash
# أنشئ كل تطبيق
python manage.py startapp accounts
python manage.py startapp candidates
python manage.py startapp clients
python manage.py startapp jobs
python manage.py startapp pipeline
python manage.py startapp activities
python manage.py startapp dashboard

# انقل التطبيقات إلى مجلد apps
move accounts apps\
move candidates apps\
move clients apps\
move jobs apps\
move pipeline apps\
move activities apps\
move dashboard apps\
```

#### الخطوة 2.2: تكوين الإعدادات

**افتح `config/settings.py` وعدّل:**

```python
# في بداية الملف، أضف:
from pathlib import Path
from decouple import config
import os

# عدّل INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    
    # Local apps
    'apps.accounts',
    'apps.candidates',
    'apps.clients',
    'apps.jobs',
    'apps.pipeline',
    'apps.activities',
    'apps.dashboard',
]

# عدّل SECRET_KEY
SECRET_KEY = config('SECRET_KEY')

# عدّل DEBUG
DEBUG = config('DEBUG', default=False, cast=bool)

# عدّل DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
    }
}

# أضف في نهاية الملف:

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'static_root'

# Login URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# File Upload Settings
MAX_UPLOAD_SIZE = 10485760  # 10MB
```

#### الخطوة 2.3: إنشاء نموذج User مخصص

**افتح `apps/accounts/models.py`:**

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('recruiter', 'Recruiter'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='recruiter')
    phone = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    class Meta:
        db_table = 'users'
```

**عدّل `config/settings.py` وأضف:**

```python
# في نهاية الملف
AUTH_USER_MODEL = 'accounts.User'
```

#### الخطوة 2.4: إنشاء نموذج Candidate

**افتح `apps/candidates/models.py`:**

```python
from django.db import models
from django.conf import settings
from django.urls import reverse

class Candidate(models.Model):
    # Basic Information
    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    phone = models.CharField(max_length=50, unique=True, verbose_name="رقم الهاتف")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="البريد الإلكتروني")
    location = models.CharField(max_length=255, blank=True, verbose_name="الموقع")
    
    # Professional Information
    current_title = models.CharField(max_length=255, blank=True, verbose_name="المسمى الوظيفي الحالي")
    years_experience = models.IntegerField(null=True, blank=True, verbose_name="سنوات الخبرة")
    expected_salary = models.CharField(max_length=100, blank=True, verbose_name="الراتب المتوقع")
    availability = models.CharField(max_length=100, blank=True, verbose_name="التوفر")
    
    # Additional Information
    skills = models.TextField(blank=True, verbose_name="المهارات")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    # Metadata
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='candidates',
        verbose_name="المسؤول"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        db_table = 'candidates'
        ordering = ['-created_at']
        verbose_name = "مرشح"
        verbose_name_plural = "المرشحين"
    
    def __str__(self):
        return self.full_name
    
    def get_absolute_url(self):
        return reverse('candidates:detail', kwargs={'pk': self.pk})


class CandidateFile(models.Model):
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name="المرشح"
    )
    file = models.FileField(upload_to='cvs/', verbose_name="الملف")
    file_name = models.CharField(max_length=255, verbose_name="اسم الملف")
    file_type = models.CharField(max_length=50, verbose_name="نوع الملف")
    file_size = models.IntegerField(verbose_name="حجم الملف")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    
    class Meta:
        db_table = 'candidate_files'
        ordering = ['-uploaded_at']
        verbose_name = "ملف مرشح"
        verbose_name_plural = "ملفات المرشحين"
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.file_name}"
```

#### الخطوة 2.5: تشغيل الهجرات الأولية

```bash
# أنشئ ملفات الهجرة
python manage.py makemigrations

# نفّذ الهجرات
python manage.py migrate

# يجب أن ترى رسائل نجاح لجميع الجداول
```

#### الخطوة 2.6: إنشاء مستخدم مدير

```bash
# أنشئ superuser
python manage.py createsuperuser

# أدخل:
# - Username: admin
# - Email: admin@example.com
# - Password: (اختر كلمة مرور قوية)
# - First name: Admin
# - Last name: User
```

#### الخطوة 2.7: تسجيل النماذج في Admin

**افتح `apps/accounts/admin.py`:**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
```

**افتح `apps/candidates/admin.py`:**

```python
from django.contrib import admin
from .models import Candidate, CandidateFile

class CandidateFileInline(admin.TabularInline):
    model = CandidateFile
    extra = 0
    readonly_fields = ['file_name', 'file_type', 'file_size', 'uploaded_at']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'current_title', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['full_name', 'phone', 'email', 'skills']
    inlines = [CandidateFileInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('full_name', 'phone', 'email', 'location')
        }),
        ('Professional Information', {
            'fields': ('current_title', 'years_experience', 'expected_salary', 'availability')
        }),
        ('Additional Information', {
            'fields': ('skills', 'notes')
        }),
        ('Metadata', {
            'fields': ('owner',)
        }),
    )
```

#### الخطوة 2.8: اختبار Admin Panel

```bash
# شغّل السيرفر
python manage.py runserver

# افتح المتصفح: http://localhost:8000/admin
# سجل دخول بحساب admin
# جرب إضافة مرشح جديد من Admin Panel
```

✅ **نهاية اليوم 2 - لديك الآن:**
- مشروع Django كامل
- قاعدة بيانات PostgreSQL متصلة
- نموذج User مخصص
- نموذج Candidate جاهز
- Admin Panel يعمل

---

### اليوم 3-4: واجهات المرشحين (Views & Templates)
### Day 3-4: Candidate Views & Templates

#### الخطوة 3.1: إنشاء هيكل المجلدات

```bash
# أنشئ مجلدات القوالب
mkdir templates
mkdir templates\base
mkdir templates\candidates
mkdir templates\clients
mkdir templates\jobs
mkdir templates\pipeline
mkdir templates\dashboard
mkdir templates\accounts

# أنشئ مجلدات الملفات الثابتة
mkdir static
mkdir static\css
mkdir static\js
mkdir static\images

# أنشئ مجلد الملفات المرفوعة
mkdir media
mkdir media\cvs
```

#### الخطوة 3.2: إنشاء القالب الأساسي

**أنشئ `templates/base.html`:**

```html
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}نظام إدارة التوظيف{% endblock %}</title>
    
    <!-- Bootstrap RTL CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Custom CSS -->
    <style>
        :root {
            --primary-color: #2767b1;
            --secondary-color: #6c757d;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }
        
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(180deg, var(--primary-color) 0%, #1a4d8f 100%);
            color: white;
            padding: 20px 0;
        }
        
        .sidebar .nav-link {
            color: rgba(255, 255, 255, 0.8);
            padding: 12px 20px;
            margin: 5px 15px;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .sidebar .nav-link:hover,
        .sidebar .nav-link.active {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .sidebar .nav-link i {
            margin-left: 10px;
            width: 20px;
        }
        
        .main-content {
            padding: 30px;
        }
        
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .card-header {
            background-color: white;
            border-bottom: 2px solid var(--primary-color);
            font-weight: 600;
            padding: 15px 20px;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            border-color: var(--primary-color);
        }
        
        .btn-primary:hover {
            background-color: #1a4d8f;
            border-color: #1a4d8f;
        }
        
        .page-header {
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .badge-stage {
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav class="col-md-2 d-md-block sidebar">
                <div class="text-center mb-4">
                    <h4 class="text-white">نظام ATS</h4>
                    <small class="text-white-50">إدارة التوظيف</small>
                </div>
                
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}" 
                           href="{% url 'dashboard:home' %}">
                            <i class="fas fa-home"></i>
                            الرئيسية
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if 'candidates' in request.path %}active{% endif %}" 
                           href="{% url 'candidates:list' %}">
                            <i class="fas fa-users"></i>
                            المرشحين
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if 'clients' in request.path %}active{% endif %}" 
                           href="{% url 'clients:list' %}">
                            <i class="fas fa-building"></i>
                            العملاء
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if 'jobs' in request.path %}active{% endif %}" 
                           href="{% url 'jobs:list' %}">
                            <i class="fas fa-briefcase"></i>
                            الوظائف
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if 'pipeline' in request.path %}active{% endif %}" 
                           href="#">
                            <i class="fas fa-tasks"></i>
                            خط الإنتاج
                        </a>
                    </li>
                    
                    <hr class="bg-white">
                    
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'accounts:logout' %}">
                            <i class="fas fa-sign-out-alt"></i>
                            تسجيل الخروج
                        </a>
                    </li>
                </ul>
                
                <div class="mt-4 px-3">
                    <small class="text-white-50">
                        <i class="fas fa-user"></i>
                        {{ request.user.get_full_name }}
                    </small>
                    <br>
                    <small class="text-white-50">{{ request.user.role }}</small>
                </div>
            </nav>
            
            <!-- Main Content -->
            <main class="col-md-10 ms-sm-auto main-content">
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
                
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### الخطوة 3.3: إنشاء Views للمرشحين

**افتح `apps/candidates/views.py`:**

```python
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .models import Candidate, CandidateFile
from .forms import CandidateForm, CandidateFileForm


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
        
        return queryset


class CandidateCreateView(LoginRequiredMixin, CreateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'candidates/candidate_form.html'
    success_url = reverse_lazy('candidates:list')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        
        # Handle CV upload
        cv_file = self.request.FILES.get('cv_file')
        if cv_file:
            CandidateFile.objects.create(
                candidate=self.object,
                file=cv_file,
                file_name=cv_file.name,
                file_type=cv_file.content_type,
                file_size=cv_file.size
            )
        
        messages.success(self.request, f'تم إضافة المرشح {self.object.full_name} بنجاح')
        return response


class CandidateUpdateView(LoginRequiredMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'candidates/candidate_form.html'
    success_url = reverse_lazy('candidates:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث بيانات {self.object.full_name}')
        return response


class CandidateDetailView(LoginRequiredMixin, DetailView):
    model = Candidate
    template_name = 'candidates/candidate_detail.html'
    context_object_name = 'candidate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['files'] = self.object.files.all()
        return context
```

#### الخطوة 3.4: إنشاء Forms

**أنشئ `apps/candidates/forms.py`:**

```python
from django import forms
from .models import Candidate, CandidateFile


class CandidateForm(forms.ModelForm):
    cv_file = forms.FileField(
        required=False,
        label='السيرة الذاتية',
        help_text='PDF أو DOCX فقط، الحد الأقصى 10MB'
    )
    
    class Meta:
        model = Candidate
        fields = [
            'full_name', 'phone', 'email', 'location',
            'current_title', 'years_experience', 'expected_salary',
            'availability', 'skills', 'notes'
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_cv_file(self):
        cv_file = self.cleaned_data.get('cv_file')
        if cv_file:
            # Check file size (10MB)
            if cv_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('حجم الملف يجب أن يكون أقل من 10MB')
            
            # Check file type
            allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if cv_file.content_type not in allowed_types:
                raise forms.ValidationError('يجب أن يكون الملف PDF أو DOCX')
        
        return cv_file


class CandidateFileForm(forms.ModelForm):
    class Meta:
        model = CandidateFile
        fields = ['file']
```

**تابع في الرد التالي...**

---

✅ **حتى الآن أنجزنا:**
- ✅ إعداد البيئة التطويرية
- ✅ إنشاء مشروع Django
- ✅ إنشاء جميع التطبيقات
- ✅ إنشاء نماذج User و Candidate
- ✅ إنشاء القالب الأساسي
- ✅ إنشاء Views و Forms للمرشحين

**الخطوات القادمة:**
- إنشاء Templates للمرشحين
- إنشاء URLs
- إنشاء نماذج العملاء والوظائف
- إنشاء نظام Pipeline
- إنشاء نظام Activities
- إنشاء Dashboard

هل تريد أن أكمل الدليل؟
