# Architecture

```text
Next.js frontend -> FastAPI /api/v1 -> PostgreSQL + pgvector
                                      -> local /storage files
                                      -> llm workflows -> Gemini/mock
```

## Applications

- `apps/backend`: FastAPI API, auth, role checks, DB access, file serving,
  material ingestion, and AI orchestration.
- `apps/frontend`: Next.js App Router UI. Auth guard is client-side in
  `src/app/(main)/layout.tsx`; API remains the permission authority.
- `llm`: provider abstraction, prompts, generation workflows, and RAG helpers.

## Runtime Modes

- `docker-compose.yml`: PostgreSQL + backend for development. Run frontend with
  `npm run dev`.
- `docker-compose.prod.yml`: PostgreSQL + backend + frontend + Nginx. Nginx
  serves `/`, proxies `/api/` and `/storage/`, and exposes `/docs`.

## Backend Flow

1. `app/main.py` mounts `/api/v1`.
2. Routers in `app/api/v1/` validate payloads and enforce dependencies.
3. Services in `app/services/` run AI/RAG/file workflows.
4. SQLAlchemy models persist state.
5. FastAPI returns Pydantic response schemas.

## Frontend Flow

`src/lib/api/client.ts` calls `${NEXT_PUBLIC_API_URL}/api/v1`, attaches bearer
tokens from Zustand, refreshes tokens after one `401`, and retries once.

Use `NEXT_PUBLIC_API_URL=http://localhost:8000` for local dev. Leave it empty in
production-like Compose so calls go through same-origin Nginx.

## Ownership And Visibility

- Admin manages all users and content.
- Instructor manages owned courses and their lessons/materials/questions.
- Learner reads published content, tracks progress, submits assignments, and
  uses chatbot flows.
- Learner assignment responses hide answer keys.

The old `enrollments` table was dropped by migration
`20260517_1000_b2c3d4e5f6a7_drop_enrollments.py`.

## AI Workflows

- Assignment generation: lesson/course context -> JSON questions -> validation.
- Assignment feedback: submission context -> per-answer feedback and score.
- Slide generation: context -> document IR -> slides JSON -> PDF.
- Chatbot: LMS scope + history + optional RAG/image context.
- Assignment chatbot: sanitized assignment context, no answer keys, hints only.
- RAG: PDF/DOCX material -> chunks -> Gemini embeddings -> pgvector search.
