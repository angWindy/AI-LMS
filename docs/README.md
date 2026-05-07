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
- Architecture overview (85% MVP complete)
- Feature breakdown and completion status
- Folder structure
- Key technologies

### 📡 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
**Complete API Reference**
- All 49 endpoints with examples
- Authentication flow
- Request/response formats
- Error handling

### 🧠 [QUESTION_BANK.md](QUESTION_BANK.md)
**Question Bank**
- Reusable course/lesson questions
- Difficulty and purpose metadata
- Follow-up notes for assignment/test reuse

### 🚢 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**Deployment Instructions**
- Development setup
- Production deployment (Docker)
- Nginx configuration
- SSL setup

---

## 🎯 Quick Start

### Backend
```bash
# Setup
git clone <repo>
cd AI-LMS
cp .env.example .env

# Run with migrations
make start

# Access
# Backend:  http://localhost:8000
# Swagger:  http://localhost:8000/docs
```

### Frontend
```bash
cd apps/frontend
npm install
cp .env.example .env.local
npm run dev

# Access
# Frontend: http://localhost:3000
```

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | ✅ 85% | 49 endpoints |
| Database | ✅ 100% | 12 tables ready |
| File Upload | ✅ 100% | Videos, docs, images |
| **Frontend** | ✅ **100%** | **Next.js 14 + shadcn/ui** |
| Testing | ⚠️ 30% | Manual tested |
| AI Features | ✅ Partially delivered | Lesson/video chatbot + assignment helper |

## 👥 Documentation by Role

**👨‍💼 New to project?** → Start with PROJECT_OVERVIEW.md  
**🔧 Setting up?** → Follow SETUP_GUIDE.md  
**📡 Integrating API?** → Check API_DOCUMENTATION.md  
**🚢 Deploying?** → Read DEPLOYMENT_GUIDE.md  
**🐛 Having issues?** → See troubleshooting in SETUP_GUIDE.md

## 📂 Docs Structure

```
docs/
├── README.md (you are here)
├── PROJECT_OVERVIEW.md
├── SETUP_GUIDE.md
├── QUESTION_BANK.md
├── API_DOCUMENTATION.md
└── DEPLOYMENT_GUIDE.md ✅ NEW
```

---

**Last Updated**: 2026-05-07
**Status**: MVP Phase 1 (updated) - AI helpers partially delivered
