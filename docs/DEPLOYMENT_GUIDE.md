# Hướng dẫn Triển khai AI-LMS

## 📋 Yêu cầu hệ thống

### Môi trường Development
- **Node.js**: v18+ (khuyến nghị v20 LTS)
- **Python**: 3.11+
- **Docker & Docker Compose**: v2.0+
- **PostgreSQL**: 15+ (nếu không dùng Docker)
- **Git**

### Môi trường Production
- **Server**: Ubuntu 22.04 LTS / Debian 12+
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB)
- **Storage**: Tối thiểu 20GB
- **Domain**: Với SSL certificate

---

## 🚀 Triển khai Development

### Bước 1: Clone Repository

```bash
git clone https://github.com/your-repo/AI-LMS.git
cd AI-LMS
```

### Bước 2: Cấu hình Environment

```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa các giá trị
nano .env
```

**Nội dung `.env`:**
```env
# Database
DB_USER=lms_user
DB_PASSWORD=your_secure_password_here
DB_NAME=lms_db
DB_PORT=5432

# Backend
BACKEND_PORT=8000
SECRET_KEY=your-secret-key-minimum-32-characters-long

# CORS (Frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
STORAGE_PATH=./storage
```

### Bước 3: Khởi động Backend với Docker

```bash
# Khởi động tất cả services (backend + database)
make start

# Hoặc sử dụng docker-compose trực tiếp
docker-compose up -d

# Kiểm tra services đang chạy
docker-compose ps

# Xem logs
make logs-backend
```

### Bước 4: Chạy Database Migrations

```bash
# Tạo migration mới (nếu cần)
make migration MESSAGE="initial setup"

# Chạy migrations
make migrate
```

### Bước 5: Khởi động Frontend

```bash
# Di chuyển vào thư mục frontend
cd apps/frontend

# Cài đặt dependencies
npm install

# Cấu hình environment
cp .env.example .env.local
# Chỉnh sửa NEXT_PUBLIC_API_URL nếu cần

# Chạy development server
npm run dev
```

### Bước 6: Truy cập ứng dụng

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🏭 Triển khai Production

### Option 1: Docker Compose với Nginx (Khuyến nghị)

#### 1. Chuẩn bị Server

```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Thêm user vào docker group
sudo usermod -aG docker $USER
newgrp docker

# Cài đặt Docker Compose (nếu chưa có)
sudo apt install docker-compose-plugin
```

#### 2. Clone và Cấu hình

```bash
# Clone repo
git clone https://github.com/your-repo/AI-LMS.git
cd AI-LMS

# Cấu hình production environment
cp .env.example .env
nano .env
```

**Cấu hình `.env` cho Production:**
```env
# Database
DB_USER=lms_user
DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE
DB_NAME=lms_db
DB_PORT=5432

# Backend
BACKEND_PORT=8000
SECRET_KEY=your-very-long-random-secret-key-at-least-32-chars

# Production mode
CORS_ORIGINS=http://localhost,https://your-domain.com
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### 3. Build và Start (Tự động)

```bash
# Build tất cả images và start services
docker compose -f docker-compose.prod.yml up -d --build

# Kiểm tra services
docker compose -f docker-compose.prod.yml ps

# Xem logs
docker compose -f docker-compose.prod.yml logs -f
```

**Services sẽ bao gồm:**
- `lms_nginx`: Reverse proxy (port 80)
- `lms_frontend`: Next.js app (port 3000 internal)
- `lms_backend`: FastAPI (port 8000 internal)
- `lms_db`: PostgreSQL (port 5432 internal)

#### 4. Tạo tài khoản mặc định

```bash
# Chạy script tạo users mặc định
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

db = SessionLocal()

# Tạo Admin
admin = User(
    email='admin@test.com',
    full_name='Admin',
    hashed_password=get_password_hash('00000000'),
    role='admin',
    is_active=True
)

