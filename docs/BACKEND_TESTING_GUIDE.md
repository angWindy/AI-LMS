# Backend Testing Guide - AI-LMS

## 📋 Testing Plan Overview

### Câu trả lời: CÓ CẦN FRONTEND KHÔNG?

**❌ KHÔNG CẦN!**

Bạn có thể test toàn bộ Backend API mà không cần Frontend bằng các công cụ sau:

### 1. Swagger UI (Recommended - Dễ nhất) ⭐⭐⭐
- **URL**: http://localhost:8000/docs
- **Ưu điểm**: 
  - Giao diện đẹp, dễ sử dụng
  - Tự động generate từ code
  - Test ngay trên browser
  - Lưu token tự động
  - Xem response ngay lập tức

### 2. cURL (Command line) ⭐⭐
- **Ưu điểm**: 
  - Nhanh, powerful
  - Có thể script automation
  - Available everywhere
- **Nhược điểm**: 
  - Syntax phức tạp hơn
  - Phải quản lý token manually

### 3. Postman / Thunder Client ⭐⭐⭐
- **Ưu điểm**: 
  - Professional tool
  - Save requests
  - Collections & environments
  - Team collaboration
- **Nhược điểm**: 
  - Cần install thêm

### 4. HTTPie (Modern cURL) ⭐⭐
- **Ưu điểm**: 
  - Syntax đơn giản hơn cURL
  - Colored output
- **Nhược điểm**: 
  - Cần install

**👉 KHUYẾN NGHỊ: Dùng Swagger UI cho testing manual**

---

## 🎯 Testing Scenarios

### Scenario 1: Basic User Flow (LEARNER)
1. ✅ Đăng ký tài khoản Learner
2. ✅ Login
3. ✅ Xem profile
4. ✅ Browse courses
5. ✅ Enroll vào course
6. ✅ Xem courses đã enroll
7. ❌ Xem lessons (CHƯA CÓ API)
8. ❌ Track progress (CHƯA CÓ API)

### Scenario 2: Instructor Flow
1. ✅ Đăng ký/tạo tài khoản Instructor
2. ✅ Login
3. ✅ Tạo course mới
4. ✅ Update course info
5. ✅ Publish course
6. ❌ Thêm lessons (CHƯA CÓ API)
7. ❌ Upload video (CHƯA CÓ API)
8. ❌ Tạo assignments (CHƯA CÓ API)

### Scenario 3: Admin Flow
1. ✅ Login as Admin
2. ✅ List all users
3. ✅ Create users (any role)
4. ✅ Activate/Deactivate users
5. ✅ Verify users
6. ✅ View all courses
7. ✅ Manage any course

---

## 🚀 TESTING WALKTHROUGH - Từng bước chi tiết

### Prerequisites

1. **Start Backend**:
```bash
cd /home/icthagws/Github/AI-LMS
make start
```

2. **Verify services running**:
```bash
docker-compose ps
# Both lms_backend and lms_db should be "Up"

# Check API health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

3. **Open Swagger UI**:
```
Browser: http://localhost:8000/docs
```

---

## 📝 TEST CASE 1: Tạo tài khoản và Login

### 1.1. Đăng ký Admin User (First user)

**Endpoint**: `POST /api/v1/auth/register`

**Request Body** (Copy vào Swagger UI):
```json
{
  "email": "admin@ailms.com",
  "password": "Admin123!",
  "full_name": "System Administrator",
  "role": "ADMIN"
}
```

**Expected Response**: 201 Created
```json
{
  "id": "uuid-here",
  "email": "admin@ailms.com",
  "full_name": "System Administrator",
  "role": "ADMIN",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-29T..."
}
```

**✅ Verification**: 
- Status code = 201
- User created với role ADMIN

---

### 1.2. Đăng ký Instructor

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "instructor1@ailms.com",
  "password": "Instructor123!",
  "full_name": "Nguyen Van A",
  "role": "INSTRUCTOR"
}
```

**Expected Response**: 201 Created

**✅ Save this for later**: instructor1@ailms.com / Instructor123!

---

### 1.3. Đăng ký Learner (Student)

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "student1@ailms.com",
  "password": "Student123!",
  "full_name": "Tran Thi B",
  "role": "LEARNER"
}
```

**Expected Response**: 201 Created

**✅ Save this**: student1@ailms.com / Student123!

---

### 1.4. Login as Admin

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "admin@ailms.com",
  "password": "Admin123!"
}
```

