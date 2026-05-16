# Database Schema Notes

The source of truth is the SQLAlchemy models in `apps/backend/app/models/` and migrations in `apps/backend/app/db/migrations/versions/`.

## Main Tables

- `users`
- `courses`
- `lessons`
- `materials`
- `enrollments`
- `assignments`
- `assignment_questions`
- `assignment_options`
- `submissions`
- `question_bank_questions`
- `question_bank_options`
- RAG tables from the RAG migration.
- Slide deck tables from the slide deck migrations.

## Question Metadata

`assignment_questions` and `question_bank_questions` include:

- `difficulty`: `easy`, `medium`, `hard`.
- `purpose_type`: `practice`, `shared`, `assessment`.

Generated Question Bank records use:

- Difficulty ratio: `easy/medium/hard = 40/40/20`.
- Purpose ratio inside each difficulty group: `practice/shared/assessment = 65/15/20`.

## Migration Commands

```bash
cd apps/backend
alembic upgrade head
alembic revision --autogenerate -m "message"
```
