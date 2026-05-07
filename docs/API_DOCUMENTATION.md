# API Documentation

## Tổng quan

AI-LMS cung cấp RESTful API được xây dựng với FastAPI, hỗ trợ JWT authentication và role-based authorization.

## Base Information

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **API Prefix**: `/api/v1`
- **Documentation**: 
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
- **Content-Type**: `application/json`
- **Authentication**: Bearer Token (JWT)

## Authentication

### Token Types

1. **Access Token**
   - Duration: 30 minutes (default)
   - Usage: Include in Authorization header
   - Format: `Authorization: Bearer <access_token>`

2. **Refresh Token**
   - Duration: 7 days (default)
   - Usage: Obtain new access token
   - Storage: Secure HTTP-only cookie (recommended) or local storage

### Authentication Flow

```
┌─────────┐                                  ┌─────────┐
│ Client  │                                  │  Server │
└────┬────┘                                  └────┬────┘
     │                                            │
     │  POST /api/v1/auth/login                  │
     │  {email, password}                        │
     ├──────────────────────────────────────────>│
     │                                            │
     │  200 OK                                    │
     │  {access_token, refresh_token, user}      │
     │<──────────────────────────────────────────┤
     │                                            │
     │  Subsequent requests                       │
     │  Authorization: Bearer <access_token>     │
     ├──────────────────────────────────────────>│
     │                                            │
     │  When access token expires:                │
     │  POST /api/v1/auth/refresh                │
     │  {refresh_token}                          │
     ├──────────────────────────────────────────>│
     │                                            │
     │  200 OK                                    │
     │  {access_token}                           │
     │<──────────────────────────────────────────┤
     │                                            │
```

## API Endpoints

### 1. Health Check

#### GET /health
Check API health status.

**Authentication**: Not required

**Response**: 200 OK
```json
{
  "status": "healthy"
}
```

---

## Authentication Endpoints

### 1.1. Register User

#### POST /api/v1/auth/register

Đăng ký tài khoản người dùng mới.

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Nguyen Van A",
  "role": "LEARNER"
}
```

**Field Validations**:
- `email`: Valid email format, unique
- `password`: Min 8 characters
- `full_name`: Required
- `role`: Optional, default "LEARNER", enum: [ADMIN, INSTRUCTOR, LEARNER]

**Success Response**: 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "role": "LEARNER",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid email or password format
- `409 Conflict`: Email already exists

---

### 1.2. Login

#### POST /api/v1/auth/login

Đăng nhập và nhận access token + refresh token.

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "Nguyen Van A",
    "role": "LEARNER",
    "avatar_url": null
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account not active

---

### 1.3. Refresh Token

#### POST /api/v1/auth/refresh

Làm mới access token sử dụng refresh token.

**Authentication**: Not required (uses refresh token)

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token

---

### 1.4. Logout

#### POST /api/v1/auth/logout

Đăng xuất và thu hồi tất cả refresh tokens.

**Authentication**: Required

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Success Response**: 200 OK
```json
{
  "message": "Successfully logged out"
}
```

---

### 1.5. Get Current User Profile

#### GET /api/v1/auth/me

Lấy thông tin profile của user đang đăng nhập.

**Authentication**: Required

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Success Response**: 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "role": "LEARNER",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Passionate learner",
  "is_active": true,
  "is_verified": true,
  "last_login_at": "2026-03-29T10:30:00Z",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

### 1.6. Update Profile

#### PUT /api/v1/auth/me

Cập nhật thông tin profile.

**Authentication**: Required

**Request Body**:
```json
{
  "full_name": "Nguyen Van B",
  "bio": "Updated bio",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Success Response**: 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Nguyen Van B",
  "bio": "Updated bio",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "updated_at": "2026-03-29T11:00:00Z"
}
```

---

### 1.7. Change Password

#### PUT /api/v1/auth/me/password

Đổi mật khẩu.

**Authentication**: Required

**Request Body**:
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

**Success Response**: 200 OK
```json
{
  "message": "Password updated successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid old password
- `422 Unprocessable Entity`: New password doesn't meet requirements

---

## User Management Endpoints

**Base Path**: `/api/v1/users`  
**Required Role**: ADMIN (all endpoints)

### 2.1. List Users

#### GET /api/v1/users

Lấy danh sách người dùng với pagination và filtering.

**Authentication**: Required (ADMIN only)

**Query Parameters**:
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 10, max: 100): Items per page
- `role` (string, optional): Filter by role (ADMIN, INSTRUCTOR, LEARNER)
- `is_active` (boolean, optional): Filter by active status
- `search` (string, optional): Search by email or full name

