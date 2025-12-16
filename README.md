# Pharma Platform - Django E-Commerce Application

A production-ready Django-based pharmacy e-commerce platform with PostgreSQL database, REST API, and comprehensive testing framework.

## Features

- **Django 6.0** with Django REST Framework
- **PostgreSQL** database with environment-based configuration
- **JWT Authentication** using djangorestframework-simplejwt
- **Custom User Model** with role-based access (Patient/Pharmacy Admin)
- **Modular Settings** (base, development, production, testing)
- **Indian Locale** (Asia/Kolkata timezone, en-in language, +91 phone number validation)
- **Comprehensive Testing** with pytest, pytest-django, and parallel execution
- **AWS S3 Integration** ready for production static/media files
- **Stripe Payment** integration ready
- **Production-ready** security settings

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
DJANGO_ENVIRONMENT=testing pytest tests/test_setup.py
```

### Run with coverage report

```bash
DJANGO_ENVIRONMENT=testing pytest --cov=. --cov-report=html
```

### Run tests in parallel

```bash
DJANGO_ENVIRONMENT=testing pytest -n auto
```

### Test markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests (can be excluded with `-m "not slow"`)

## Project Structure

```text
Pharma-Platform/
├── accounts/               # User management & Authentication
├── config/                 # Project configuration
│   ├── settings/          # Modular settings
│   │   ├── __init__.py   # Settings loader
│   │   ├── base.py       # Base settings
│   │   ├── development.py # Development settings
│   │   ├── production.py  # Production settings
│   │   └── testing.py    # Testing settings
│   ├── urls.py           # URL configuration
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── orders/                 # Order management
├── pharmacies/             # Pharmacy management
├── prescriptions/          # Prescription management
├── tests/                 # Test suite
│   ├── conftest.py       # Pytest configuration
│   └── test_setup.py     # Setup verification tests
├── logs/                  # Application logs
├── static/               # Static files
├── media/                # Media files
├── templates/            # Django templates
├── manage.py             # Django management script
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Environment Variables

Key environment variables (see `.env.example` for complete list):

- `SECRET_KEY` - Django secret key
- `DJANGO_ENVIRONMENT` - Environment (development/production/testing)
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port

## Development

### Settings Structure

The project uses a modular settings structure:

- `base.py` - Common settings for all environments
- `development.py` - Development-specific settings
- `production.py` - Production-specific settings
- `testing.py` - Test-specific settings (in-memory SQLite, optimizations)

The appropriate settings module is loaded based on the `DJANGO_ENVIRONMENT` variable.

### Logging

Logs are written to both console and file (`logs/django.log`). The logging level is:

- `DEBUG` in development
- `INFO` in production
- Disabled in testing

## Production Deployment

1. Set `DJANGO_ENVIRONMENT=production`
2. Configure all required environment variables
3. Set `DEBUG=False` (automatic in production settings)
4. Configure `ALLOWED_HOSTS`
5. Set up PostgreSQL database
6. Run migrations: `python manage.py migrate`
7. Collect static files: `python manage.py collectstatic`
8. Configure web server (nginx/Apache) and WSGI server (gunicorn/uwsgi)

### Optional: AWS S3 for Static/Media Files

Set `USE_S3=True` and configure AWS credentials in environment variables.

## Testing Philosophy

This project follows **Test-Driven Development (TDD)** principles:

1. Write tests first
2. Watch them fail
3. Write minimal code to pass
4. Refactor

All tests are designed to fail if configuration is incorrect - **fix the configuration, never modify the tests**.

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Implement your changes
5. Ensure all tests pass
6. Submit a pull request
