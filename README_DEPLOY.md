# 🚀 Triển khai AI-LMS - Hướng dẫn Nhanh

## ⚡ Cách 1: Tự động (Khuyến nghị)

Chỉ cần 1 lệnh:

```bash
./deploy.sh
```

Script sẽ tự động:
- ✅ Kiểm tra Docker
- ✅ Tạo file .env
- ✅ Build images
- ✅ Khởi động services
- ✅ Tạo tài khoản mặc định

**Thời gian:** 5-10 phút

---

## 🔧 Cách 2: Thủ công (Chi tiết)

### Bước 1: Build và Start
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Bước 2: Tạo tài khoản
```bash
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

db = SessionLocal()
users = [
    ('admin@test.com', 'Admin', 'admin'),
    ('teacher@test.com', 'Teacher', 'instructor'),
    ('student@test.com', 'Student', 'learner')
]

for email, name, role in users:
    if not db.query(User).filter(User.email == email).first():
        db.add(User(
            email=email, full_name=name,
            hashed_password=get_password_hash('00000000'),
            role=role, is_active=True
        ))
        print(f'Created: {email}')

db.commit()
"
```

---

## 🌐 Truy cập

| Mục đích | URL |
|----------|-----|
| Frontend | http://localhost |
| API Docs | http://localhost/api/docs |

## 🔑 Tài khoản

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| Admin | admin@test.com | 00000000 |
| Teacher | teacher@test.com | 00000000 |
| Student | student@test.com | 00000000 |

---

## 📊 Quản lý

### Xem logs
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Dừng
```bash
docker compose -f docker-compose.prod.yml down
```

### Restart
```bash
docker compose -f docker-compose.prod.yml restart backend
```

---

## 📚 Tài liệu chi tiết

Xem file [QUICK_START.md](./QUICK_START.md) để biết hướng dẫn đầy đủ từng bước.

---

**Version:** 1.0  
**Last Updated:** 2026-03-31