**Example Request**:
```
GET /api/v1/users?page=1&page_size=20&role=INSTRUCTOR&is_active=true&search=nguyen
```

**Success Response**: 200 OK
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "instructor@example.com",
      "full_name": "Nguyen Van A",
      "role": "INSTRUCTOR",
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 2.2. Create User

#### POST /api/v1/users

Tạo người dùng mới (admin function).

**Authentication**: Required (ADMIN only)

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "TempPass123!",
  "full_name": "New User",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": false
}
```

**Success Response**: 201 Created
```json
{
  "id": "new-uuid",
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-29T12:00:00Z"
}
```

---

### 2.3. Get User by ID

#### GET /api/v1/users/{user_id}

Lấy thông tin chi tiết của một user.

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Success Response**: 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "role": "LEARNER",
  "avatar_url": null,
  "bio": null,
  "is_active": true,
  "is_verified": true,
  "last_login_at": "2026-03-29T10:00:00Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-03-29T10:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: User not found

---

### 2.4. Update User

#### PUT /api/v1/users/{user_id}

Cập nhật thông tin user.

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Request Body**:
```json
{
  "full_name": "Updated Name",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": true
}
```

**Success Response**: 200 OK
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Updated Name",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": true,
  "updated_at": "2026-03-29T12:00:00Z"
}
```

---

### 2.5. Delete User

#### DELETE /api/v1/users/{user_id}

Xóa user (soft delete recommended).

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Success Response**: 204 No Content

**Error Responses**:
- `403 Forbidden`: Cannot delete own account
- `404 Not Found`: User not found

---

### 2.6. Activate User

#### POST /api/v1/users/{user_id}/activate

Kích hoạt tài khoản user.

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Success Response**: 200 OK
```json
{
  "message": "User activated successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "is_active": true
  }
}
```

---

### 2.7. Deactivate User

#### POST /api/v1/users/{user_id}/deactivate

Vô hiệu hóa tài khoản user.

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Success Response**: 200 OK
```json
{
  "message": "User deactivated successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "is_active": false
  }
}
```

---

### 2.8. Verify User

#### POST /api/v1/users/{user_id}/verify

Xác thực email của user.

**Authentication**: Required (ADMIN only)

**Path Parameters**:
- `user_id` (UUID): User identifier

**Success Response**: 200 OK
```json
{
  "message": "User verified successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "is_verified": true
  }
}
```

---

## Course Management Endpoints

**Base Path**: `/api/v1/courses`

### 3.1. List Courses

#### GET /api/v1/courses

Lấy danh sách khóa học (chỉ PUBLISHED courses cho public).

**Authentication**: Optional (public endpoint, but may have different results when authenticated)

**Query Parameters**:
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 10, max: 100): Items per page
- `category` (string, optional): Filter by category
- `level` (string, optional): Filter by level (beginner, intermediate, advanced)
- `search` (string, optional): Search in title and description
- `is_featured` (boolean, optional): Featured courses only
- `instructor_id` (UUID, optional): Filter by instructor

**Example Request**:
```
GET /api/v1/courses?page=1&page_size=12&level=beginner&search=python
```

