# TrustShare Security Design

## 1. Objective

TrustShare protects sensitive files through secure authentication, authorization, encryption, activity monitoring, and controlled sharing.

## 2. Authentication

- Users register with an email and password.
- Passwords are hashed using bcrypt before storage.
- Passwords are never stored as plain text.
- Login generates a JWT access token.
- Protected API endpoints require a valid JWT token.
- Future enhancement: multi-factor authentication and OAuth login.

## 3. Authorization

TrustShare uses Role-Based Access Control (RBAC).

| Role | Permissions |
|---|---|
| Admin | Manage users, view audit logs, monitor system activity |
| User | Upload, manage, and share their own files |
| Recipient | Access only files explicitly shared with them |

The backend validates file ownership, user permissions, link status, and expiry before allowing access.

## 4. File Encryption

1. User uploads a file through the React frontend.
2. FastAPI validates the file type, size, and user permission.
3. FastAPI generates a unique encryption key for the file.
4. The file is encrypted using AES-256-GCM.
5. Only the encrypted file is stored in object storage.
6. File metadata and key references are stored in PostgreSQL.
7. The actual encryption key is protected by a master key or cloud key-management service.
8. During download, the file is decrypted temporarily in memory for authorized users.

## 5. Secure Sharing

Share links include:

- Secure randomly generated token
- Token hash stored in the database instead of the raw token
- Expiration date and time
- View or download permission
- Optional download limit
- Ability for the owner to revoke the link

## 6. Upload Security

Before accepting a file, the backend checks:

- Allowed file extension
- MIME type
- Maximum file size
- User authentication and authorization
- Potential malware-scanning integration

## 7. API Security

- HTTPS-only communication in deployment
- JWT validation for protected routes
- CORS restricted to the approved frontend domain
- Rate limiting for login, upload, and share-link endpoints
- Pydantic request validation
- Secure HTTP headers
- Generic error messages that do not expose sensitive system details

## 8. Audit Logging

The system records:

- Registration, login, and failed-login attempts
- File uploads, updates, downloads, and deletes
- Permission changes
- Share-link creation, access, expiration, and revocation
- Unauthorized-access attempts
- Security-related errors

Audit logs will be stored separately from core data, using MongoDB or a centralized logging service.

## 9. Secrets Management

The following values must never be committed to GitHub:

- Database password
- JWT secret key
- Encryption master key
- Cloud storage credentials
- Email-service credentials

Local secrets are stored in `.env` files, which must remain in `.gitignore`.

## 10. Security Design Principles

- Least-privilege access
- Encrypt data in transit and at rest
- Validate every user request
- Never trust frontend-only permission checks
- Keep security logs for investigation
- Rotate keys and tokens when required
- Use dependency updates and security testing before deployment