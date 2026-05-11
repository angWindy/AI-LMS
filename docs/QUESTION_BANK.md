# Question Bank

## Scope

Question Bank is the reusable question repository for courses and lessons.

- Admin can access questions for all courses.
- Instructor can access only questions for courses they teach.
- Questions can be filtered by course and by lesson, or shown across all lessons in a course.
- LLM question generation now belongs to Question Bank UI instead of Lesson Studio assignment creation.
- Generated questions reuse the existing assignment question generation workflow, then save the output into reusable bank tables.
- The frontend request timeout for AI generation is 30 minutes.

Learners do not manage Question Bank content directly. Question Bank is an authoring feature for Admin and Instructor roles.

## User Flow

### Open Question Bank

Route:

```text
/question-bank
```

The page is available from the main navigation for Admin and Instructor users.

### Filter Questions

Users can filter by:

- Course
- Lesson inside the selected course

When no course is selected, Admin can see questions across all courses. Instructor users only see questions from courses they teach.

### Create a Question Manually

Manual questions require:

- Course
- Optional lesson
- Question text
- Difficulty
- Purpose type
- Exactly 4 answer options
- Exactly 1 correct answer
- Optional explanation

### Generate Questions with AI

AI generation requires:

- Course
- Lesson
- Question count from 1 to 100
- Difficulty
- Purpose type

The backend builds course and lesson context, calls the assignment generator workflow, and saves each generated question into Question Bank.

### Edit and Delete

Admin and course instructors can:

- Edit question metadata and text.
- Replace the answer option set.
- Delete reusable questions.

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

## Difficulty and Purpose

Difficulty values:

- `easy`
- `medium`
- `hard`

Purpose values:

- `practice`: for practice and self-check questions.
- `assessment`: for future test/exam use.
- `shared`: default reusable question pool.

## Backend Components

### API Router

```text
apps/backend/app/api/v1/question_bank.py
```

Registered under:

```text
/api/v1/question-bank
```

### Schemas

```text
apps/backend/app/schemas/question_bank.py
```

Important schemas:

- `QuestionBankCourseResponse`
- `QuestionBankQuestionCreate`
- `QuestionBankQuestionUpdate`
- `QuestionBankGenerateRequest`
- `QuestionBankQuestionResponse`

### Models

```text
apps/backend/app/models/question_bank.py
```

Models:

- `QuestionBankQuestion`
- `QuestionBankOption`

### AI Generation Service

Question Bank generation currently uses:

```text
apps/backend/app/services/assignment_generator_service.py
```

This keeps generated questions consistent with the existing assignment generator prompt and validation rules.

## API

All endpoints require an Admin or Instructor token.

### List Courses

```http
GET /api/v1/question-bank/courses
```

Returns courses visible to the current user.

Visibility:

- Admin sees all courses.
- Instructor sees courses they teach.

### List Questions

```http
GET /api/v1/question-bank/questions?course_id={course_id}&lesson_id={lesson_id}
```

Query parameters:

| Parameter | Required | Purpose |
| --- | --- | --- |
| `course_id` | No | Filter by course |
| `lesson_id` | No | Filter by lesson |

If `lesson_id` is provided without `course_id`, the API resolves the lesson course and still enforces access control.

### Create Question

```http
POST /api/v1/question-bank/questions
```

Request body:

```json
{
  "course_id": "00000000-0000-0000-0000-000000000000",
  "lesson_id": "00000000-0000-0000-0000-000000000000",
  "question_text": "Khái niệm chính của bài học là gì?",
  "explanation": "Giải thích ngắn gọn vì sao đáp án đúng.",
  "difficulty": "easy",
  "purpose_type": "shared",
  "options": [
    {
      "option_text": "Đáp án A",
      "is_correct": true
    },
    {
      "option_text": "Đáp án B",
      "is_correct": false
    },
    {
      "option_text": "Đáp án C",
      "is_correct": false
    },
    {
      "option_text": "Đáp án D",
      "is_correct": false
    }
  ]
}
```

Validation:

- Exactly 4 options.
- Exactly 1 correct option.
- Course must be managed by the current user.
- Lesson, when provided, must belong to the course.

