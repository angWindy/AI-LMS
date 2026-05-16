# AI-LMS Frontend

Next.js frontend for AI-LMS.

## Stack

- Next.js 14 App Router.
- TypeScript.
- Tailwind CSS.
- shadcn/ui components.
- Zustand for auth state.
- Axios API client with JWT handling.

## Local Run

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Environment

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Structure

```text
src/app/          routes and layouts
src/components/   UI and feature components
src/lib/api/      API client modules
src/lib/auth/     auth store
src/types/        shared TypeScript types
```

## Main Routes

- `/login`
- `/register`
- `/dashboard`
- `/courses`
- `/courses/my`
- `/courses/enrolled`
- `/question-bank`
- `/users`
- `/profile`

## Commands

```bash
npm run dev
npm run build
npm run lint
```

The Question Bank generation UI only asks for lesson and count. Difficulty and purpose metadata are allocated by backend generation logic.
