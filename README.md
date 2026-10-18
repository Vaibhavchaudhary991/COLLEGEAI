# AI College Assistant

A production-ready Django web application that serves as a foundation for an AI-powered college assistant platform. Built with Django REST Framework, JWT authentication, and a modern dark-themed Bootstrap 5 UI — designed so that RAG/AI functionality can be cleanly plugged in later.

---

## 📋 Project Overview

AI College Assistant is a SaaS-style academic platform where:

- **Students** can browse course documents, manage their chat history, and interact with the AI assistant (placeholder response until RAG is integrated)
- **Admins** can upload/manage documents, view system statistics, and manage users

The architecture is deliberately structured so the AI/RAG layer is **isolated in a single service function** — swapping in the full pipeline requires zero refactoring of views, models, or URLs.

---

## ✨ Features

### Accounts
- Custom User model with role-based access (`student` / `admin`)
- Registration, Login, Logout (Django session auth + JWT)
- User profile with avatar upload
- API authentication via JWT (Bearer tokens)

### Documents
- Upload PDF, DOCX, and TXT files (max 10 MB)
- File type & size validation at both serializer and form levels
- Activate/deactivate documents (inactive = hidden from students)
- Download documents
- Admin-only upload and delete; students can view active documents

### Chat
- Create chat sessions and send messages
- Placeholder AI response (`"AI functionality will be available soon."`)
- Full message history per session
- Session auto-titles based on first user message
- API-driven frontend using `fetch()` + CSRF cookie

### Dashboards
- **Student dashboard**: Document count, chat session count, recent activity
- **Admin dashboard**: Total users/documents/sessions, quick actions, recent uploads/registrations

### API (REST)
- JWT-protected endpoints for all resources
- Consistent JSON responses with standard HTTP status codes
- DRF serializers with proper validation

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 |
| API | Django REST Framework 3.x |
| Authentication | Django sessions + djangorestframework-simplejwt |
| Database | SQLite (development) |
| File Uploads | Django media storage |
| Environment | python-dotenv |
| Frontend | Django Templates + Bootstrap 5.3 + Bootstrap Icons |
| Fonts | Google Fonts (Inter) |

---

## 📁 Project Structure