**Success Response**: 200 OK
```json
{
  "items": [
    {
      "id": "course-uuid",
      "title": "Introduction to Python",
      "slug": "introduction-to-python",
      "short_description": "Learn Python programming from scratch",
      "thumbnail_url": "https://example.com/thumb.jpg",
      "category": "Programming",
      "level": "beginner",
      "language": "vi",
      "estimated_duration": 1200,
      "is_featured": true,
      "instructor": {
        "id": "instructor-uuid",
        "full_name": "Nguyen Van A",
        "avatar_url": "https://example.com/avatar.jpg"
      },
      "enrollment_count": 150,
      "published_at": "2026-01-15T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 12,
  "total_pages": 1
}
```

---

### 3.2. Create Course

#### POST /api/v1/courses

Tạo khóa học mới.

**Authentication**: Required (INSTRUCTOR or ADMIN)

**Request Body**:
```json
{
  "title": "Advanced JavaScript",
  "description": "Master advanced JavaScript concepts and patterns",
  "short_description": "Learn advanced JS",
  "category": "Programming",
  "level": "advanced",
  "language": "vi",
  "estimated_duration": 1800,
  "thumbnail_url": "https://example.com/js-thumb.jpg"
}
```

**Success Response**: 201 Created
```json
{
  "id": "new-course-uuid",
  "title": "Advanced JavaScript",
  "slug": "advanced-javascript",
  "description": "Master advanced JavaScript concepts and patterns",
  "short_description": "Learn advanced JS",
  "instructor_id": "instructor-uuid",
  "status": "DRAFT",
  "category": "Programming",
  "level": "advanced",
  "language": "vi",
  "estimated_duration": 1800,
  "is_featured": false,
  "created_at": "2026-03-29T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation errors
- `403 Forbidden`: Insufficient permissions

---

### 3.3. Get Course by ID

#### GET /api/v1/courses/{course_id}

Lấy thông tin chi tiết khóa học.

**Authentication**: Optional (required for DRAFT courses)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Success Response**: 200 OK
```json
{
  "id": "course-uuid",
  "title": "Introduction to Python",
  "slug": "introduction-to-python",
  "description": "Comprehensive Python course for beginners...",
  "short_description": "Learn Python from scratch",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "status": "PUBLISHED",
  "category": "Programming",
  "level": "beginner",
  "language": "vi",
  "estimated_duration": 1200,
  "is_featured": true,
  "instructor": {
    "id": "instructor-uuid",
    "full_name": "Nguyen Van A",
    "email": "instructor@example.com",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "lessons_count": 25,
  "enrolled_count": 150,
  "published_at": "2026-01-15T00:00:00Z",
  "created_at": "2026-01-10T00:00:00Z",
  "updated_at": "2026-03-20T00:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Course not found
- `403 Forbidden`: Cannot access DRAFT course

---

### 3.4. Update Course

#### PUT /api/v1/courses/{course_id}

Cập nhật thông tin khóa học.

**Authentication**: Required (Course owner or ADMIN)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Request Body**: (all fields optional)
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "short_description": "Updated short desc",
  "category": "Web Development",
  "level": "intermediate",
  "estimated_duration": 1500,
  "thumbnail_url": "https://example.com/new-thumb.jpg"
}
```

**Success Response**: 200 OK
```json
{
  "id": "course-uuid",
  "title": "Updated Title",
  "slug": "updated-title",
  "updated_at": "2026-03-29T12:30:00Z",
  ...
}
```

**Error Responses**:
- `403 Forbidden`: Not course owner
- `404 Not Found`: Course not found

---

### 3.5. Delete Course

#### DELETE /api/v1/courses/{course_id}

Xóa khóa học.

**Authentication**: Required (Course owner or ADMIN)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Success Response**: 204 No Content

**Error Responses**:
- `403 Forbidden`: Not course owner or has active enrollments
- `404 Not Found`: Course not found

---

### 3.6. Publish Course

#### POST /api/v1/courses/{course_id}/publish

Publish khóa học (DRAFT → PUBLISHED).

**Authentication**: Required (Course owner or ADMIN)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Success Response**: 200 OK
```json
{
  "id": "course-uuid",
  "status": "PUBLISHED",
  "published_at": "2026-03-29T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Course not ready to publish (missing lessons, etc.)
- `403 Forbidden`: Not course owner

---

### 3.7. Get Course Lessons

#### GET /api/v1/courses/{course_id}/lessons

Lấy danh sách bài giảng của khóa học.

**Authentication**: Required (enrolled users or course owner)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Success Response**: 200 OK
```json
{
  "items": [
    {
      "id": "lesson-uuid",
      "course_id": "course-uuid",
      "title": "Introduction to Variables",
      "description": "Learn about variables in Python",
      "video_url": "https://example.com/video1.mp4",
      "video_duration": 600,
      "thumbnail_url": "https://example.com/thumb1.jpg",
      "order_index": 1,
      "is_published": true,
      "is_preview": true,
      "created_at": "2026-01-10T00:00:00Z"
    }
  ],
  "total": 25
}
```

**Error Responses**:
- `403 Forbidden`: Not enrolled
- `404 Not Found`: Course not found

---

### 3.8. Enroll in Course

#### POST /api/v1/courses/{course_id}/enroll

Đăng ký học khóa học.

**Authentication**: Required (LEARNER role)

**Path Parameters**:
- `course_id` (UUID): Course identifier

**Success Response**: 201 Created
```json
{
  "id": "enrollment-uuid",
  "user_id": "user-uuid",
  "course_id": "course-uuid",
  "status": "ACTIVE",
  "progress": 0,
  "enrolled_at": "2026-03-29T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Already enrolled
- `403 Forbidden`: Not a LEARNER
- `404 Not Found`: Course not found or not published

---

### 3.9. Get My Enrollments

#### GET /api/v1/courses/enrollments/me

Lấy danh sách khóa học đã đăng ký của user hiện tại.

**Authentication**: Required

**Query Parameters**:
- `status` (string, optional): Filter by status (ACTIVE, COMPLETED, DROPPED)

**Success Response**: 200 OK
```json
{
  "items": [
    {
      "id": "enrollment-uuid",
      "course": {
        "id": "course-uuid",
        "title": "Introduction to Python",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "instructor": {
          "id": "instructor-uuid",
          "full_name": "Nguyen Van A"
        }
      },
      "status": "ACTIVE",
      "progress": 35.5,
      "enrolled_at": "2026-03-01T00:00:00Z",
      "last_accessed_at": "2026-03-29T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

## Error Responses

### Standard Error Format

All error responses follow this structure:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-03-29T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Codes

```json
// 401 Unauthorized
{
  "detail": "Could not validate credentials",
  "error_code": "INVALID_CREDENTIALS"
}

// 403 Forbidden
{
  "detail": "Insufficient permissions",
  "error_code": "FORBIDDEN"
}

// 404 Not Found
{
  "detail": "Course not found",
  "error_code": "RESOURCE_NOT_FOUND"
}

// 409 Conflict
{
  "detail": "Email already registered",
  "error_code": "EMAIL_EXISTS"
}

// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

**Status**: 🟡 Not yet implemented

**Planned limits**:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Burst: 20 requests/minute

---

## Pagination

All list endpoints support pagination:

**Query Parameters**:
- `page` (integer, min: 1, default: 1)
- `page_size` (integer, min: 1, max: 100, default: 10)

**Response Format**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

---

## CORS Configuration

**Allowed Origins**: Configurable via environment variable `CORS_ORIGINS`

**Default**: `http://localhost:3000`

**Allowed Methods**: GET, POST, PUT, DELETE, PATCH, OPTIONS

**Allowed Headers**: Authorization, Content-Type

**Credentials**: Allowed

---

## API Testing with cURL

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "role": "LEARNER"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Get Profile (with token)
```bash
TOKEN="your_access_token_here"
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### List Courses
```bash
curl -X GET "http://localhost:8000/api/v1/courses?page=1&page_size=10"
```

---

## API Client Examples

### JavaScript/TypeScript

```typescript
// API Client setup
const API_BASE_URL = 'http://localhost:8000/api/v1';

class APIClient {
  private accessToken: string | null = null;

  setToken(token: string) {
    this.accessToken = token;
  }

  async request(endpoint: string, options: RequestInit = {}) {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    return response.json();
  }

  // Auth methods
  async login(email: string, password: string) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async register(userData: RegisterData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getProfile() {
    return this.request('/auth/me');
  }

  // Course methods
  async getCourses(params: CoursesParams) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/courses?${query}`);
  }

  async getCourse(courseId: string) {
    return this.request(`/courses/${courseId}`);
  }

  async enrollCourse(courseId: string) {
    return this.request(`/courses/${courseId}/enroll`, {
      method: 'POST',
    });
  }
}

// Usage
const api = new APIClient();

// Login
const loginData = await api.login('user@example.com', 'password');

// Get courses
const courses = await api.getCourses({ page: 1, page_size: 10 });

// Enroll
await api.enrollCourse(courseId);
```

### Python

```python
import requests
from typing import Optional, Dict, Any

class LMSClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            headers=self._headers()
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        return data
    
    def get_courses(self, **params) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/courses",
            params=params,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def enroll_course(self, course_id: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/courses/{course_id}/enroll",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = LMSClient()
client.login("user@example.com", "password")
courses = client.get_courses(page=1, page_size=10)
client.enroll_course(course_id)
```

---

## Missing Endpoints (To Be Implemented)

### Lessons Management
- `POST /api/v1/lessons` - Create lesson
- `GET /api/v1/lessons/{lesson_id}` - Get lesson details
- `PUT /api/v1/lessons/{lesson_id}` - Update lesson
- `DELETE /api/v1/lessons/{lesson_id}` - Delete lesson
- `POST /api/v1/lessons/{lesson_id}/progress` - Update watch progress

### Assignments
- `POST /api/v1/assignments` - Create assignment
- `GET /api/v1/assignments/{assignment_id}` - Get assignment
- `PUT /api/v1/assignments/{assignment_id}` - Update assignment
- `DELETE /api/v1/assignments/{assignment_id}` - Delete assignment
- `GET /api/v1/question-bank/courses` - List courses visible to the question bank
- `GET /api/v1/question-bank/questions` - List reusable questions, filter by course/lesson
- `POST /api/v1/question-bank/questions` - Create a reusable question manually
- `POST /api/v1/question-bank/generate` - Generate reusable lesson questions with LLM
- `PUT /api/v1/question-bank/questions/{question_id}` - Update reusable question details
- `DELETE /api/v1/question-bank/questions/{question_id}` - Delete reusable question

### Submissions
- `POST /api/v1/submissions` - Submit assignment
- `GET /api/v1/submissions/{submission_id}` - Get submission
- `PUT /api/v1/submissions/{submission_id}/grade` - Grade submission
- `GET /api/v1/assignments/{assignment_id}/submissions` - List submissions

### Materials
- `POST /api/v1/materials` - Upload material
- `GET /api/v1/materials/{material_id}` - Get material
- `DELETE /api/v1/materials/{material_id}` - Delete material

### AI Chatbot

The backend now exposes LMS-aware chatbot endpoints for both lesson video rooms and assignment support:

- `POST /api/v1/chatbot/ask` - General lesson/video classroom chatbot
- `POST /api/v1/chatbot/assignment/preload` - Warm and validate sanitized assignment context
- `POST /api/v1/chatbot/assignment/ask` - Guided assignment helper that uses assignment content only
- `GET /api/v1/chatbot/conversations` - List chatbot conversations for the current user
- `GET /api/v1/chatbot/conversations/{conversation_id}/messages` - Get conversation history

Important notes:

- Assignment chatbot context is intentionally limited to course title, lesson title, and the visible assignment questions/options.
- Answer keys and explanations are not sent to the model.
- Lesson/video chatbot can still use course/lesson scoped RAG and teaching images.

---

**Version**: 1.0.0-alpha  
**Last Updated**: 2026-03-29  
**API Status**: ~20 endpoints implemented, ~15 planned
