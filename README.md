# Pharma Platform - Django E-Commerce Application

A production-ready Django-based pharmacy e-commerce platform with PostgreSQL database, REST API, and comprehensive testing framework.

## 🚀 Key Features

- **Django 6.0** with Django REST Framework
- **PostgreSQL** database with environment-based configuration
- **JWT Authentication** using `djangorestframework-simplejwt`
  - Short-lived access tokens (15m) and long-lived refresh tokens (7d)
  - Token rotation and blacklisting for enhanced security
  - Custom claims (user type, verification status) in JWT payloads
- **Rate Limiting & Security**
  - IP-based rate limiting for authentication endpoints
  - Customizable throttling rates for login, registration, and token refresh
  - CORS configuration for secure cross-origin requests
  - Strict production security validation (`SECRET_KEY`, `ALLOWED_HOSTS`, HTTPS)
- **Custom User Model** with role-based access (Patient/Pharmacy Admin)
- **Role-Based Access Control (RBAC)**
  - Custom DRF permission classes (`IsPatient`, `IsPharmacyAdmin`, `IsVerifiedPharmacy`)
  - Strict endpoint protection based on user roles and verification status
- **User Profile Management**
  - Authenticated profile retrieval
  - Partial updates for contact and personal information
- **Password Management**
  - Secure password change for authenticated users (with old password verification)
  - Account recovery via password reset request and confirmation (token-based)
- **Indian Locale Support**
  - Asia/Kolkata timezone and `en-in` language
  - Indian phone number validation (+91 format)
- **Order Management** with sequential status workflow (Placed → Confirmed → Shipped → Delivered)
- **Pharmacy Management** including license verification and medicine inventory
- **Prescription Workflow** with upload, verification, and rejection handling
- **Comprehensive Testing** with pytest, parallel execution, and in-memory SQLite for speed
- **AWS S3 Integration** with custom storage backend for prescription files
  - File validation (size, extension, MIME type, corruption detection)
  - Intelligent path generation with collision prevention
  - Server-side encryption (SSE-S3 AES-256)
  - Private file access with presigned URLs
  - Metadata support for auditing

## 📁 Core Applications (`apps/`)

The project is organized into modular Django applications:

| Application | Responsibility |
| :--- | :--- |
| **`accounts`** | User management, JWT Authentication, Password Management (Change/Reset), Rate limiting, RBAC Permissions, User Profiles |
| **`pharmacies`** | Business details, license management, Medicine inventory & stock tracking |
| **`prescriptions`** | Patient uploads, S3 storage integration, Admin verification workflow |
| **`orders`** | Order lifecycle, sequential status transitions, business rule enforcement |

## 🛠 Prerequisites

- Python 3.12+ (managed via `pyenv`)
- PostgreSQL
- `pyenv` and `pyenv-virtualenv`

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Pharma-Platform
```

### 2. Set up Python environment

```bash
# Install Python 3.12.12 if not already installed
pyenv install 3.12.12

# Create virtual environment
pyenv virtualenv 3.12.12 pharma-platform-env

# Activate virtual environment
pyenv local pharma-platform-env
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update with your configuration:

```bash
cp .env.example .env
```

### 5. Set up PostgreSQL database

```bash
# Create database
createdb pharma_platform_dev

# Run migrations
python manage.py migrate
```

### 6. Create superuser (optional)

```bash
python manage.py createsuperuser
```

## 🚀 Running the Application

### Development Server

```bash
# Make sure DJANGO_ENVIRONMENT is set to development (default)
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

## 🧪 Testing

The project uses `pytest` with comprehensive test coverage and parallel execution.

### Run all tests

```bash
DJANGO_ENVIRONMENT=testing pytest
```

### Run specific test file

```bash
DJANGO_ENVIRONMENT=testing pytest apps/accounts/tests/test_registration.py
```

### Run with coverage report

```bash
DJANGO_ENVIRONMENT=testing pytest --cov=. --cov-report=html
```

### Infrastructure Optimizations

- **In-Memory SQLite**: Used during tests for extreme speed.
- **Parallel Execution**: Leverages `pytest-xdist` to utilize all CPU cores.
- **Fast Hashing**: MD5 hashing used for passwords in tests to reduce overhead.
- **Database-Agnosticism**: Tests maintain compatibility across PostgreSQL and SQLite.

## 🏗 Project Structure

```text
Pharma-Platform/
├── apps/               # Core applications (accounts, orders, pharmacies, prescriptions)
├── config/             # Project configuration and settings
│   ├── settings/       # Modular settings (base, development, production, testing)
│   ├── storage_backends.py # Custom AWS S3 storage implementation
│   └── urls.py         # Root URL configuration
├── tests/              # Global infrastructure and setup tests
├── docs/               # Project documentation
├── logs/               # Application log files
├── static/             # Static assets
├── media/              # Locally stored media files
├── manage.py           # Django management script
├── pytest.ini          # Pytest configuration
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (local-only)
└── .env.example        # Environment variables template
```

## 🔐 Security & Production

To ensure the application is ready for production, run the deployment check:

```bash
DJANGO_ENVIRONMENT=production python manage.py check --deploy
```

Key security features:

- **Strict Environment Validation**: Fails early if `SECRET_KEY` or `ALLOWED_HOSTS` are misconfigured in production.
- **JWT Security**: Tokens are short-lived with rotation enabled.
- **AWS Security**: Prescriptions are stored privately with AES-256 encryption and accessed via expiring presigned URLs.
- **Security Logging**:
  - Continuous monitoring of authentication attempts (success/failure)
  - Audit logging for password changes and resets
  - IP-address tracking for sensitive registration and login events
- **Advanced Throttling**: Tiered rate limits based on endpoint sensitivity (Registration, Login, Token Refresh).

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.
