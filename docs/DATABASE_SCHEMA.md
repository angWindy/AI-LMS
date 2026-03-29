# Database Schema Documentation

## Tổng quan

AI-LMS sử dụng PostgreSQL 15 làm cơ sở dữ liệu chính với SQLAlchemy 2.0 ORM. Schema được thiết kế để hỗ trợ một hệ thống LMS đầy đủ với khả năng mở rộng cho AI integration.

## Database Information

- **DBMS**: PostgreSQL 15-alpine
- **ORM**: SQLAlchemy 2.0.25+
- **Migration Tool**: Alembic 1.13.1
- **Character Set**: UTF-8
- **Timezone**: UTC (with timezone-aware timestamps)
- **Connection Pool**: Configured via SQLAlchemy

## Entity Relationship Diagram

```
                                 ┌──────────────┐
                          ┌──────│    users     │──────┐
                          │      └──────────────┘      │
                          │                             │
                          ↓                             ↓
                   ┌──────────────┐            ┌────────────────┐
            ┌──────│   courses    │────┐       │  refresh_tokens│
            │      └──────────────┘    │       └────────────────┘
            │                           │
            ↓                           ↓
      ┌──────────┐              ┌────────────┐
      │  lessons │              │enrollments │
      └──────────┘              └────────────┘
            │                           │
     ┌──────┴──────┐                   ↓
     ↓             ↓           ┌─────────────────┐
┌──────────┐  ┌──────────────┐│ lesson_progress │
│materials │  │ assignments  │└─────────────────┘
└──────────┘  └──────────────┘
                      │
                      ↓
              ┌──────────────┐
              │ submissions  │
              └──────────────┘

        ┌───────────────────┐
        │ ai_conversations  │
        └───────────────────┘
                │
                ↓
        ┌──────────────┐
        │ ai_messages  │
        └──────────────┘
```

## Tables Overview

| Table Name | Primary Key | Rows (Est.) | Purpose | Status |
|------------|-------------|-------------|---------|--------|
| users | UUID | 10K-100K | User accounts & authentication | ✅ Active |
| courses | UUID | 1K-10K | Course information | ✅ Active |
| lessons | UUID | 10K-100K | Video lessons content | ✅ Active |
| materials | UUID | 50K-500K | Additional learning materials | ✅ Active |
| enrollments | UUID | 100K-1M | Course enrollments | ✅ Active |
| lesson_progress | UUID | 1M-10M | User progress tracking | ✅ Active |
| assignments | UUID | 10K-100K | Course assignments | ✅ Active |
| submissions | UUID | 100K-1M | Student submissions | ✅ Active |
| refresh_tokens | UUID | 100K-1M | JWT refresh tokens | ✅ Active |
| ai_conversations | UUID | 10K-100K | AI chat sessions | 🟡 Prepared |
| ai_messages | UUID | 100K-1M | AI conversation messages | 🟡 Prepared |

## Table Definitions

### 1. users

Bảng lưu trữ thông tin người dùng và authentication.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | User email (login) |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(255) | NOT NULL | User's full name |
| role | ENUM | NOT NULL, INDEXED | ADMIN, INSTRUCTOR, LEARNER |
| avatar_url | VARCHAR(500) | NULLABLE | Profile picture URL |
| bio | TEXT | NULLABLE | User biography |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| is_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| last_login_at | TIMESTAMP | NULLABLE | Last login timestamp |
| created_at | TIMESTAMPTZ | NOT NULL | Account creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Indexes:**
- `ix_users_email` (UNIQUE) on `email`
- `ix_users_role` on `role`

**Relationships:**
- One-to-Many: `courses` (as instructor)
- One-to-Many: `enrollments`
- One-to-Many: `submissions`
- One-to-Many: `lesson_progress`
- One-to-Many: `refresh_tokens`
- One-to-Many: `ai_conversations`

**Business Rules:**
- Email must be unique and valid format
- Password minimum 8 characters (enforced at application level)
- Default role is LEARNER
- Admin accounts should be limited

