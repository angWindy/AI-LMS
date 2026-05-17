# Assignments And Tests

Assignments are exercises attached to a course and optionally a lesson.

## Types

- `practice`: manual, AI-generated, or assembled from `practice/shared` Question
  Bank items.
- `test`: course-level, optionally scoped to selected lessons, assembled from
  `assessment/shared` Question Bank items.

Question types:

- `multiple_choice`: exactly four options and one correct option.
- `essay`: requires `correct_answer_text`, no options.

## API

```text
POST   /api/v1/assignments?course_id={course_id}
POST   /api/v1/assignments/generate-draft?course_id={course_id}
POST   /api/v1/assignments/generate-from-bank?course_id={course_id}
POST   /api/v1/assignments/generate-test?course_id={course_id}
GET    /api/v1/assignments?course_id={course_id}&include_unpublished=false
GET    /api/v1/assignments/{assignment_id}
GET    /api/v1/assignments/{assignment_id}/submission
POST   /api/v1/assignments/{assignment_id}/submit
DELETE /api/v1/assignments/{assignment_id}/submission
PUT    /api/v1/assignments/{assignment_id}
DELETE /api/v1/assignments/{assignment_id}
POST   /api/v1/assignments/{assignment_id}/publish
```

Learners see only published assignments and never receive answer keys.

## Generation Rules

AI practice draft:

- Uses course and lesson context.
- Validates 40/40/20 difficulty distribution.
- Saves as unpublished `practice`.

Practice from bank:

- Selects `practice/shared`.
- Requires enough questions per difficulty bucket.

Test from bank:

- Selects `assessment/shared`.
- Optional lesson scope.
- Preserves 40/40/20.
- Converts about 50% medium and 70% hard selected questions to essay mode, with
  at least one essay when that bucket exists.

## Submission

Learners submit one answer per question. A submitted assignment cannot be
retaken until the learner deletes their submission.

Scoring:

- Multiple-choice: local 1/0 score.
- Essay: LLM feedback service returns score, explanation, and summary.
- Submission score is saved as a percentage.

## Main Files

- API: `apps/backend/app/api/v1/assignments.py`
- Models: `apps/backend/app/models/assignment.py`,
  `apps/backend/app/models/submission.py`
- Schemas: `apps/backend/app/schemas/assignment.py`
- Services: `apps/backend/app/services/assignment_generator_service.py`,
  `apps/backend/app/services/assignment_feedback_service.py`
- Frontend API: `apps/frontend/src/lib/api/assignments.ts`
- UI: `apps/frontend/src/app/(main)/lessons/[id]/assignment/page.tsx`,
  `apps/frontend/src/app/(main)/courses/[slug]/tests/[assignmentId]/page.tsx`

## Gaps

No manual grading UI, due dates, late penalties, or per-learner randomization.