### Generate Questions

```http
POST /api/v1/question-bank/generate
```

Request body:

```json
{
  "course_id": "00000000-0000-0000-0000-000000000000",
  "lesson_id": "00000000-0000-0000-0000-000000000000",
  "question_count": 10,
  "difficulty": "medium",
  "purpose_type": "practice"
}
```

Rules:

- `question_count` must be between 1 and 100.
- The lesson must belong to the course.
- The current user must be Admin or the course instructor.
- Generated questions are persisted immediately as reusable bank questions.

### Update Question

```http
PUT /api/v1/question-bank/questions/{question_id}
```

The update payload uses the same core fields as create. If `options` is provided, the old option set is replaced.

### Delete Question

```http
DELETE /api/v1/question-bank/questions/{question_id}
```

Deletes one reusable question and its options.

## Frontend Components

### Page

```text
apps/frontend/src/app/(main)/question-bank/page.tsx
```

Route:

```text
/question-bank
```

Main behavior:

- Load courses visible to the current Admin/Instructor.
- Filter questions by course and lesson.
- Create questions manually.
- Generate questions with AI.
- Edit and delete existing questions.

### API Client

```text
apps/frontend/src/lib/api/question-bank.ts
```

Client methods:

- `listCourses()`
- `listQuestions(params)`
- `createQuestion(data)`
- `generateQuestions(data)`
- `updateQuestion(questionId, data)`
- `deleteQuestion(questionId)`

The AI generation client uses a 30-minute timeout:

```ts
timeout: 30 * 60 * 1000
```

## Operational Notes

AI generation can take several minutes. The browser timeout is 30 minutes, and production reverse proxy timeouts should be aligned with that value.

For Nginx deployments:

```nginx
proxy_connect_timeout 1800s;
proxy_send_timeout 1800s;
proxy_read_timeout 1800s;
send_timeout 1800s;
```

If the backend logs a successful generation but the frontend reports failure, check proxy timeout logs first.

## Testing

Backend tests:

```bash
rtk python -m pytest -q
```

Frontend checks:

```bash
cd apps/frontend
rtk npx tsc --noEmit
rtk npm run lint
```

## Known Limitations

- Question Bank stores reusable questions, but assignments still keep their own copied question records.
- There is no UI flow yet to select existing Question Bank questions when creating an assignment.
- `purpose_type=assessment` is stored, but there is no separate assessment/test module using it yet.
- There is no bulk import/export for questions.
- There is no duplicate detection across generated or manually created questions.
- There is no question tagging system beyond course, lesson, difficulty, and purpose type.
- There is no version history for edited questions.
- There is no review/approval workflow for AI-generated questions before they enter the bank; generated questions are saved immediately.
- There is no background job progress tracking for long-running AI question generation.
- There is no retry/resume mechanism if the browser request is interrupted while generation continues on the backend.
- There is no automatic quality grading beyond option count and single-correct-answer validation.
- Question options are currently fixed to exactly 4 options.

## Not Done Yet

The following items are intentionally not implemented in the current scope:

- Reusing bank questions directly inside assignment creation.
- Building dedicated tests/exams from bank questions.
- Snapshot policy for attempts that use reusable bank questions.
- Bulk CSV/Excel import and export.
- Question deduplication and similarity search.
- Tagging, topic hierarchy, and learning objective mapping.
- Question analytics such as correctness rate or discrimination index.
- Background job queue and progress API for AI generation.
- Manual approval queue for generated questions.
- Renaming `AssignmentGeneratorService` to a neutral shared question-generation service.

## Follow-Up Work

The current implementation intentionally introduces the Question Bank first and keeps existing assignment behavior stable.

Required follow-up:

- Build assessment/test entities and use `purpose_type=assessment` when selecting questions for tests.
- Refactor assignment creation so assignments can pick/reuse questions from `question_bank_questions` instead of duplicating question content in `assignment_questions`.
- Decide whether assignment/test attempts should snapshot bank questions at publish time or reference live bank questions.
- Add bulk import/export and deduplication rules for shared questions.
- Rename the backend `AssignmentGeneratorService` to a neutral question generation service once assignment and assessment generation share it.