**Sample Data:**
```sql
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
  '123e4567-e89b-12d3-a456-426614174000',
  'admin@ailms.com',
  '$2b$12$...',  -- bcrypt hash
  'System Administrator',
  'ADMIN',
  TRUE,
  TRUE,
  NOW(),
  NOW()
);
```

---

### 2. courses

Bảng lưu trữ thông tin khóa học.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| instructor_id | UUID | FK→users, NOT NULL, INDEXED | Course creator |
| title | VARCHAR(255) | NOT NULL | Course title |
| slug | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | URL-friendly identifier |
| description | TEXT | NULLABLE | Full course description |
| short_description | VARCHAR(500) | NULLABLE | Brief summary |
| thumbnail_url | VARCHAR(500) | NULLABLE | Course thumbnail image |
| status | ENUM | NOT NULL, INDEXED | DRAFT, PUBLISHED, ARCHIVED |
| category | VARCHAR(100) | NULLABLE | Course category |
| level | VARCHAR(50) | NULLABLE | beginner, intermediate, advanced |
| language | VARCHAR(10) | DEFAULT 'vi' | Course language code |
| estimated_duration | INTEGER | NULLABLE | Duration in minutes |
| is_featured | BOOLEAN | DEFAULT FALSE | Featured on homepage |
| published_at | TIMESTAMP | NULLABLE | Publication timestamp |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Indexes:**
- `ix_courses_slug` (UNIQUE) on `slug`
- `ix_courses_instructor_id` on `instructor_id`
- `ix_courses_status` on `status`

**Foreign Keys:**
- `instructor_id` REFERENCES `users(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `users` (instructor)
- One-to-Many: `lessons`
- One-to-Many: `enrollments`
- One-to-Many: `assignments`
- One-to-Many: `ai_conversations`

**Business Rules:**
- Slug is auto-generated from title
- Only PUBLISHED courses are visible to learners
- Instructor must have INSTRUCTOR or ADMIN role
- Cannot delete course if there are active enrollments

**Status Flow:**
```
DRAFT → PUBLISHED → ARCHIVED
  ↑         ↓
  └─────────┘
