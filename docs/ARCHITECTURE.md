# Project Architecture

This document describes the high-level architecture of the Pharma Platform.

## 🏛 System Overview

The Pharma Platform is a Django-based e-commerce backend designed for pharmacies and patients. It follows a modular monolith architecture with a clear separation of concerns across different applications.

## 📂 Core Components

### 1. `accounts` (Identity & Access)

- **Custom User Model**: Extends `AbstractUser` to support `email` as the primary identifier.
- **Roles & RBAC**: Supports `patient` and `pharmacy_admin` with custom DRF permission classes (`IsPatient`, `IsPharmacyAdmin`, `IsVerifiedPharmacy`).
- **Profile Management**: Stateless profile retrieval and updates for authenticated users.
- **Password Lifecycle**: Integrated password strength validation, secure change workflow, and token-based reset system.
- **Authentication**: Stateless JWT-based authentication using `djangorestframework-simplejwt`.
- **Security**: Implements IP-based rate limiting on sensitive endpoints and comprehensive security logging.

### 2. `pharmacies` (Inventory)

- **Pharmacy**: Manages business identity and license verification.
- **Medicine**: Product catalog with inventory tracking per pharmacy.

### 3. `prescriptions` (File Storage)

- **S3 Integration**: Custom storage backend located in `config/storage_backends.py`.
- **Security**: Files are stored in a private S3 bucket. Access is granted via short-lived presigned URLs.
- **Encryption**: AES-256 Server-Side Encryption (SSE-S3).

### 4. `orders` (Workflow)

- **StateMachine**: Implements a strict sequential workflow for order status.
- **Validation**: Ensures that orders can only be placed with verified prescriptions (when required).

## 🛠 Infrastructure

- **Database**: PostgreSQL for persistent storage.
- **Cache**: Django's cache framework (used for rate limiting).
- **Storage**: AWS S3 for media files (prescriptions).
- **Environment**: Configuration managed via `.env` files using `python-decouple`.

## 🧪 Testing Strategy

- **Pytest**: Primary testing framework.
- **In-Memory SQLite**: Used for running tests to maximize performance.
- **Parallel Testing**: `pytest-xdist` is configured to run tests across multiple CPU cores.
- **Database Agnosticism**: The test suite is designed to be compatible with both PostgreSQL and SQLite.

## 🔐 Security Model

1. **Authentication**: JWT with short-lived access tokens.
2. **Authorization**: DRF Permission classes and custom role-based checks.
3. **Data Security**: Encryption at rest for prescriptions, environment-based secrets.
4. **Resiliency**: Rate limiting on login and registration to prevent brute-force attacks.
