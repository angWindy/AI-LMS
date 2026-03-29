# Documentation Index - AI-LMS

Chào mừng bạn đến với tài liệu dự án AI-LMS! Đây là hệ thống quản lý học tập hiện đại tích hợp AI.

## 📚 Mục lục tài liệu

### 1. [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)
**Tổng quan dự án - Bắt đầu từ đây!**

Tài liệu này cung cấp cái nhìn tổng quan về:
- Mục tiêu và tầm nhìn của dự án
- Tiến độ phát triển hiện tại (Phase 1 - MVP: 70% hoàn thành)
- Kiến trúc hệ thống high-level
- Cấu trúc thư mục chi tiết
- Roadmap và kế hoạch phát triển
- Các vấn đề cần giải quyết
- Metrics và KPIs

**Đọc tài liệu này nếu bạn:**
- ✅ Mới tham gia dự án
- ✅ Muốn hiểu tổng quan về hệ thống
- ✅ Cần biết tiến độ hiện tại
- ✅ Muốn xem roadmap tương lai

---

### 2. [SETUP_GUIDE.md](./SETUP_GUIDE.md)
**Hướng dẫn cài đặt và triển khai**

Hướng dẫn chi tiết từng bước để:
- Cài đặt Docker và các dependencies
- Clone repository và setup environment
- Khởi động services (Database, Backend API)
- Chạy database migrations
- Verify API hoạt động
- Setup môi trường development
- Troubleshooting các vấn đề thường gặp

**Đọc tài liệu này nếu bạn:**
- ✅ Muốn chạy project lần đầu
- ✅ Cần setup môi trường development
- ✅ Gặp lỗi khi cài đặt
- ✅ Muốn deploy production

---

### 3. [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)
**Chi tiết về database schema**

Tài liệu đầy đủ về:
- 11 database tables và relationships
- Column definitions với data types
- Indexes và constraints
- Business rules cho từng table
- Entity Relationship Diagram (ERD)
- Migration guide
- Database optimization tips
- Query examples
- Maintenance procedures

**Đọc tài liệu này nếu bạn:**
- ✅ Cần hiểu cấu trúc database
- ✅ Muốn thêm tables mới
- ✅ Tối ưu queries
- ✅ Làm việc với migrations

---

### 4. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
**API Reference đầy đủ**

Documentation cho tất cả API endpoints:
- **Authentication**: register, login, logout, refresh token
- **User Management**: CRUD operations (Admin only)
- **Course Management**: courses, lessons, enrollment
- Error handling và status codes
- Request/Response examples
- Authentication flow
- API client examples (JavaScript, Python)
- cURL examples

**Đọc tài liệu này nếu bạn:**
- ✅ Phát triển frontend
- ✅ Tích hợp API
- ✅ Test endpoints
- ✅ Cần API reference

---

### 5. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)
**Hướng dẫn phát triển cho developers**

Best practices và workflow cho:
- Coding standards (PEP 8, type hints, docstrings)
- Project architecture (Clean Architecture)
- Thêm features mới (step-by-step)
- Database migrations
- Writing tests
- API development patterns
- Common development tasks
- Debugging tips
- Git workflow

**Đọc tài liệu này nếu bạn:**
- ✅ Contribute code vào project
- ✅ Thêm features mới
- ✅ Viết tests
- ✅ Cần coding guidelines

---

## 🎯 Quick Start Guide

### Nếu bạn là...