```

---

### 3. lessons

Bảng lưu trữ bài giảng video trong khóa học.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| course_id | UUID | FK→courses, NOT NULL, INDEXED | Parent course |
| title | VARCHAR(255) | NOT NULL | Lesson title |
| description | TEXT | NULLABLE | Lesson description |
| content | TEXT | NULLABLE | Rich text content |
| video_url | VARCHAR(500) | NULLABLE | Video file URL |
| video_duration | INTEGER | NULLABLE | Duration in seconds |
| thumbnail_url | VARCHAR(500) | NULLABLE | Video thumbnail |
| order_index | INTEGER | NOT NULL | Lesson order in course |
| is_published | BOOLEAN | DEFAULT FALSE | Visibility status |
| is_preview | BOOLEAN | DEFAULT FALSE | Free preview allowed |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Indexes:**
- `ix_lessons_course_id` on `course_id`

**Foreign Keys:**
- `course_id` REFERENCES `courses(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `courses`
- One-to-Many: `materials`
- One-to-Many: `assignments`
- One-to-Many: `lesson_progress`
- One-to-Many: `ai_conversations`

**Business Rules:**
- order_index must be unique within a course
- is_preview allows non-enrolled users to watch
- video_duration should match actual video length

---

### 4. materials

Bảng lưu trữ tài liệu học tập bổ sung.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| lesson_id | UUID | FK→lessons, NOT NULL, INDEXED | Parent lesson |
| title | VARCHAR(255) | NOT NULL | Material title |
| description | TEXT | NULLABLE | Material description |
| type | ENUM | NOT NULL | VIDEO, DOCUMENT, LINK, QUIZ |
| file_url | VARCHAR(500) | NULLABLE | File/link URL |
| file_size | INTEGER | NULLABLE | Size in bytes |
| mime_type | VARCHAR(100) | NULLABLE | File MIME type |
| order_index | INTEGER | NOT NULL | Display order |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Indexes:**
- `ix_materials_lesson_id` on `lesson_id`

**Foreign Keys:**
- `lesson_id` REFERENCES `lessons(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `lessons`

**Business Rules:**
- order_index determines display sequence
- LINK type doesn't require file_size or mime_type
- DOCUMENT type must have valid mime_type

**Material Types:**
- VIDEO: Additional video content
- DOCUMENT: PDF, Word, etc.
- LINK: External resources
- QUIZ: Quiz content (JSON structure)

---

### 5. enrollments

Bảng theo dõi việc đăng ký khóa học của người dùng.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FK→users, NOT NULL, INDEXED | Enrolled student |
| course_id | UUID | FK→courses, NOT NULL, INDEXED | Enrolled course |
| status | ENUM | NOT NULL, INDEXED | ACTIVE, COMPLETED, DROPPED |
| progress | NUMERIC(5,2) | DEFAULT 0 | Progress percentage (0-100) |
| enrolled_at | TIMESTAMP | NOT NULL | Enrollment timestamp |
| completed_at | TIMESTAMP | NULLABLE | Completion timestamp |
| last_accessed_at | TIMESTAMP | NULLABLE | Last access time |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Constraints:**
- UNIQUE (user_id, course_id) - One enrollment per user per course

**Indexes:**
- `ix_enrollments_user_id` on `user_id`
- `ix_enrollments_course_id` on `course_id`
- `ix_enrollments_status` on `status`

**Foreign Keys:**
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- `course_id` REFERENCES `courses(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `users`
- Many-to-One: `courses`
- One-to-Many: `lesson_progress` (implicit)

**Business Rules:**
- progress is calculated from lesson_progress records
- completed_at is set when progress reaches 100%
- status transitions: ACTIVE → COMPLETED or ACTIVE → DROPPED

---

### 6. lesson_progress

Bảng theo dõi tiến độ xem video của người dùng.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FK→users, NOT NULL, INDEXED | User watching |
| lesson_id | UUID | FK→lessons, NOT NULL, INDEXED | Lesson being watched |
| watched_seconds | INTEGER | DEFAULT 0 | Seconds watched |
| total_seconds | INTEGER | NOT NULL | Total lesson duration |
| is_completed | BOOLEAN | DEFAULT FALSE | Completion status |
| completed_at | TIMESTAMP | NULLABLE | Completion timestamp |
| last_position | INTEGER | DEFAULT 0 | Last playback position |
| last_accessed_at | TIMESTAMP | NULLABLE | Last access time |

**Constraints:**
- UNIQUE (user_id, lesson_id) - One progress record per user per lesson

**Indexes:**
- `ix_lesson_progress_user_id` on `user_id`
- `ix_lesson_progress_lesson_id` on `lesson_id`

**Foreign Keys:**
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- `lesson_id` REFERENCES `lessons(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `users`
- Many-to-One: `lessons`

**Business Rules:**
- is_completed = TRUE when watched_seconds >= total_seconds * 0.9 (90%)
- last_position allows resume functionality
- Updates on video pause/completion events

---

### 7. assignments

Bảng lưu trữ bài tập của khóa học.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| course_id | UUID | FK→courses, NOT NULL, INDEXED | Parent course |
| lesson_id | UUID | FK→lessons, NULLABLE, INDEXED | Related lesson (optional) |
| title | VARCHAR(255) | NOT NULL | Assignment title |
| description | TEXT | NULLABLE | Brief description |
| instructions | TEXT | NULLABLE | Detailed instructions |
| due_date | TIMESTAMP | NULLABLE | Submission deadline |
| max_score | NUMERIC(5,2) | NOT NULL | Maximum points |
| allow_late_submission | BOOLEAN | DEFAULT FALSE | Allow late work |
| late_penalty_percent | NUMERIC(5,2) | DEFAULT 0 | Late penalty (0-100) |
| is_published | BOOLEAN | DEFAULT FALSE | Visibility status |
| order_index | INTEGER | NOT NULL | Display order |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update time |

**Indexes:**
- `ix_assignments_course_id` on `course_id`
- `ix_assignments_lesson_id` on `lesson_id`

**Foreign Keys:**
- `course_id` REFERENCES `courses(id)` ON DELETE CASCADE
- `lesson_id` REFERENCES `lessons(id)` ON DELETE SET NULL

**Relationships:**
- Many-to-One: `courses`
- Many-to-One: `lessons` (optional)
- One-to-Many: `submissions`

**Business Rules:**
- max_score must be > 0
- late_penalty_percent between 0-100
- due_date can be NULL for no deadline

---

### 8. submissions

Bảng lưu trữ bài nộp của học viên.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| assignment_id | UUID | FK→assignments, NOT NULL, INDEXED | Parent assignment |
| user_id | UUID | FK→users, NOT NULL, INDEXED | Student |
| content | TEXT | NULLABLE | Text submission |
| file_url | VARCHAR(500) | NULLABLE | Uploaded file URL |
| file_name | VARCHAR(255) | NULLABLE | Original filename |
| file_size | INTEGER | NULLABLE | File size in bytes |
| status | ENUM | NOT NULL, INDEXED | SUBMITTED, GRADED, RETURNED |
| score | NUMERIC(5,2) | NULLABLE | Earned score |
| feedback | TEXT | NULLABLE | Instructor feedback |
| submitted_at | TIMESTAMP | NOT NULL | Submission time |
| graded_at | TIMESTAMP | NULLABLE | Grading time |
| graded_by | UUID | FK→users, NULLABLE | Grading instructor |
| is_late | BOOLEAN | DEFAULT FALSE | Late submission flag |

**Constraints:**
- UNIQUE (assignment_id, user_id) - One submission per student per assignment

**Indexes:**
- `ix_submissions_assignment_id` on `assignment_id`
- `ix_submissions_user_id` on `user_id`
- `ix_submissions_status` on `status`

**Foreign Keys:**
- `assignment_id` REFERENCES `assignments(id)` ON DELETE CASCADE
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- `graded_by` REFERENCES `users(id)` ON DELETE SET NULL

**Relationships:**
- Many-to-One: `assignments`
- Many-to-One: `users` (student)
- Many-to-One: `users` (grader)

**Business Rules:**
- is_late determined by comparing submitted_at with due_date
- score cannot exceed assignment.max_score
- Late submissions apply late_penalty_percent if applicable

---

### 9. refresh_tokens

Bảng lưu trữ JWT refresh tokens.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FK→users, NOT NULL, INDEXED | Token owner |
| token | VARCHAR(500) | NOT NULL, INDEXED | Token string |
| expires_at | TIMESTAMP | NOT NULL | Expiration time |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| revoked_at | TIMESTAMP | NULLABLE | Revocation time |

**Indexes:**
- `ix_refresh_tokens_user_id` on `user_id`
- `ix_refresh_tokens_token` on `token`

**Foreign Keys:**
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `users`

**Business Rules:**
- Token expires after 7 days (default)
- revoked_at is set on logout
- Expired/revoked tokens should be periodically cleaned

---

### 10. ai_conversations

Bảng lưu trữ cuộc hội thoại với AI (Future feature).

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FK→users, NOT NULL, INDEXED | User chatting |
| course_id | UUID | FK→courses, NULLABLE, INDEXED | Related course |
| lesson_id | UUID | FK→lessons, NULLABLE | Related lesson |
| title | VARCHAR(255) | NULLABLE | Conversation title |
| is_active | BOOLEAN | DEFAULT TRUE | Active conversation |
| created_at | TIMESTAMPTZ | NOT NULL | Start time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last message time |

**Indexes:**
- `ix_ai_conversations_user_id` on `user_id`
- `ix_ai_conversations_course_id` on `course_id`

**Foreign Keys:**
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- `course_id` REFERENCES `courses(id)` ON DELETE SET NULL
- `lesson_id` REFERENCES `lessons(id)` ON DELETE SET NULL

**Relationships:**
- Many-to-One: `users`
- Many-to-One: `courses` (optional)
- Many-to-One: `lessons` (optional)
- One-to-Many: `ai_messages`

**Status**: 🟡 Database ready, service not implemented

---

### 11. ai_messages

Bảng lưu trữ tin nhắn trong cuộc hội thoại AI.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| conversation_id | UUID | FK→ai_conversations, NOT NULL, INDEXED | Parent conversation |
| role | VARCHAR(20) | NOT NULL | user, assistant, system |
| content | TEXT | NOT NULL | Message content |
| tokens_used | INTEGER | NULLABLE | Token consumption |
| model_version | VARCHAR(50) | NULLABLE | LLM model version |
| created_at | TIMESTAMP | NOT NULL | Message timestamp |

**Indexes:**
- `ix_ai_messages_conversation_id` on `conversation_id`

**Foreign Keys:**
- `conversation_id` REFERENCES `ai_conversations(id)` ON DELETE CASCADE

**Relationships:**
- Many-to-One: `ai_conversations`

**Status**: 🟡 Database ready, service not implemented

---

## Database Performance Optimization

### Indexes Strategy

**Current Indexes:**
1. **Primary Keys**: All tables have UUID primary keys (automatic B-tree index)
2. **Foreign Keys**: All FK columns are indexed for join performance
3. **Search Fields**: email, slug indexed for lookups
4. **Filter Fields**: role, status indexed for filtering
5. **Unique Constraints**: email, slug, (user_id, course_id), (user_id, lesson_id)

### Query Optimization Tips

**Common Queries:**

```sql
-- Get user courses with progress
SELECT c.*, e.progress, e.status
FROM courses c
JOIN enrollments e ON c.id = e.course_id
WHERE e.user_id = $1 AND e.status = 'ACTIVE';

-- Get lesson progress for course
SELECT l.*, lp.watched_seconds, lp.is_completed
FROM lessons l
LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND lp.user_id = $1
WHERE l.course_id = $2
ORDER BY l.order_index;

-- Get pending submissions for grading
SELECT s.*, a.title, u.full_name
FROM submissions s
JOIN assignments a ON s.assignment_id = a.id
JOIN users u ON s.user_id = u.id
WHERE a.course_id = $1 AND s.status = 'SUBMITTED'
ORDER BY s.submitted_at;
```

### Connection Pooling

SQLAlchemy connection pool configuration:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Base connections
    max_overflow=20,       # Additional connections
    pool_timeout=30,       # Timeout in seconds
    pool_recycle=3600,     # Recycle connections hourly
)
```

---

## Data Migration Guide

### Initial Migration

```bash
# Create migration
make migration MESSAGE="initial migration"

# Apply migration
make migrate

# Rollback (if needed)
docker-compose exec backend alembic downgrade -1
```

### Adding New Columns

```bash
# Example: Add 'phone' column to users
make migration MESSAGE="add phone to users"

# Migration file will be generated in:
# apps/backend/app/db/migrations/versions/
```

### Migration Best Practices

1. **Always test migrations** on development database first
2. **Backup production data** before running migrations
3. **Use descriptive migration messages**
4. **Review auto-generated migrations** before applying
5. **Create separate migrations** for schema and data changes

---

## Data Seeding

### Development Seed Data

```python
# Create admin user
admin = User(
    email="admin@ailms.com",
    password_hash=hash_password("admin123"),
    full_name="System Admin",
    role=UserRole.ADMIN,
    is_verified=True
)

# Create sample course
course = Course(
    title="Introduction to Python",
    slug="intro-to-python",
    instructor_id=instructor_id,
    status=CourseStatus.PUBLISHED,
    level="beginner"
)
```

---

## Database Maintenance

### Regular Tasks

1. **Vacuum** (weekly): `VACUUM ANALYZE;`
2. **Reindex** (monthly): `REINDEX DATABASE lms_db;`
3. **Clean expired tokens** (daily):
   ```sql
   DELETE FROM refresh_tokens
   WHERE expires_at < NOW() OR revoked_at IS NOT NULL;
   ```

### Backup Strategy

```bash
# Backup
docker-compose exec db pg_dump -U lms_user lms_db > backup.sql

# Restore
docker-compose exec -T db psql -U lms_user lms_db < backup.sql
```

---

## Database Monitoring

### Key Metrics to Monitor

1. **Connection Count**: Should be < pool_size + max_overflow
2. **Query Performance**: Slow queries > 100ms
3. **Table Size**: Growth rate
4. **Index Usage**: Ensure indexes are being used
5. **Lock Contention**: Detect blocking queries

### Useful Queries

```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Find slow queries
SELECT
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-29  
**Migration Version**: 299a7a8507ce (Initial migration)
