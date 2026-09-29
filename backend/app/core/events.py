"""
Central registry of audit-event and notification-type identifiers.

Using string constants instead of literal strings scattered across the
codebase means a typo becomes an import error / linter warning instead
of a silently-never-matched analytics filter.
"""


class EventType:
    # --- Auth ---
    USER_REGISTERED = "user_registered"
    REGISTRATION_FAILED = "registration_failed"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"
    SUSPICIOUS_LOGIN_ACTIVITY = "suspicious_login_activity"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    PASSWORD_RESET_SUCCESS = "password_reset_success"

    # --- Files ---
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    FILE_KEY_ROTATED = "file_key_rotated"
    FILE_SHARED = "file_shared"
    PERMISSION_UPDATED = "file_permission_updated"
    PERMISSION_REVOKED = "file_permission_revoked"

    # --- Share links ---
    SHARE_LINK_CREATED = "share_link_created"
    SHARE_LINK_REVOKED = "share_link_revoked"
    PUBLIC_LINK_DOWNLOADED = "public_link_downloaded"
    PUBLIC_LINK_VIEWED = "public_link_viewed"


class NotificationType:
    NEW_LOGIN = "new_login"
    FILE_SHARED = "file_shared"
    FILE_DOWNLOADED = "file_downloaded"
    SECURITY_ALERT = "security_alert"
    LINK_EXPIRING_SOON = "link_expiring_soon"
    KEY_ROTATED = "key_rotated"


# Severity levels, ordered low -> high. Kept as plain strings (not an
# Enum/DB check constraint) so ops can add a level without a migration.
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"