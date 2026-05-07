# Question Bank

## Scope

Question Bank is the reusable question repository for courses and lessons.

- Admin can access questions for all courses.
- Instructor can access only questions for courses they teach.
- Questions can be filtered by course and by lesson, or shown across all lessons in a course.
- LLM question generation now belongs to Question Bank UI instead of Lesson Studio assignment creation.

## Data Model

### `question_bank_questions`

Reusable question records.

| Column | Purpose |
| --- | --- |
| `id` | Question id |
| `course_id` | Owning course |
| `lesson_id` | Optional lesson scope |
| `question_text` | Question content |
| `explanation` | Optional answer explanation |
| `difficulty` | `easy`, `medium`, `hard`; default `easy` |
| `purpose_type` | `practice`, `assessment`, `shared`; default `shared` |
| `order_index` | Course-level display ordering |
| `created_at`, `updated_at` | Audit timestamps |

### `question_bank_options`

Multiple-choice options for bank questions.

| Column | Purpose |
| --- | --- |
| `id` | Option id |
| `question_id` | Parent question |
| `option_text` | Option content |
| `is_correct` | Correct answer marker |
| `order_index` | Option order |
| `created_at`, `updated_at` | Audit timestamps |

### Assignment Metadata

Existing `assignment_questions` now also has:

- `difficulty`, default `easy`
- `purpose_type`, default `shared`

These fields keep existing assignment data compatible with the new taxonomy.

## API

- `GET /api/v1/question-bank/courses`
- `GET /api/v1/question-bank/questions?course_id=...&lesson_id=...`
- `POST /api/v1/question-bank/questions`
- `POST /api/v1/question-bank/generate`
- `PUT /api/v1/question-bank/questions/{question_id}`
- `DELETE /api/v1/question-bank/questions/{question_id}`

## Follow-Up Work

The current implementation intentionally introduces the Question Bank first and keeps existing assignment behavior stable.

Required follow-up:

- Build assessment/test entities and use `purpose_type=assessment` when selecting questions for tests.
- Refactor assignment creation so assignments can pick/reuse questions from `question_bank_questions` instead of duplicating question content in `assignment_questions`.
- Decide whether assignment/test attempts should snapshot bank questions at publish time or reference live bank questions.
- Add bulk import/export and deduplication rules for shared questions.
- Rename the backend `AssignmentGeneratorService` to a neutral question generation service once assignment and assessment generation share it.