#### 🆕 **New Developer** (Lần đầu tiếp cận dự án)
1. Đọc [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - Hiểu tổng quan
2. Đọc [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Cài đặt môi trường
3. Explore code trong `apps/backend/app/`
4. Đọc [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Bắt đầu code

#### 💻 **Backend Developer**
1. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup môi trường
2. [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Hiểu database
3. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Coding standards
4. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API reference

#### 🎨 **Frontend Developer**
1. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Xem API endpoints
2. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup backend để test
3. Check `apps/frontend/` - Frontend structure (đang phát triển)

#### 📊 **Project Manager / Product Owner**
1. [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - Tiến độ và roadmap
2. Check "Phase 1 - MVP" section - Xem tính năng đã hoàn thành
3. Check "Roadmap" section - Kế hoạch tương lai

#### 🧪 **QA / Tester**
1. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup test environment
2. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - Test API endpoints
3. Use Swagger UI: http://localhost:8000/docs

---

## 📂 Cấu trúc Documentation

```
docs/
├── README.md                    # File này - Index và navigation
├── PROJECT_OVERVIEW.md          # Tổng quan dự án
├── SETUP_GUIDE.md              # Hướng dẫn cài đặt
├── DATABASE_SCHEMA.md          # Database documentation
├── API_DOCUMENTATION.md        # API reference
├── DEVELOPMENT_GUIDE.md        # Development guidelines
└── ai/                         # AI services docs (future)
    ├── CHATBOT.md              # (Planned) AI chatbot docs
    ├── ANALYTICS.md            # (Planned) Analytics service
    └── RECOMMENDATION.md       # (Planned) Recommendation system
```

---

## 🔄 Tài liệu đang phát triển

### Kế hoạch bổ sung tài liệu:

#### Phase 2 - Advanced Features
- [ ] **FRONTEND_GUIDE.md** - Frontend development guide (Next.js)
- [ ] **TESTING_GUIDE.md** - Comprehensive testing guide
- [ ] **DEPLOYMENT_GUIDE.md** - Production deployment guide
- [ ] **SECURITY_GUIDE.md** - Security best practices

#### Phase 3 - AI Integration
- [ ] **AI_CHATBOT.md** - AI assistant integration guide
- [ ] **AI_ANALYTICS.md** - Analytics service documentation
- [ ] **AI_RECOMMENDATIONS.md** - Recommendation system docs

#### Operational Docs
- [ ] **MONITORING_GUIDE.md** - Application monitoring
- [ ] **BACKUP_RECOVERY.md** - Backup and recovery procedures
- [ ] **PERFORMANCE_TUNING.md** - Performance optimization
- [ ] **CONTRIBUTING.md** - Contribution guidelines

---

## 📖 Documentation Standards

### Khi viết tài liệu mới:

1. **Use Markdown** - Tất cả docs dùng .md format
2. **Clear Headers** - Sử dụng hierarchy rõ ràng (H1, H2, H3)
3. **Code Examples** - Include working code examples
4. **Screenshots** - Thêm hình ảnh khi cần thiết
5. **Keep Updated** - Update khi có thay đổi code
6. **Vietnamese + English** - Support cả 2 ngôn ngữ khi có thể

### Template Structure:

```markdown
# Title

## Overview
Brief description...

## Prerequisites
What you need before...

## Step-by-Step Guide
1. First step
2. Second step
...

## Examples
Practical examples...

## Troubleshooting
Common issues...

## References
Links to related docs...
```

---

## 🔗 External Resources

### Official Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Docs](https://docs.docker.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)

### Learning Resources
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [RESTful API Design](https://restfulapi.net/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 🤝 Contributing to Documentation

Nếu bạn tìm thấy lỗi hoặc muốn cải thiện tài liệu:

1. **Báo lỗi**: Tạo GitHub issue với label `documentation`
2. **Đề xuất cải tiến**: Submit pull request với changes
3. **Thêm ví dụ**: Bổ sung practical examples
4. **Dịch thuật**: Giúp dịch docs sang tiếng Việt

### Documentation Checklist:
- [ ] Nội dung chính xác và updated
- [ ] Code examples có thể chạy được
- [ ] Formatting consistent
- [ ] Links hoạt động
- [ ] Ngữ pháp và chính tả đúng
- [ ] Screenshots clear (nếu có)

---

## 📊 Documentation Stats

| Document | Pages | Status | Last Updated |
|----------|-------|--------|--------------|
| PROJECT_OVERVIEW | 8 | ✅ Complete | 2026-03-29 |
| SETUP_GUIDE | 10 | ✅ Complete | 2026-03-29 |
| DATABASE_SCHEMA | 15 | ✅ Complete | 2026-03-29 |
| API_DOCUMENTATION | 18 | ✅ Complete | 2026-03-29 |
| DEVELOPMENT_GUIDE | 16 | ✅ Complete | 2026-03-29 |
| **Total** | **67** | **5/5** | - |

---

## 🎯 Documentation Roadmap

### Q1 2026 ✅
- [x] Project Overview
- [x] Setup Guide
- [x] Database Schema
- [x] API Documentation
- [x] Development Guide

### Q2 2026 📝
- [ ] Frontend Development Guide
- [ ] Testing Guide
- [ ] Deployment Guide
- [ ] API Client Libraries

### Q3 2026 🔮
- [ ] AI Services Documentation
- [ ] Performance Tuning Guide
- [ ] Security Best Practices
- [ ] Monitoring & Logging

### Q4 2026 🚀
- [ ] Video Tutorials
- [ ] Interactive API Explorer
- [ ] Architecture Decision Records (ADRs)
- [ ] Case Studies

---

## 📞 Need Help?

- **Technical Issues**: Check [SETUP_GUIDE.md](./SETUP_GUIDE.md#troubleshooting)
- **API Questions**: See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Development Questions**: Read [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)
- **Other Questions**: Open GitHub issue or contact team

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-29 | Initial documentation set |
| | | - Project Overview |
| | | - Setup Guide |
| | | - Database Schema |
| | | - API Documentation |
| | | - Development Guide |

---

**Last Updated**: 2026-03-29  
**Maintained by**: AI-LMS Development Team  
**License**: MIT (same as project)

---

## 🌟 Quick Links

- [🏠 Project Home](../README.md)
- [📋 Project Overview](./PROJECT_OVERVIEW.md)
- [⚙️ Setup Guide](./SETUP_GUIDE.md)
- [🗃️ Database Schema](./DATABASE_SCHEMA.md)
- [🔌 API Documentation](./API_DOCUMENTATION.md)
- [💻 Development Guide](./DEVELOPMENT_GUIDE.md)
- [📊 Swagger UI](http://localhost:8000/docs) *(when running)*
- [🔍 ReDoc](http://localhost:8000/redoc) *(when running)*

---

**Happy Coding! 🚀**
