# Recruitment Agency ATS - MVP

A comprehensive Applicant Tracking System (ATS) designed for recruitment agencies to manage candidates, clients, job orders, and track applications through a complete pipeline.

## 🎯 Project Overview

This ATS enables recruitment agencies to:
- Store and manage candidates with CV files
- Manage clients and their contacts
- Create and track job orders
- Link candidates to jobs through a pipeline
- Track all activities and interactions
- Generate basic reports and analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd rec
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=ats_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

5. **Create database**
```bash
# In PostgreSQL
createdb ats_db
```

6. **Run migrations**
```bash
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Load initial data (pipeline stages)**
```bash
python manage.py loaddata initial_stages
```

9. **Run development server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 📋 Features

### MVP Features (Week 1-4)

#### Candidate Management
- ✅ Create/edit candidates
- ✅ Upload CV files (PDF/DOCX)
- ✅ Search by name, phone, email, skills
- ✅ View candidate profile with timeline

#### Client Management
- ✅ Create/edit clients
- ✅ Manage multiple client contacts
- ✅ View client details with all jobs

#### Job Order Management
- ✅ Create/edit job orders
- ✅ Link jobs to clients
- ✅ Filter by status (Open/On Hold/Closed)

#### Pipeline Management
- ✅ Add candidates to jobs
- ✅ Track through stages (Sourced → Hired/Rejected)
- ✅ Visual pipeline board
- ✅ Quick actions (Submit to Client, Schedule Interview)

#### Activity Tracking
- ✅ Manual activities (Call, Email, WhatsApp, Note)
- ✅ Automatic logging (stage changes, submissions)
- ✅ Complete timeline view

#### Dashboard & Reports
- ✅ Open jobs count
- ✅ Applications by stage
- ✅ Recent candidates
- ✅ Activity feed

## 🗂️ Project Structure

```
rec/
├── config/                 # Django settings
├── apps/
│   ├── accounts/          # User authentication
│   ├── candidates/        # Candidate management
│   ├── clients/           # Client management
│   ├── jobs/              # Job orders
│   ├── pipeline/          # Applications & pipeline
│   ├── activities/        # Activity logging
│   └── dashboard/         # Dashboard & reports
├── static/                # CSS, JS, images
├── media/                 # Uploaded files (CVs)
├── templates/             # Base templates
└── requirements.txt
```

## 📊 Database Schema

### Core Models

1. **User** - Admin and Recruiter roles
2. **Candidate** - Candidate profiles with CVs
3. **Client** - Client companies
4. **ClientContact** - Client contact persons
5. **JobOrder** - Job vacancies
6. **Application** - Candidate ↔ Job link
7. **PipelineStage** - Pipeline stages
8. **Activity** - Activity timeline

## 🔐 User Roles

### Admin
- Full system access
- Manage users
- Manage pipeline stages
- View all data

### Recruiter
- Create/edit candidates
- Create/edit clients
- Create/edit jobs
- Manage pipeline
- Add activities

## 🎨 Pipeline Stages

1. **Sourced** - Candidate identified
2. **Screened** - Initial screening completed
3. **Submitted to Client** - Profile sent to client
4. **Interview** - Interview in progress
5. **Offer** - Offer stage
6. **Hired** - Placement confirmed ✅
7. **Rejected** - Not moving forward ❌

## 🧪 Testing

Run tests:
```bash
python manage.py test
```

Run specific app tests:
```bash
python manage.py test apps.candidates
python manage.py test apps.pipeline
```

## 📈 Future Enhancements

### Phase 2 (Month 2-3)
- Full-text CV search
- Duplicate detection
- Task/reminder system
- Email templates
- Basic automation

### Phase 3 (Month 4+)
- CV parsing
- Email/WhatsApp integration
- Calendar integration
- Client portal
- Advanced permissions
- Job board integration

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## 📝 License

[Your License Here]

## 📞 Support

For support, email support@yourcompany.com or create an issue in the repository.

---

**Built with ❤️ for recruitment agencies**
