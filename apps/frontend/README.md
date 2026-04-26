# AI-LMS Frontend

Next.js 14 Frontend cho hệ thống AI-LMS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Setup environment
cp .env.example .env.local

# Run development server
npm run dev
```

Truy cập: http://localhost:3000

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Library**: shadcn/ui
- **State**: Zustand (auth) + React Query (data fetching)
- **Forms**: React Hook Form + Zod validation
- **API Client**: Axios with JWT interceptors

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth pages (login, register)
│   ├── (main)/             # Protected pages
│   │   ├── dashboard/      # Role-based dashboard
│   │   ├── courses/        # Course pages
│   │   ├── users/          # Admin: user management
│   │   └── profile/        # User settings
│   ├── layout.tsx
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── layout/             # Layout components
│   └── shared/             # Shared components
├── lib/
│   ├── api/                # API client & services
│   ├── auth/               # Auth store (Zustand)
│   └── utils.ts            # Utility functions
├── types/                  # TypeScript interfaces
├── hooks/                  # Custom React hooks
└── middleware.ts           # Route protection
```

## 📱 Pages

| Page | Route | Role | Description |
|------|-------|------|-------------|
| Landing | `/` | Public | Landing page |
| Login | `/login` | Public | User login |
| Register | `/register` | Public | New registration |
| Dashboard | `/dashboard` | All | Role-based dashboard |
| Courses | `/courses` | All | Browse courses |
| Course Detail | `/courses/[slug]` | All | View course |
| Create Course | `/courses/create` | Instructor/Admin | Create new course |
| My Courses | `/courses/my` | Instructor/Admin | Manage courses |
| Enrolled | `/courses/enrolled` | Learner | Enrolled courses |
| Users | `/users` | Admin | User management |
| Profile | `/profile` | All | Account settings |

## 🔧 Commands

```bash
npm run dev      # Development server
npm run build    # Production build
npm start        # Start production server
npm run lint     # Run ESLint
npm run type-check # TypeScript check
```

## 🔐 Authentication

JWT-based authentication với:
- Access token (30 min expiry)
- Refresh token (7 days)
- Automatic token refresh via Axios interceptors
- Persistent auth state với Zustand + localStorage

## 📡 API Integration

Backend API: `http://localhost:8000`

Configured in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎨 UI Components

Using shadcn/ui components:
- Button, Input, Textarea, Label
- Card, Badge, Avatar
- Select, Dropdown Menu
- Dialog, Tabs (can be added)

## 📋 Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000
```