```
college_ai/
├── college_ai/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # User auth app
│   ├── models.py             # Custom User model
│   ├── serializers.py        # Register & Profile serializers
│   ├── views.py              # API + Template views
│   ├── permissions.py        # IsAdminRole permission
│   ├── admin.py              # Django admin config
│   ├── urls.py               # Template URL routes
│   ├── api_urls.py           # API URL routes
│   └── management/
│       └── commands/
│           └── create_sample_data.py
├── documents/                # Document management app
│   ├── models.py             # Document model
│   ├── serializers.py        # Document serializers with validation
│   ├── views.py              # API + Template views
│   ├── permissions.py        # Document-level permissions
│   ├── admin.py
│   ├── urls.py
│   ├── api_urls.py
│   └── services/             # ← Future text-extraction service goes here
├── chat/                     # Chat app
│   ├── models.py             # ChatSession, ChatMessage
│   ├── serializers.py        # Chat serializers
│   ├── views.py              # API + Template views
│   ├── admin.py
│   ├── urls.py
│   ├── api_urls.py
│   └── services/
│       └── ai_service.py     # ← RAG integration point (placeholder now)
├── dashboard/                # Dashboard routing app
│   ├── views.py              # Student + Admin dashboards
│   └── urls.py
├── templates/                # All HTML templates
│   ├── base.html             # Authenticated layout (sidebar + topbar)
│   ├── home/index.html       # Public landing page
│   ├── accounts/             # login, register, profile
│   ├── chat/                 # chat interface
│   ├── dashboard/            # student + admin dashboards
│   └── documents/            # list, detail, upload, admin list
├── static/
│   └── css/main.css          # Custom dark SaaS stylesheet
├── media/                    # Uploaded files (git-ignored)
├── .env                      # Secrets (git-ignored)
├── .env.example              # Template for .env
├── requirements.txt
└── manage.py
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd college_ai
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MAX_UPLOAD_SIZE_MB=10
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser / sample data

**Option A — Create superuser interactively:**

```bash
python manage.py createsuperuser
```

> After creating the superuser, log into Django Admin at `/admin/` and set the user's **role** to `admin`.

**Option B — Use the built-in sample data command (recommended for development):**

```bash
python manage.py create_sample_data
```

This creates:
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin (superuser) |
| `student` | `student123` | Student |

### 7. Start the development server

```bash
python manage.py runserver
```

The app is now available at **http://127.0.0.1:8000/**

---

## 🔐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum document upload size |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | JWT access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | JWT refresh token lifetime |

---

## 🌐 URL Routes

### Template Pages

| URL | Description | Access |
|---|---|---|
| `/` | Landing page | Public |
| `/login/` | Login form | Public |
| `/register/` | Registration form | Public |
| `/profile/` | User profile | Authenticated |
| `/dashboard/` | Redirects by role | Authenticated |
| `/dashboard/student/` | Student dashboard | Students |
| `/dashboard/admin/` | Admin dashboard | Admins |
| `/documents/` | Document list | Authenticated |
| `/documents/<id>/` | Document detail | Authenticated |
| `/documents/upload/` | Upload form | Admins |
| `/documents/admin/` | Document management | Admins |
| `/chat/` | Chat interface | Authenticated |
| `/chat/<id>/` | Specific chat session | Authenticated |
| `/admin/` | Django admin | Staff |

### API Endpoints

| Method | URL | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register new user | None |
| `POST` | `/api/auth/login/` | Login, receive JWT | None |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT | None |
| `GET/PATCH` | `/api/auth/profile/` | View/update profile | JWT |
| `GET` | `/api/documents/` | List documents | JWT |
| `POST` | `/api/documents/` | Upload document | JWT (Admin) |
| `GET` | `/api/documents/<id>/` | Document detail | JWT |
| `DELETE` | `/api/documents/<id>/` | Delete document | JWT (Admin) |
| `PATCH` | `/api/documents/<id>/toggle/` | Activate/deactivate | JWT (Admin) |
| `GET/POST` | `/api/chat/sessions/` | List/create sessions | JWT |
| `GET/DELETE` | `/api/chat/sessions/<id>/` | Session detail/delete | JWT |
| `GET/POST` | `/api/chat/sessions/<id>/messages/` | List/send messages | JWT |

---

## 👥 User Roles

### Student
- Register/login to the platform
- View all **active** documents
- Download documents
- Create and manage their own chat sessions
- Cannot access admin-only pages or APIs

### Admin
- All student permissions, plus:
- Upload new documents (PDF, DOCX, TXT)
- Activate/deactivate documents
- Delete documents
- View system-wide statistics (admin dashboard)
- Access Django admin panel

---

## 🤖 Future RAG Integration

The application is architected to accept the RAG pipeline with **zero refactoring**.

### Integration Point

**File:** `chat/services/ai_service.py`

**Current placeholder:**
```python
def generate_response(question: str, chat_history: list = None) -> str:
    return "AI functionality will be available soon."
```

**Future RAG pipeline (replace the function body):**
```
Question
  → Embedding Model (e.g. text-embedding-ada-002)
  → Vector Search (Chroma / Pinecone / Weaviate)
  → Retrieved Context Chunks (top-k)
  → LLM Call (GPT-4, Gemini, Groq, etc.)
  → Response string
```

### Document Processing Hook

When documents are uploaded, add processing in `documents/services/` (already scaffolded):

```
Document Upload
  → Text Extraction (PyMuPDF / python-docx)
  → Chunking
  → Embedding
  → Vector Store Upsert
```

No views, models, URLs, or templates need to change when RAG is added.

---

## 🧪 Testing the API

### Register a user

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test1234","password_confirm":"test1234"}'
```

### Login and get tokens

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Get profile (with JWT)

```bash
curl http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer <your-access-token>"
```

### Create a chat session

```bash
curl -X POST http://127.0.0.1:8000/api/chat/sessions/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Chat"}'
```

### Send a message

```bash
curl -X POST http://127.0.0.1:8000/api/chat/sessions/1/messages/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is machine learning?"}'
```

---

## 📦 Dependencies

```
Django>=4.2,<5.0
djangorestframework>=3.14,<4.0
djangorestframework-simplejwt>=5.3,<6.0
python-dotenv>=1.0,<2.0
Pillow>=10.0,<11.0
```

---

## 📄 License

MIT
