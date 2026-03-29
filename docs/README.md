# 📚 AI-LMS Documentation

Welcome to the AI-LMS documentation! Quick links to get started.

## 📖 Essential Guides

### 🚀 [SETUP_GUIDE.md](SETUP_GUIDE.md)
**Installation & Configuration**
- Environment setup with Docker
- Running the application
- Database migrations
- Troubleshooting

### 📋 [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
**Project Structure & Goals**
- Architecture overview (70% MVP complete)
- Feature breakdown and completion status
- Folder structure
- Key technologies

### 📡 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
**Complete API Reference**
- All 49 endpoints with examples
- Authentication flow
- Request/response formats
- Error handling

---

## 🎯 Quick Start

```bash
# Setup
git clone <repo>
cd AI-LMS
cp .env.example .env

# Run with migrations
make start

# Access
Backend:  http://localhost:8000
Swagger:  http://localhost:8000/docs
ReDoc:    http://localhost:8000/redoc
```

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | ✅ 70% | 49/70 endpoints |
| Database | ✅ 100% | 12 tables ready |
| File Upload | ✅ 100% | Videos, docs, images |
| Testing | ⚠️ 30% | Manual tested |
| Frontend | ❌ 0% | Phase 2 |
| AI Features | ❌ 0% | Phase 2 |

## 👥 Documentation by Role

**👨‍💼 New to project?** → Start with PROJECT_OVERVIEW.md  
**🔧 Setting up?** → Follow SETUP_GUIDE.md  
**📡 Integrating API?** → Check API_DOCUMENTATION.md  
**🐛 Having issues?** → See troubleshooting in SETUP_GUIDE.md

## 📂 Docs Structure

```
docs/
├── README.md (you are here)
├── PROJECT_OVERVIEW.md
├── SETUP_GUIDE.md
└── API_DOCUMENTATION.md
```

---

**Last Updated**: 2026-03-29  
**Status**: MVP Phase 1 (70% complete)
