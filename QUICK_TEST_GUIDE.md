# Quick Test Guide - AI-LMS Backend

## TRẢ LỜI CÂU HỎI CỦA BẠN:

### ❓ Backend đã làm được gì?

**✅ ĐÃ HOÀN THÀNH (70%):**
1. ✅ User Management (ADMIN, INSTRUCTOR, LEARNER) 
2. ✅ JWT Authentication với Refresh Tokens
3. ✅ Course CRUD (Create, Read, Update, Delete, Publish)
4. ✅ Enrollment system (Đăng ký khóa học)
5. ✅ Database với 11 tables
6. ✅ API Documentation (Swagger UI)

**❌ CHƯA HOÀN THÀNH:**
1. ❌ Lesson Management API (model có, API chưa)
2. ❌ File Upload System (video, tài liệu)
3. ❌ Assignment & Submission System
4. ❌ Progress Tracking
5. ❌ Materials Management  
6. ❌ Service & Repository layers
7. ❌ Testing suite

**📊 Tổng kết**: ~30% chức năng thực tế (cơ bản đã có, advanced features chưa)

---

### ❓ Có cần Frontend để test không?

**❌ KHÔNG CẦN FRONTEND!**

Bạn có thể test toàn bộ Backend bằng:

**1. Swagger UI (RECOMMENDED) ⭐⭐⭐**
- Mở browser: http://localhost:8000/docs
- Giao diện đẹp, dễ dùng nhất
- Click "Try it out" → Nhập data → Execute
- Tự động quản lý tokens

**2. cURL (Command Line)**
- Dùng terminal
- Mạnh mẽ nhưng phức tạp hơn

**3. Postman / Thunder Client**
- Professional tools
- Tốt cho team collaboration

---

## 🚀 HƯỚNG DẪN TEST NHANH

### Bước 1: Start Backend

