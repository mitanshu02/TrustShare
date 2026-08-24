# TrustShare Database Design

## Database Technology

- Primary database: PostgreSQL
- Primary keys: UUID
- Timestamps: All major tables use `created_at` and `updated_at`
- File content: Stored as encrypted data in object storage, not in PostgreSQL
- Audit logs: Stored separately in MongoDB

---

## 1. Users

Stores registered users and their access role.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| full_name | VARCHAR(150) | Required |
| email | VARCHAR(255) | Required, unique |
| password_hash | VARCHAR(255) | Required |
| role | VARCHAR(20) | `admin` or `user` |
| account_status | VARCHAR(20) | `active`, `inactive`, or `locked` |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

---

## 2. Folders

Stores user-created folders.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| owner_id | UUID | Foreign key → users.id |
| parent_folder_id | UUID | Foreign key → folders.id, optional |
| name | VARCHAR(255) | Required |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

---

## 3. Files

Stores encrypted-file metadata. Actual file content is stored in encrypted object storage.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| owner_id | UUID | Foreign key → users.id |
| folder_id | UUID | Foreign key → folders.id, optional |
| original_name | VARCHAR(255) | Required |
| storage_key | VARCHAR(500) | Required, unique |
| content_type | VARCHAR(100) | Required |
| size_bytes | BIGINT | Required |
| checksum | VARCHAR(64) | SHA-256 checksum |
| encryption_key_reference | VARCHAR(255) | Key reference only; never the actual key |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |
| deleted_at | TIMESTAMP | Optional soft delete |

---

## 4. File Versions

Stores previous versions of a file.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| file_id | UUID | Foreign key → files.id |
| version_number | INTEGER | Required |
| storage_key | VARCHAR(500) | Required, unique |
| size_bytes | BIGINT | Required |
| checksum | VARCHAR(64) | SHA-256 checksum |
| encryption_key_reference | VARCHAR(255) | Key reference only |
| uploaded_by | UUID | Foreign key → users.id |
| created_at | TIMESTAMP | Required |

---

## 5. File Permissions

Stores direct permissions granted to specific users.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| file_id | UUID | Foreign key → files.id |
| user_id | UUID | Foreign key → users.id |
| access_level | VARCHAR(20) | `view` or `download` |
| granted_by | UUID | Foreign key → users.id |
| expires_at | TIMESTAMP | Optional |
| created_at | TIMESTAMP | Required |

Constraint: One permission record per user per file.

---

## 6. Share Links

Stores secure temporary file-sharing links.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| file_id | UUID | Foreign key → files.id |
| created_by | UUID | Foreign key → users.id |
| token_hash | VARCHAR(255) | Required, unique; never store the raw token |
| access_level | VARCHAR(20) | `view` or `download` |
| expires_at | TIMESTAMP | Required |
| max_downloads | INTEGER | Optional |
| download_count | INTEGER | Default: 0 |
| is_active | BOOLEAN | Default: true |
| created_at | TIMESTAMP | Required |
| revoked_at | TIMESTAMP | Optional |

---

## 7. Downloads

Tracks download activity.

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| file_id | UUID | Foreign key → files.id |
| share_link_id | UUID | Foreign key → share_links.id, optional |
| user_id | UUID | Foreign key → users.id, optional |
| ip_address | VARCHAR(45) | Optional |
| user_agent | TEXT | Optional |
| downloaded_at | TIMESTAMP | Required |

---

## Relationships

- One user owns many folders and files.
- One folder can contain many files and subfolders.
- One file can have many versions, permissions, share links, and downloads.
- One user can receive permissions for many files.
- One share link can be used for many downloads.