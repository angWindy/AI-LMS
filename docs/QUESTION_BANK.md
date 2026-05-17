# Question Bank

Reusable multiple-choice questions for courses and lessons.

## Access

- Admin: all courses.
- Instructor: owned courses.
- Learner: no management access.

## API

```text
GET    /api/v1/question-bank/courses
GET    /api/v1/question-bank/questions
POST   /api/v1/question-bank/questions
POST   /api/v1/question-bank/generate
PUT    /api/v1/question-bank/questions/{question_id}
DELETE /api/v1/question-bank/questions/{question_id}
```

Filters: `course_id`, `lesson_id`, `difficulty`, `purpose_type`.

## Data

`question_bank_questions` stores course, optional lesson, question text,
`difficulty`, `purpose_type`, and `order_index`.

`question_bank_options` stores four options with exactly one correct answer.

Values:

```text
difficulty: easy, medium, hard
purpose_type: practice, shared, assessment
```

## AI Generation

```json
{ "course_id": "uuid", "lesson_id": "uuid", "question_count": 10 }
```

Flow:

1. Backend builds course/lesson/material context.
2. LLM returns Vietnamese questions with difficulty metadata.
3. Backend validates `easy/medium/hard = 40/40/20`.
4. Backend assigns purpose inside each difficulty group:
   `practice/shared/assessment = 65/15/20`.
5. Questions are saved to the bank.

Purpose usage:

- `practice`: practice assignments.
- `assessment`: tests.
- `shared`: both.

Existing assignments copy question content at creation time; later bank edits do
not change them.

## Main Files

- API: `apps/backend/app/api/v1/question_bank.py`
- Models: `apps/backend/app/models/question_bank.py`
- Schemas: `apps/backend/app/schemas/question_bank.py`
- Service: `apps/backend/app/services/assignment_generator_service.py`
- Prompt/workflow: `llm/prompts/assignment_generator.py`,
  `llm/workflows/assignment_generator.py`
- UI: `apps/frontend/src/app/(main)/question-bank/page.tsx`

## Test

```bash
python -m pytest -q tests/test_question_generation_metadata.py
```

## Gaps

No approval queue, bulk import/export, duplicate detection, or live assignment
references to bank rows.
