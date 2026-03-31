# 🚀 Hướng dẫn Triển khai AI-LMS - Chi tiết từng bước

## 📋 Yêu cầu hệ thống

- **Docker**: Phiên bản 20.10 trở lên
- **Docker Compose**: Phiên bản 2.0 trở lên
- **Hệ điều hành**: Linux (Ubuntu/Debian), macOS, hoặc Windows với WSL2

---

## 🔧 BƯỚC 1: Kiểm tra Docker

```bash
# Kiểm tra Docker đã cài đặt chưa
docker --version

# Kiểm tra Docker Compose
docker compose version

# Nếu chưa có Docker, cài đặt bằng lệnh:
# curl -fsSL https://get.docker.com -o get-docker.sh
# sudo sh get-docker.sh
```

**Kết quả mong đợi:**
```
Docker version 20.10.x trở lên
Docker Compose version v2.x.x
```

---

## 📂 BƯỚC 2: Di chuyển vào thư mục dự án

```bash
# Di chuyển vào thư mục dự án
cd /home/icthagws/Github/AI-LMS

# Kiểm tra cấu trúc thư mục
ls -la
```

**Kết quả mong đợi:** Thấy các file/folder:
- `docker-compose.prod.yml`
- `apps/` (backend và frontend)
- `docker/` (nginx config)
- `.env` (nếu đã có)

---

## ⚙️ BƯỚC 3: Cấu hình môi trường (.env)

```bash
# Kiểm tra file .env có tồn tại chưa
cat .env
```

Nếu chưa có file `.env`, tạo file mới:

```bash
cat > .env << 'EOF'
# Database Configuration
DB_USER=lms_user
DB_PASSWORD=lms_password_123
DB_NAME=lms_db
DB_HOST=db
DB_PORT=5432

# Backend Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (cho phép frontend gọi API)
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:3000

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
EOF

# Xem nội dung file vừa tạo
cat .env
```

---

## 🏗️ BƯỚC 4: Build Docker Images (lần đầu)

```bash
# Build tất cả Docker images (Backend, Frontend, Nginx)
# Quá trình này sẽ mất khoảng 5-10 phút
docker compose -f docker-compose.prod.yml build

# Xem tiến trình build
# Đợi cho đến khi thấy "Image ... Built" cho cả 3 services
```

**Kết quả mong đợi:**
```
✔ Container ai-lms-backend Built
✔ Container ai-lms-frontend Built
✔ Container nginx Built
```

---

## 🚀 BƯỚC 5: Khởi động Dự án

```bash
# Khởi động tất cả services (DB, Backend, Frontend, Nginx)
docker compose -f docker-compose.prod.yml up -d

# Flag -d: chạy ở chế độ background (detached)
```

**Kết quả mong đợi:**
```
✔ Container lms_db Created
✔ Container lms_backend Created
✔ Container lms_frontend Created
✔ Container lms_nginx Created
```

---

## ✅ BƯỚC 6: Kiểm tra trạng thái Services

```bash
# Xem danh sách containers đang chạy
docker compose -f docker-compose.prod.yml ps
```

**Kết quả mong đợi:** Tất cả STATUS là `Up` hoặc `Up (healthy)`
```
NAME           STATUS
lms_db         Up (healthy)
lms_backend    Up (healthy)
lms_frontend   Up
lms_nginx      Up
```

Nếu có container nào STATUS là `Exited` hoặc `Unhealthy`, xem logs:

```bash
# Xem logs của container bị lỗi
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
```

---

## 🗄️ BƯỚC 7: Khởi tạo Database (tự động)

Database sẽ tự động được khởi tạo khi Backend start lần đầu (qua Alembic migrations).

Kiểm tra logs để đảm bảo migrations chạy thành công:

```bash
# Xem logs của Backend
docker compose -f docker-compose.prod.yml logs backend | grep -i migration

# Hoặc xem logs realtime
docker compose -f docker-compose.prod.yml logs -f backend
```

**Kết quả mong đợi:** Thấy các dòng như:
```
INFO [alembic.runtime.migration] Running upgrade ... -> ...
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
```

---

## 👥 BƯỚC 8: Tạo Tài khoản Mặc định

```bash
# Tạo 3 tài khoản mặc định (Admin, Teacher, Student)
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

db = SessionLocal()

# Danh sách users cần tạo
users_data = [
    {
        'email': 'admin@test.com',
        'full_name': 'Admin User',
        'password': '00000000',
        'role': 'admin'
    },
    {
        'email': 'teacher@test.com',
        'full_name': 'Teacher User',
        'password': '00000000',
        'role': 'instructor'
    },
    {
        'email': 'student@test.com',
        'full_name': 'Student User',
        'password': '00000000',
        'role': 'learner'
    }
]

# Tạo từng user
for user_data in users_data:
    existing = db.query(User).filter(User.email == user_data['email']).first()
    if not existing:
        user = User(
            email=user_data['email'],
            full_name=user_data['full_name'],
            hashed_password=get_password_hash(user_data['password']),
            role=user_data['role'],
            is_active=True
        )
        db.add(user)
        print(f'✓ Created: {user_data[\"email\"]}')
    else:
        print(f'- Already exists: {user_data[\"email\"]}')

db.commit()
print('Done! All default users are ready.')
"
```

