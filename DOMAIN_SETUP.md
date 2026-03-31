# 🌐 Thiết lập Domain angwindy-ai-lms

## Cách 1: Dùng script tự động (Khuyến nghị)

```bash
sudo ./setup-domain.sh
```

## Cách 2: Thêm thủ công

### Trên Linux/Mac:

```bash
sudo nano /etc/hosts
```

Thêm dòng sau vào cuối file:
```
127.0.0.1 angwindy-ai-lms
```

Lưu lại (Ctrl+O, Enter, Ctrl+X)

### Trên Windows:

1. Mở Notepad **với quyền Administrator**
2. Mở file: `C:\Windows\System32\drivers\etc\hosts`
3. Thêm dòng:
   ```
   127.0.0.1 angwindy-ai-lms
   ```
4. Lưu lại

## Kiểm tra

Sau khi thêm domain, kiểm tra:

```bash
# Linux/Mac
ping angwindy-ai-lms

# Hoặc
curl http://angwindy-ai-lms
```

Nếu thấy response từ server là thành công!

## Truy cập hệ thống

- **Trang chủ**: http://angwindy-ai-lms
- **Đăng nhập**: http://angwindy-ai-lms/login
- **Đăng ký**: http://angwindy-ai-lms/register
- **Dashboard**: http://angwindy-ai-lms/dashboard
- **API Docs**: http://angwindy-ai-lms/docs

## Gỡ bỏ domain

Nếu muốn xóa domain:

```bash
sudo nano /etc/hosts
```

Xóa dòng chứa `angwindy-ai-lms`