# Tạo Teacher
teacher = User(
    email='teacher@test.com',
    full_name='Teacher',
    hashed_password=get_password_hash('00000000'),
    role='instructor',
    is_active=True
)

# Tạo Student
student = User(
    email='student@test.com',
    full_name='Student',
    hashed_password=get_password_hash('00000000'),
    role='learner',
    is_active=True
)

for user in [admin, teacher, student]:
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing:
        db.add(user)
        print(f'Created: {user.email}')

db.commit()
print('Done!')
"
```

#### 5. Truy cập ứng dụng

- **Frontend**: http://localhost (hoặc http://your-domain.com)
- **Backend API**: http://localhost/api/v1
- **API Docs**: http://localhost/api/docs

#### 6. (Optional) Cấu hình HTTPS với Certbot

```bash
# Cài đặt certbot
sudo apt install certbot

# Tạo certificate
sudo certbot certonly --standalone -d your-domain.com

# Cập nhật nginx config để dùng SSL
# Chỉnh sửa docker/nginx/nginx.conf
```

---

### Option 2: Kubernetes (Scale lớn)

Tham khảo thư mục `k8s/` (nếu có) hoặc liên hệ team DevOps.

---

## 🔧 Các lệnh hữu ích

### Docker Commands (Production)
```bash
# Xem logs
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f db

# Restart services
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml restart backend

# Rebuild container (sau khi thay đổi code)
docker compose -f docker-compose.prod.yml up -d --build frontend
docker compose -f docker-compose.prod.yml up -d --build backend

# Truy cập container shell
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec db psql -U lms_user -d lms_db

# Stop all services
docker compose -f docker-compose.prod.yml down

# Dọn dẹp
docker compose -f docker-compose.prod.yml down -v  # Xóa cả volumes
docker system prune -a  # Xóa unused images
```

### Frontend Commands
```bash
cd apps/frontend

npm run dev      # Development mode
npm run build    # Production build
npm start        # Start production server
npm run lint     # Run linter
npm run type-check  # TypeScript check
```

### Backend Commands
```bash
# Vào container backend
make shell-backend

# Run tests
make test

# Format code
make format

# Lint
make lint
```

---

## 📊 Monitoring & Logs

### Xem logs
```bash
# All services
make logs

# Backend only
make logs-backend

# Realtime
docker-compose logs -f --tail=100
```

### Health Check
```bash
# Backend health
curl http://localhost:8000/health

# Database connection
docker-compose exec db pg_isready
```

---

## 🔐 Security Checklist

- [ ] Thay đổi tất cả default passwords
- [ ] Set `SECRET_KEY` là random string dài (32+ ký tự)
- [ ] Cấu hình `CORS_ORIGINS` chỉ cho phép domains cần thiết
- [ ] Enable HTTPS với SSL certificate hợp lệ
- [ ] Cấu hình firewall (chỉ mở ports 80, 443)
- [ ] Regular backup database
- [ ] Update packages định kỳ

---

## 🆘 Troubleshooting

### Backend không khởi động
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from app.db.session import get_db; print('OK')"

# Rebuild
docker-compose up -d --build backend
```

### Frontend build lỗi
```bash
# Clear cache
rm -rf apps/frontend/.next
rm -rf apps/frontend/node_modules
npm install
npm run build
```

### Database connection refused
```bash
# Check if db is running
docker-compose ps db

# Restart db
docker-compose restart db

# Check logs
docker-compose logs db
```

### Port đã được sử dụng
```bash
# Tìm process đang dùng port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill process (thay PID)
sudo kill -9 <PID>

# Hoặc đổi port trong .env
BACKEND_PORT=8001
```

---

## 📞 Hỗ trợ

- Xem [README.md](./README.md) để biết thêm chi tiết
- Tạo GitHub Issue nếu gặp vấn đề
- Liên hệ team development

---

**Last Updated**: 2026-03-31
