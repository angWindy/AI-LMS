# Triển khai AI-LMS trên angwindy-ai-lms

## 🚀 Hướng dẫn nhanh

### Bước 1: Setup domain name

Chạy script để thêm domain vào /etc/hosts:

```bash
sudo ./setup-domain.sh
```

Hoặc thêm thủ công:
```bash
sudo nano /etc/hosts
```
Thêm dòng:
```
127.0.0.1 angwindy-ai-lms
```

### Bước 2: Triển khai

```bash
# Triển khai toàn bộ hệ thống
make prod

# Hoặc rebuild nếu đã chạy rồi
make prod-rebuild
```

### Bước 3: Truy cập

- **Trang chủ**: http://angwindy-ai-lms
- **Đăng nhập**: http://angwindy-ai-lms/login
- **Đăng ký**: http://angwindy-ai-lms/register
- **Dashboard**: http://angwindy-ai-lms/dashboard
- **API Docs**: http://angwindy-ai-lms/docs

## 🔧 Lệnh quản lý

```bash
# Xem logs
make prod-logs

# Dừng hệ thống
make prod-stop

# Khởi động lại
make prod

# Rebuild toàn bộ
make prod-rebuild
```

## 📊 Kiểm tra services

```bash
# Xem containers đang chạy
docker ps

# Xem logs riêng
docker logs lms_nginx
docker logs lms_frontend
docker logs lms_backend
docker logs lms_db
```

## 🔐 Tài khoản test

Sau khi triển khai, ba tài khoản seed đã được tạo tự động:

- **Admin**: admin@test.com / 00000000
- **Learner**: student@test.com / 00000000
- **Teacher**: teacher@test.com / 00000000

Bạn có thể đăng nhập tại: http://localhost/login

## 🌐 Kiến trúc

```
    http://angwindy-ai-lms (port 80)
              │
              ▼
        ┌─────────┐
        │  Nginx  │ (Reverse Proxy)
        └────┬────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌─────────┐      ┌─────────┐
│Frontend │      │ Backend │
│Next.js  │      │ FastAPI │
│  :3000  │      │  :8000  │
└─────────┘      └────┬────┘
                      │
                      ▼
                 ┌─────────┐
                 │Postgres │
                 │  :5432  │
                 └─────────┘
```

## 📝 Troubleshooting

### Domain không hoạt động
```bash
# Kiểm tra /etc/hosts
cat /etc/hosts | grep angwindy

# Nếu chưa có, chạy:
sudo ./setup-domain.sh
```

### Services không khởi động
```bash
# Xem logs
make prod-logs

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Port 80 đã được dùng
```bash
# Kiểm tra process đang dùng port 80
sudo lsof -i :80

# Dừng service đó hoặc đổi port trong docker-compose.prod.yml
```