```bash
cd /home/icthagws/Github/AI-LMS
docker-compose up -d

# Kiểm tra
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Bước 2: Mở Swagger UI

```
Browser: http://localhost:8000/docs
```

---

## 📝 TEST SCENARIOS (Using Swagger UI)

### SCENARIO 1: Tạo tài khoản và Login

#### 1.1. Đăng ký Admin

**Endpoint**: `POST /api/v1/auth/register`

Click "Try it out", paste JSON:

```json
{
  "email": "admin@ailms.com",
  "password": "Admin123!",
  "full_name": "System Administrator",
  "role": "admin"
}
```

⚠️ **CHÚ Ý**: role phải lowercase: "admin", "instructor", "learner"

Click **Execute**

**Expected**: 201 Created

---

#### 1.2. Đăng ký Giảng viên

```json
{
  "email": "gv1@ailms.com",
  "password": "Teacher123!",
  "full_name": "Nguyen Van A",
  "role": "instructor"
}
```

**Expected**: 201 Created

---

#### 1.3. Đăng ký Học sinh

```json
{
  "email": "hs1@ailms.com",
  "password": "Student123!",
  "full_name": "Tran Thi B",
  "role": "learner"
}
```

**Expected**: 201 Created

---

#### 1.4. Login

**Endpoint**: `POST /api/v1/auth/login`

```json
{
  "email": "admin@ailms.com",
  "password": "Admin123!"
}
```

**Response sẽ có**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

**🔑 QUAN TRỌNG**: Copy `access_token`!

---

#### 1.5. Authorize trong Swagger

1. Click nút **"Authorize"** 🔓 ở góc trên phải
2. Paste token vào field "Value":
   ```
   <paste access_token here>
   ```
3. Click "Authorize"
4. Click "Close"

**✅ Bây giờ tất cả requests sẽ tự động có token!**

---

### SCENARIO 2: Giảng viên tạo Khóa học

#### 2.1. Logout Admin, Login as Instructor

Click "Authorize" → "Logout"

Login lại với `gv1@ailms.com / Teacher123!`

Copy token mới và Authorize

---

#### 2.2. Tạo khóa học Python

**Endpoint**: `POST /api/v1/courses`

```json
{
  "title": "Lập trình Python cho người mới bắt đầu",
  "description": "Khóa học Python toàn diện từ cơ bản đến nâng cao. Học về biến, kiểu dữ liệu, vòng lặp, hàm, OOP. Phù hợp cho người chưa có kinh nghiệm lập trình.",
  "short_description": "Học Python từ con số 0",
  "category": "Programming",
  "level": "beginner",
  "language": "vi",
  "estimated_duration": 1200
}
```

**Expected**: 201 Created

**Response**:
```json
{
  "id": "uuid-here",  ← LƯU LẠI COURSE_ID NÀY!
  "title": "Lập trình Python...",
  "slug": "lap-trinh-python-cho-nguoi-moi-bat-dau",
  "status": "DRAFT",  ← Khóa học đang ở trạng thái DRAFT
  "instructor_id": "...",
  ...
}
```

---

#### 2.3. Xem khóa học vừa tạo

**Endpoint**: `GET /api/v1/courses/{course_id}`

Thay `{course_id}` bằng ID từ bước trước

**Expected**: 200 OK với full course details

---

#### 2.4. Cập nhật khóa học

**Endpoint**: `PUT /api/v1/courses/{course_id}`

```json
{
  "title": "Lập trình Python Complete - Từ Zero đến Hero",
  "short_description": "Master Python với các dự án thực tế",
  "estimated_duration": 1500
}
```

**Expected**: 200 OK

---

#### 2.5. Publish khóa học

**Endpoint**: `POST /api/v1/courses/{course_id}/publish`

Không cần body, chỉ cần Execute

**Expected**: 200 OK

**Response**:
```json
{
  "id": "uuid",
  "status": "PUBLISHED",  ← Status changed!
  "published_at": "2026-03-29T..."
}
```

**✅ Khóa học bây giờ visible cho public!**

---

#### 2.6. Tạo thêm khóa học khác

**Web Development**:
```json
{
  "title": "Phát triển Web hiện đại với React",
  "description": "Học xây dựng ứng dụng web với React, thư viện JavaScript phổ biến nhất.",
  "short_description": "Build web apps với React",
  "category": "Web Development",
  "level": "intermediate",
  "language": "vi",
  "estimated_duration": 1800
}
```

**Data Science**:
```json
{
  "title": "Khoa học dữ liệu với Python",
  "description": "Nhập môn Data Science với Python. Học pandas, numpy, matplotlib.",
  "short_description": "Data analysis và ML với Python",
  "category": "Data Science",
  "level": "intermediate",
  "language": "vi",
  "estimated_duration": 2000
}
```

Publish các khóa học này!

---

### SCENARIO 3: Public Browse Courses (Không cần login)

#### 3.1. Logout

Click "Authorize" → "Logout"

---

#### 3.2. Xem danh sách khóa học

**Endpoint**: `GET /api/v1/courses`

Query Parameters:
- page: 1
- page_size: 10

**Expected**: 200 OK - Chỉ thấy PUBLISHED courses

---

#### 3.3. Tìm kiếm khóa học

**Endpoint**: `GET /api/v1/courses`

Query Parameters:
- search: python

**Expected**: Các khóa học có "python" trong title/description

---

#### 3.4. Filter theo category

**Endpoint**: `GET /api/v1/courses`

Query Parameters:
- category: Programming

**Expected**: Chỉ thấy khóa học Programming

---

### SCENARIO 4: Học sinh Enroll khóa học

#### 4.1. Login as Student

Login với `hs1@ailms.com / Student123!`

Copy token và Authorize

---

#### 4.2. Enroll vào khóa Python

**Endpoint**: `POST /api/v1/courses/{course_id}/enroll`

Dùng course_id của khóa Python

Không cần body

**Expected**: 201 Created

**Response**:
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

**✅ Học sinh đã enroll thành công!**

---

#### 4.3. Thử enroll lại (Sẽ bị reject)

Thử lại endpoint trên

**Expected**: 400 Bad Request - "Already enrolled"

---

#### 4.4. Xem các khóa đã enroll

**Endpoint**: `GET /api/v1/courses/enrollments/me`

**Expected**: 200 OK - List tất cả khóa học đã enroll

---

#### 4.5. Xem lessons của khóa học

**Endpoint**: `GET /api/v1/courses/{course_id}/lessons`

**Expected**: 200 OK - nhưng empty array `[]`

**❌ Lý do**: API cho lessons tồn tại nhưng chưa có API để TẠO lessons!

---

## ❌ KHÔNG THỂ TEST (APIs không tồn tại)

### 1. Tạo Bài giảng (Lesson)
- ❌ API không có
- Model có trong database
- Cần implement: `POST /lessons`

### 2. Upload Video cho bài giảng
- ❌ File upload system chưa có
- Không thể upload video
- Cần implement: File upload service

### 3. Đăng tải tài liệu (Materials)
- ❌ API không có  
- Model có trong database
- Cần implement: `POST /materials`

### 4. Tạo Bài tập (Assignments)
- ❌ API không có
- Model có trong database
- Cần implement: `POST /assignments`

### 5. Nộp bài (Submissions)
- ❌ API không có
- Model có trong database  
- Cần implement: `POST /submissions`

### 6. Track tiến độ học
- ❌ API không có
- Model có trong database
- Cần implement: Progress tracking endpoints

---

## 📊 KẾT LUẬN

### ✅ CÓ THỂ TEST (Hoạt động tốt):

1. ✅ Đăng ký tài khoản (3 roles)
2. ✅ Login/Logout
3. ✅ Quản lý profile
4. ✅ Đổi mật khẩu
5. ✅ Admin quản lý users
6. ✅ Tạo khóa học (Instructor)
7. ✅ Publish khóa học
8. ✅ Browse & search courses
9. ✅ Enroll vào khóa học
10. ✅ Xem khóa học đã enroll

### ❌ CHƯA THỂ TEST (Missing APIs):

1. ❌ Lesson management (CRUD)
2. ❌ Upload video/tài liệu
3. ❌ Materials management
4. ❌ Assignments creation
5. ❌ Submission system
6. ❌ Progress tracking
7. ❌ Grading system

---

## 🎯 CẦN LÀM TIẾP (Priority Order)

### 🔴 URGENT (Cần ngay để có LMS hoàn chỉnh):

1. **Lesson Management API**
   - POST /lessons - Tạo bài giảng
   - PUT /lessons/{id} - Sửa bài giảng
   - DELETE /lessons/{id} - Xóa bài giảng
   - GET /lessons/{id} - Xem chi tiết

2. **File Upload System**
   - Upload video
   - Upload documents (PDF, PPT)
   - Thumbnails
   - File validation

3. **Progress Tracking**
   - Track video watch time
   - Mark lesson complete
   - Calculate course progress

### 🟡 IMPORTANT (Cần cho MVP đầy đủ):

4. **Assignment System**
   - Create assignments
   - Set deadlines
   - Scoring system

5. **Submission System**
   - Submit assignments
   - Grade submissions
   - Feedback system

6. **Materials Management**
   - Upload supplementary materials
   - Download tracking

---

## 💡 TIPS KHI TEST

1. **Token expires sau 30 phút** - Cần login lại
2. **Role phải lowercase**: "admin", "instructor", "learner"
3. **Slug tự động generate** từ title
4. **Course phải PUBLISHED** mới visible cho public
5. **Chỉ owner hoặc admin** mới edit được course
6. **Không thể enroll 2 lần** vào cùng 1 khóa học

---

## 🐛 NẾU GẶP LỖI

### "Backend không chạy"
```bash
cd /home/icthagws/Github/AI-LMS
docker-compose up -d
```

### "401 Unauthorized"
- Token đã hết hạn → Login lại
- Quên Authorize trong Swagger

### "403 Forbidden"
- Role không đủ quyền
- VD: Learner không thể tạo course

### "422 Validation Error"
- Check field format
- Role phải lowercase
- Email phải valid format

---

## 📚 TÀI LIỆU THAM KHẢO

- **Full Documentation**: /home/icthagws/Github/AI-LMS/docs/
- **Backend Status**: docs/BACKEND_STATUS.md
- **API Documentation**: docs/API_DOCUMENTATION.md  
- **Testing Guide**: docs/BACKEND_TESTING_GUIDE.md
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Test Guide Version**: 1.0  
**Date**: 2026-03-29  
**Backend Version**: 1.0.0-alpha