**Expected Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "...",
    "email": "admin@ailms.com",
    "full_name": "System Administrator",
    "role": "ADMIN"
  }
}
```

**🔑 IMPORTANT**: Copy `access_token` value!

**In Swagger UI**:
1. Click "Authorize" button (🔓 icon) ở góc trên
2. Paste token vào field "Value"
3. Click "Authorize"
4. Close dialog

**Bây giờ tất cả requests sẽ tự động include token!**

---

### 1.5. Get Current User Profile

**Endpoint**: `GET /api/v1/auth/me`

**No body needed** (token in header)

**Expected Response**: 200 OK
```json
{
  "id": "...",
  "email": "admin@ailms.com",
  "full_name": "System Administrator",
  "role": "ADMIN",
  "avatar_url": null,
  "bio": null,
  "is_active": true,
  "is_verified": false,
  "last_login_at": "2026-03-29T...",
  "created_at": "2026-03-29T..."
}
```

**✅ Test passed**: Có thể get profile với token

---

## 📝 TEST CASE 2: Admin quản lý Users

### 2.1. List All Users (Admin only)

**Endpoint**: `GET /api/v1/users`

**Query Parameters**:
- page: 1
- page_size: 10

**Expected Response**: 200 OK
```json
{
  "items": [
    {
      "id": "...",
      "email": "admin@ailms.com",
      "full_name": "System Administrator",
      "role": "ADMIN",
      ...
    },
    {
      "id": "...",
      "email": "instructor1@ailms.com",
      "full_name": "Nguyen Van A",
      "role": "INSTRUCTOR",
      ...
    },
    {
      "id": "...",
      "email": "student1@ailms.com",
      "full_name": "Tran Thi B",
      "role": "LEARNER",
      ...
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

**✅ Verification**: Thấy tất cả 3 users đã tạo

---

### 2.2. Filter Users by Role

**Endpoint**: `GET /api/v1/users?role=INSTRUCTOR`

**Expected Response**: Only instructors returned

---

### 2.3. Create Additional Instructor (Admin action)

**Endpoint**: `POST /api/v1/users` (Admin only)

**Request Body**:
```json
{
  "email": "instructor2@ailms.com",
  "password": "Instructor123!",
  "full_name": "Le Van C",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": true
}
```

**Expected Response**: 201 Created

**✅ Note**: Admin có thể tạo user đã verified ngay

---

### 2.4. Verify User Email (Admin action)

**Endpoint**: `POST /api/v1/users/{user_id}/verify`

**Steps**:
1. Copy `id` của instructor1 từ list users
2. Call endpoint với user_id đó

**Expected Response**: 200 OK
```json
{
  "message": "User verified successfully",
  "user": {
    "id": "...",
    "is_verified": true
  }
}
```

---

## 📝 TEST CASE 3: Instructor tạo Course

### 3.1. Login as Instructor

**Logout admin first** (Click Authorize → Logout trong Swagger)

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "instructor1@ailms.com",
  "password": "Instructor123!"
}
```

**Copy new access_token và Authorize lại!**

---

### 3.2. Create Course

**Endpoint**: `POST /api/v1/courses`

**Request Body**:
```json
{
  "title": "Python Programming for Beginners",
  "description": "Learn Python from scratch. This comprehensive course covers all fundamental concepts including variables, data types, loops, functions, and object-oriented programming. Perfect for absolute beginners with no prior coding experience.",
  "short_description": "Learn Python programming from zero to hero",
  "category": "Programming",
  "level": "beginner",
  "language": "vi",
  "estimated_duration": 1200,
  "thumbnail_url": "https://example.com/python-course.jpg"
}
```

**Expected Response**: 201 Created
```json
{
  "id": "course-uuid",
  "title": "Python Programming for Beginners",
  "slug": "python-programming-for-beginners",
  "description": "...",
  "instructor_id": "instructor-uuid",
  "status": "DRAFT",
  "category": "Programming",
  "level": "beginner",
  "language": "vi",
  "estimated_duration": 1200,
  "is_featured": false,
  "created_at": "2026-03-29T...",
  "updated_at": "2026-03-29T..."
}
```

**✅ Save course_id**: Copy `id` value!

---

### 3.3. View Created Course

**Endpoint**: `GET /api/v1/courses/{course_id}`

**Use course_id từ step trước**

**Expected Response**: 200 OK with course details

---

### 3.4. Update Course

**Endpoint**: `PUT /api/v1/courses/{course_id}`

**Request Body** (only fields to update):
```json
{
  "title": "Complete Python Programming Course",
  "short_description": "Master Python programming with hands-on projects",
  "estimated_duration": 1500
}
```

**Expected Response**: 200 OK with updated course

---

### 3.5. Create More Courses

Repeat step 3.2 với different data:

**Course 2: Web Development**
```json
{
  "title": "Modern Web Development with React",
  "description": "Learn to build modern web applications using React, the most popular JavaScript library. Covers components, hooks, state management, and API integration.",
  "short_description": "Build modern web apps with React",
  "category": "Web Development",
  "level": "intermediate",
  "language": "vi",
  "estimated_duration": 1800
}
```

**Course 3: Data Science**
```json
{
  "title": "Data Science with Python",
  "description": "Introduction to data science using Python. Learn pandas, numpy, matplotlib, and basic machine learning concepts.",
  "short_description": "Data analysis and ML with Python",
  "category": "Data Science",
  "level": "intermediate",
  "language": "vi",
  "estimated_duration": 2000
}
```

---

### 3.6. Publish Course

**Endpoint**: `POST /api/v1/courses/{course_id}/publish`

**No body needed**

**Expected Response**: 200 OK
```json
{
  "id": "course-uuid",
  "status": "PUBLISHED",
  "published_at": "2026-03-29T..."
}
```

**✅ Course bây giờ visible cho public**

---

## 📝 TEST CASE 4: Public Browse Courses

### 4.1. List All Published Courses (No auth needed)

**Logout in Swagger** (để test như anonymous user)

**Endpoint**: `GET /api/v1/courses`

**Query Parameters**:
- page: 1
- page_size: 10

**Expected Response**: 200 OK
```json
{
  "items": [
    {
      "id": "...",
      "title": "Complete Python Programming Course",
      "slug": "complete-python-programming-course",
      "short_description": "Master Python programming...",
      "thumbnail_url": "...",
      "category": "Programming",
      "level": "beginner",
      "instructor": {
        "id": "...",
        "full_name": "Nguyen Van A",
        "avatar_url": null
      },
      "enrollment_count": 0
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

**✅ Chỉ thấy PUBLISHED courses**

---

### 4.2. Filter Courses by Category

**Endpoint**: `GET /api/v1/courses?category=Programming`

**Expected Response**: Only programming courses

---

### 4.3. Search Courses

**Endpoint**: `GET /api/v1/courses?search=python`

**Expected Response**: Courses có "python" trong title/description

---

## 📝 TEST CASE 5: Student Enrollment

### 5.1. Login as Student

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "student1@ailms.com",
  "password": "Student123!"
}
```

**Authorize với token mới!**

---

### 5.2. Enroll in Course

**Endpoint**: `POST /api/v1/courses/{course_id}/enroll`

**Use course_id của Python course**

**No body needed**

**Expected Response**: 201 Created
```json
{
  "id": "enrollment-uuid",
  "user_id": "student-uuid",
  "course_id": "course-uuid",
  "status": "ACTIVE",
  "progress": 0,
  "enrolled_at": "2026-03-29T..."
}
```

**✅ Student đã enroll thành công!**

---

### 5.3. Try to Enroll Again (Should fail)

**Same endpoint**: `POST /api/v1/courses/{course_id}/enroll`

**Expected Response**: 400 Bad Request
```json
{
  "detail": "Already enrolled in this course"
}
```

**✅ Prevent duplicate enrollment**

---

### 5.4. View My Enrollments

**Endpoint**: `GET /api/v1/courses/enrollments/me`

**Expected Response**: 200 OK
```json
{
  "items": [
    {
      "id": "enrollment-uuid",
      "course": {
        "id": "course-uuid",
        "title": "Complete Python Programming Course",
        "thumbnail_url": "...",
        "instructor": {
          "id": "...",
          "full_name": "Nguyen Van A"
        }
      },
      "status": "ACTIVE",
      "progress": 0,
      "enrolled_at": "2026-03-29T...",
      "last_accessed_at": null
    }
  ],
  "total": 1
}
```

**✅ See all enrolled courses**

---

### 5.5. Get Course Lessons (Should be empty for now)

**Endpoint**: `GET /api/v1/courses/{course_id}/lessons`

**Expected Response**: 200 OK
```json
{
  "items": [],
  "total": 0
}
```

**❌ No lessons yet** - API hoạt động nhưng chưa có lessons

---

## 📝 TEST CASE 6: Advanced Testing

### 6.1. Token Expiration & Refresh

**Wait 30 minutes** (hoặc change ACCESS_TOKEN_EXPIRE_MINUTES trong .env)

**Try any authenticated request**: Should get 401 Unauthorized

**Use Refresh Token**:
**Endpoint**: `POST /api/v1/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "your-refresh-token-from-login"
}
```

**Expected Response**: 200 OK with new access_token

---

### 6.2. Update Profile

**Endpoint**: `PUT /api/v1/auth/me`

**Request Body**:
```json
{
  "full_name": "Tran Thi B (Updated)",
  "bio": "Passionate learner interested in programming and data science",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Expected Response**: 200 OK with updated profile

---

### 6.3. Change Password

**Endpoint**: `PUT /api/v1/auth/me/password`

**Request Body**:
```json
{
  "old_password": "Student123!",
  "new_password": "NewStudent456!"
}
```

**Expected Response**: 200 OK

**Try login with old password**: Should fail
**Try login with new password**: Should work

---

### 6.4. Logout

**Endpoint**: `POST /api/v1/auth/logout`

**No body needed**

**Expected Response**: 200 OK
```json
{
  "message": "Successfully logged out"
}
```

**✅ Refresh tokens revoked**

---

## ❌ KHÔNG THỂ TEST (API chưa có)

### Lesson Management
- ❌ Tạo lesson trong course
- ❌ Upload video cho lesson
- ❌ Edit lesson
- ❌ Delete lesson
- ❌ Reorder lessons

### File Upload
- ❌ Upload video files
- ❌ Upload documents (PDF, PPT)
- ❌ Upload thumbnails
- ❌ Upload materials

### Progress Tracking
- ❌ Track video watch time
- ❌ Mark lesson as completed
- ❌ View overall progress
- ❌ Get course completion percentage

### Assignments
- ❌ Create assignment
- ❌ Submit assignment
- ❌ Grade submission
- ❌ View grades

---

## 📊 Testing Summary Template

Copy và điền khi test:

```
# Backend Testing Report
Date: ___________
Tester: __________

## Test Results

### Authentication & User Management
- [ ] Register Admin: PASS / FAIL
- [ ] Register Instructor: PASS / FAIL
- [ ] Register Learner: PASS / FAIL
- [ ] Login: PASS / FAIL
- [ ] Get Profile: PASS / FAIL
- [ ] Update Profile: PASS / FAIL
- [ ] Change Password: PASS / FAIL
- [ ] Token Refresh: PASS / FAIL
- [ ] Logout: PASS / FAIL

### User Management (Admin)
- [ ] List Users: PASS / FAIL
- [ ] Create User: PASS / FAIL
- [ ] Verify User: PASS / FAIL
- [ ] Activate/Deactivate: PASS / FAIL

### Course Management
- [ ] Create Course: PASS / FAIL
- [ ] Update Course: PASS / FAIL
- [ ] Publish Course: PASS / FAIL
- [ ] List Courses: PASS / FAIL
- [ ] Search Courses: PASS / FAIL
- [ ] Filter by Category: PASS / FAIL

### Enrollment
- [ ] Enroll in Course: PASS / FAIL
- [ ] View Enrollments: PASS / FAIL
- [ ] Prevent Duplicate: PASS / FAIL

### Issues Found
1. ___________________________
2. ___________________________

### API Coverage
- Implemented: 24 endpoints
- Tested: ___ endpoints
- Passed: ___ endpoints
- Failed: ___ endpoints

### Recommendations
________________________________
________________________________
```

---

## 🔧 Testing với cURL (Alternative)

Nếu không dùng Swagger, đây là cURL commands:

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailms.com",
    "password": "Admin123!",
    "full_name": "System Administrator",
    "role": "ADMIN"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailms.com",
    "password": "Admin123!"
  }'
```

### Save token
```bash
TOKEN="paste-your-token-here"
```

### Get Profile
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create Course
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Programming",
    "description": "Learn Python from scratch",
    "short_description": "Python basics",
    "category": "Programming",
    "level": "beginner",
    "language": "vi",
    "estimated_duration": 1200
  }'
```

---

**Testing Guide Version**: 1.0  
**Last Updated**: 2026-03-29  
**Tested With**: Backend v1.0.0-alpha
