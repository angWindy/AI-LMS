# AI-LMS Frontend

Next.js frontend for AI-LMS.

## Stack

- Next.js 14 App Router.
- TypeScript.
- Tailwind CSS and Radix/shadcn-style components.
- Zustand auth store.
- Axios API client with JWT attach and refresh retry.

## Run Locally

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Or create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open `http://localhost:3000`.

In production-like Compose, `NEXT_PUBLIC_API_URL` is empty and requests go
through same-origin Nginx.

## Structure

```text
src/app/          routes/layouts
src/components/   UI and feature components
src/lib/api/      API clients
src/lib/auth/     persisted auth store
src/types/        TypeScript API/domain types
```

## Main Routes

```text
/
/login
/register
/dashboard
/profile
/courses
/courses/my
/courses/create
/courses/[slug]
/courses/[slug]/lessons/[lessonId]/studio
/courses/[slug]/tests/[assignmentId]
/lessons/[id]/video
/lessons/[id]/assignment
/lessons/[id]/materials/[materialId]
/question-bank
/users
```

Navigation role visibility is in `src/app/(main)/layout.tsx`; backend
permissions remain authoritative.

## API Client

`src/lib/api/client.ts` calls:

```text
${NEXT_PUBLIC_API_URL}/api/v1
```

It attaches the access token, refreshes once on `401`, then retries the original
request.

## Commands

```bash
npm run dev
npm run build
npm run lint
```

## Notes

- Question Bank UI only asks for lesson/count; backend assigns metadata.
- AI generation requests have long client timeouts.
- Assignment chatbot is hint-focused and does not receive answer keys.