**Kết quả mong đợi:**
```
✓ Created: admin@test.com
✓ Created: teacher@test.com
✓ Created: student@test.com
Done! All default users are ready.
```

---

## 🌐 BƯỚC 9: Truy cập Ứng dụng

Mở trình duyệt web và truy cập:

### 🖥️ Frontend (Trang chính)
```
http://localhost
```

### 🔑 Đăng nhập với các tài khoản:

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| **Admin** | admin@test.com | 00000000 |
| **Teacher** | teacher@test.com | 00000000 |
| **Student** | student@test.com | 00000000 |

### 📚 API Documentation (Swagger)
```
http://localhost/api/docs
```

### 📖 API Documentation (ReDoc)
```
http://localhost/api/redoc
```

---

## 🔍 BƯỚC 10: Test Chức năng Cơ bản

### Test 1: Đăng nhập
1. Truy cập http://localhost
2. Nhập email: `admin@test.com`
3. Nhập password: `00000000`
4. Click "Đăng nhập"
5. **Kết quả:** Vào được Dashboard với thống kê hệ thống

### Test 2: Xem danh sách khóa học
1. Click menu "Khóa học" trên sidebar
2. **Kết quả:** Hiển thị danh sách khóa học (có thể trống ban đầu)

### Test 3: Tạo khóa học mới (Admin/Teacher)
1. Click menu "Tạo khóa học"
2. Điền thông tin khóa học
3. Click "Tạo khóa học"
4. **Kết quả:** Khóa học được tạo thành công

### Test 4: Quản lý người dùng (Admin only)
1. Đăng nhập với `admin@test.com`
2. Click menu "Quản lý Users"
3. **Kết quả:** Hiển thị danh sách người dùng
4. Test thêm/sửa/xóa user

---

## 📊 Các Lệnh Quản lý Hữu ích

### Xem logs của tất cả services:
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Xem logs của một service cụ thể:
```bash
# Backend
docker compose -f docker-compose.prod.yml logs -f backend

# Frontend
docker compose -f docker-compose.prod.yml logs -f frontend

# Database
docker compose -f docker-compose.prod.yml logs -f db

# Nginx
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart một service:
```bash
# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend
```

### Stop tất cả services:
```bash
docker compose -f docker-compose.prod.yml down
```

### Stop và xóa cả volumes (data sẽ mất):
```bash
docker compose -f docker-compose.prod.yml down -v
```

### Xem resource usage:
```bash
docker stats
```

### Truy cập shell của container:
```bash
# Backend
docker compose -f docker-compose.prod.yml exec backend bash

# Frontend
docker compose -f docker-compose.prod.yml exec frontend sh

# Database
docker compose -f docker-compose.prod.yml exec db psql -U lms_user -d lms_db
```

---

## 🔄 Rebuild sau khi thay đổi code

Nếu bạn thay đổi code và muốn áp dụng:

```bash
# 1. Rebuild service cần thiết
docker compose -f docker-compose.prod.yml build backend
# hoặc
docker compose -f docker-compose.prod.yml build frontend

# 2. Restart service đó
docker compose -f docker-compose.prod.yml up -d backend
# hoặc
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## ❌ Dừng Dự án Hoàn toàn

```bash
# Stop tất cả containers nhưng giữ data
docker compose -f docker-compose.prod.yml down

# Stop và xóa cả volumes (database sẽ mất)
docker compose -f docker-compose.prod.yml down -v
```

---

## 🐛 Troubleshooting (Xử lý lỗi thường gặp)

### Lỗi: Port already in use
```bash
# Kiểm tra process đang dùng port 80
sudo lsof -i :80

# Kill process (thay PID)
sudo kill -9 <PID>

# Hoặc đổi port trong docker-compose.prod.yml
# Sửa "80:80" thành "8080:80"
```

### Lỗi: Database connection refused
```bash
# Kiểm tra DB có chạy không
docker compose -f docker-compose.prod.yml ps db

# Xem logs DB
docker compose -f docker-compose.prod.yml logs db

# Restart DB
docker compose -f docker-compose.prod.yml restart db
```

### Lỗi: Frontend không load được
```bash
# Rebuild frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Xem logs
docker compose -f docker-compose.prod.yml logs frontend
```

### Lỗi: Permission denied
```bash
# Thêm user vào docker group
sudo usermod -aG docker $USER
newgrp docker

# Hoặc chạy với sudo
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 📞 Liên hệ & Hỗ trợ

- **Documentation đầy đủ**: Xem folder `docs/`
- **API Documentation**: http://localhost/api/docs
- **GitHub Issues**: Tạo issue trên repository

---

## 🎉 Hoàn thành!

Chúc mừng! Bạn đã triển khai thành công AI-LMS.

**Checklist cuối cùng:**
- ✅ Tất cả containers đang chạy (status: Up/healthy)
- ✅ Truy cập được http://localhost
- ✅ Đăng nhập thành công
- ✅ Tạo được khóa học mới
- ✅ Quản lý được người dùng (Admin)

**Next Steps:**
1. Tạo khóa học mẫu
2. Thêm lessons và materials
3. Thử nghiệm enrollment
4. Tùy chỉnh hệ thống theo nhu cầu

---

**Version**: 1.0  
**Last Updated**: 2026-03-31
