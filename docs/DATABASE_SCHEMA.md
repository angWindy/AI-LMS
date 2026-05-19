# Database Schema Notes

Source of truth:

- Models: `apps/backend/app/models/`
- Migrations: `apps/backend/app/db/migrations/versions/`

Current migration head:

```text
8b1c9f2d3a4e_course_levels
```

## Active Tables

Auth:

- `users`
- `refresh_tokens`

Course content:

- `courses`
- `lessons`
- `materials`
- `lesson_progress`

Assignments:

- `assignments`
- `assignment_lesson_scopes`
- `assignment_questions`
- `assignment_options`
- `submissions`
- `submission_answers`

AI/content:

- `question_bank_questions`
- `question_bank_options`
- `slide_decks`
- `ai_conversations`
- `ai_messages`
- `rag_documents`
- `rag_chunks`
- `rag_search_sessions`
- `rag_search_results`
- `rag_integrations`

`enrollments` was removed by migration
`20260517_1000_b2c3d4e5f6a7_drop_enrollments.py`.

## Key Relationships

- Course owns lessons, materials, assignments, question bank records, slide
  decks, and RAG docs.
- Lesson owns lesson materials, progress records, question bank records, slide
  decks, and optional assignment scope.
- Material may map to one `rag_documents.material_id`.
- Assignment owns questions, options, submissions, and test lesson scopes.
- Submission owns one `submission_answers` row per question answer.

## Enums

```text
UserRole: admin, instructor, learner
CourseStatus: draft, published, archived
CourseLevel: primary, lower_secondary, upper_secondary, higher_ed
MaterialType: video, document, link, quiz
AssignmentType: practice, test
AssignmentQuestionType: multiple_choice, essay
QuestionDifficulty: easy, medium, hard
QuestionPurposeType: practice, shared, assessment
SubmissionStatus: submitted, graded, returned
```

`courses.level` is required and constrained to `CourseLevel`.

## Question Metadata

`assignment_questions` and `question_bank_questions` store `difficulty` and
`purpose_type`.

Generated Question Bank sets:

- difficulty: `easy/medium/hard = 40/40/20`
- purpose inside each difficulty group:
  `practice/shared/assessment = 65/15/20`

Practice assignments use `practice/shared`; tests use `assessment/shared`.

## RAG Vectors

`rag_chunks.embedding` uses `Vector(3072)`, matching Gemini
`gemini-embedding-001`. The RAG migration enables PostgreSQL `vector`.

## Migration Commands

```bash
cd apps/backend
alembic upgrade head
alembic revision --autogenerate -m "message"
```

Docker:

```bash
docker compose exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```
