# API Documentation

This document lists the available API endpoints for the Pharma Platform.

## 🔐 Authentication (`/api/auth/`)

All authentication endpoints are rate-limited to prevent abuse.

| Endpoint | Method | Description | Rate Limit |
| :--- | :--- | :--- | :--- |
| `register/` | `POST` | Register a new user account | 5/hr |
| `token/` | `POST` | Obtain JWT access/refresh tokens | 5/min |
| `token/refresh/` | `POST` | Refresh an expired access token | 10/min |
| `token/verify/` | `POST` | Verify a token's validity | - |
| `validate-password/` | `POST` | Check password strength before registration | - |
| `logout/` | `POST` | Blacklist the refresh token and logout | - |
| `profile/` | `GET`, `PATCH` | Retrieve or update current user profile | - |
| `password/change/` | `POST` | Change authenticated user's password | - |
| `password/reset/` | `POST` | Request password reset email | - |
| `password/reset/confirm/` | `POST` | Confirm password reset with token | - |

### Registration Payload

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!",
  "phone_number": "+919876543210",
  "user_type": "patient"
}
```

## 🏥 Other Modules

The following modules are currently in development and will expose API endpoints soon:

- **`pharmacies`**: Pharmacy and medicine management.
- **`prescriptions`**: Prescription upload and verification.
- **`orders`**: Order placement and lifecycle management.
