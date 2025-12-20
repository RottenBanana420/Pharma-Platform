# Pharma Platform - Django E-Commerce Application

A production-ready Django-based pharmacy e-commerce platform with PostgreSQL database, REST API, and comprehensive testing framework.

## Features

- **Django 6.0** with Django REST Framework
- **PostgreSQL** database with environment-based configuration
- **JWT Authentication** using `djangorestframework-simplejwt`
- **Custom User Model** with role-based access (Patient/Pharmacy Admin)
- **Modular Settings** (base, development, production, testing)
- **Indian Locale** (Asia/Kolkata timezone, en-in language, +91 phone number validation)
- **Order Management** with sequential status workflow (Placed -> Confirmed -> Shipped -> Delivered)
- **Pharmacy Management** including license verification and medicine inventory
- **Prescription Workflow** with upload, verification, and rejection handling
- **Comprehensive Testing** with pytest, parallel execution, and in-memory SQLite for speed
- **AWS S3 Integration** ready for production static/media files
- **Stripe Payment** integration ready
- **Production-ready** security settings with strict validation for `SECRET_KEY` and `ALLOWED_HOSTS`
- **Database-Agnostic Test Suite** compatible with PostgreSQL and SQLite

## Core Applications

The project is organized into modular Django applications located in the `apps/` directory:

### 1. `accounts`

- **User Model**: Custom `User` model extending `AbstractUser`.
- **Fields**: Email (unique), Phone Number (+91 validation), User Type (Patient/Admin), Verification Status.
- **Authentication**: JWT-based authentication for secure API access.

### 2. `pharmacies`

- **Pharmacy**: Business details, license number (unique), contact info, and verification status.
- **Medicine**: Inventory management with pricing, stock tracking, and per-pharmacy uniqueness.

### 3. `prescriptions`

- **Prescription**: Patient-uploaded prescriptions (S3 storage).
- **Workflow**: Verification system allowing admins to verify or reject prescriptions with reasons.
- **Validation**: Enforces terminal states (cannot revert from verified/rejected).

### 4. `orders`

- **Order**: Links patients, pharmacies, and verified prescriptions.
- **Order Items**: Line items with point-of-sale pricing and quantity tracking.
- **Workflow**: Strict sequential status transitions and business rule enforcement (e.g., tracking number required for shipping).

## Prerequisites

- Python 3.12+ (installed via pyenv)
- PostgreSQL
- pyenv and pyenv-virtualenv

## Installation

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

Edit `.env` with your database credentials and other settings.

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

## Running the Application

### Development Server

```bash
# Make sure DJANGO_ENVIRONMENT is set to development (default)
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

## Testing

The project uses pytest with comprehensive test coverage and parallel execution.

### Run all tests

```bash
DJANGO_ENVIRONMENT=testing pytest
```

### Run specific test file

```bash
DJANGO_ENVIRONMENT=testing pytest apps/accounts/tests/test_models.py
```

### Run with coverage report

```bash
DJANGO_ENVIRONMENT=testing pytest --cov=. --cov-report=html
```

### Run tests in parallel

```bash
DJANGO_ENVIRONMENT=testing pytest -n auto
```

### Infrastructure Optimizations

- **In-Memory SQLite**: Used during tests for extreme speed.
- **Parallel Execution**: Leverages `pytest-xdist` to utilize all CPU cores.
- **Fast Hashing**: MD5 hashing used for passwords in tests to reduce overhead.
- **Database-Agnosticism**: Tests use Django introspection to maintain compatibility across different database engines (PostgreSQL/SQLite).

## Project Structure

```text
Pharma-Platform/
├── apps/                 # Core applications
│   ├── accounts/         # User management & Authentication
│   ├── orders/           # Order management & Workflows
│   ├── pharmacies/       # Pharmacy & Medicine inventory
│   └── prescriptions/    # Prescription uploads & Verification
├── config/               # Project configuration
│   ├── settings/        # Modular settings
│   │   ├── base.py      # Base settings
│   │   ├── development.py # Development settings
│   │   ├── production.py  # Production settings
│   │   └── testing.py   # Testing settings (Optimized)
│   ├── urls.py          # URL configuration
│   ├── wsgi.py          # WSGI configuration
│   └── asgi.py          # ASGI configuration
├── tests/               # Global test configuration
│   ├── conftest.py      # Pytest fixtures
│   └── test_setup.py    # Setup verification tests
├── logs/                # Application logs
├── static/              # Static files
├── media/               # Media files
├── templates/           # Django templates
├── manage.py            # Django management script
├── pytest.ini           # Pytest configuration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Environment Variables

Key environment variables:

- `SECRET_KEY` - Django secret key (Required in production)
- `ALLOWED_HOSTS` - List of allowed hostnames (Required in production)
- `DJANGO_ENVIRONMENT` - Environment (`development`/`production`/`testing`)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database credentials
- `CORS_ALLOWED_ORIGINS` - Origins allowed for cross-site requests

## Production Verification

To ensure the application is ready for production, run:

```bash
DJANGO_ENVIRONMENT=production python manage.py check --deploy
```

This verifies critical security settings including `SECRET_KEY`, `ALLOWED_HOSTS`, HTTPS settings, and more.

## Development

The project uses a modular settings structure loaded based on `DJANGO_ENVIRONMENT`. This ensures clean separation between development, production, and high-performance testing environments.

## License

MIT License - See [LICENSE](LICENSE) file for details.
