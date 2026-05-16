# Question Bank

Question Bank stores reusable multiple-choice questions for courses and lessons.

## Access

- Admin: can manage all course question banks.
- Instructor: can manage question banks for courses they teach.
- Learner: cannot manage Question Bank content.

## Data Model

`question_bank_questions`:

- `course_id`
- `lesson_id`
- `question_text`
- `difficulty`: `easy`, `medium`, `hard`
- `purpose_type`: `practice`, `shared`, `assessment`
- `order_index`

`question_bank_options`:

- `question_id`
- `option_text`
- `is_correct`
- `order_index`

Each question must have exactly four options and exactly one correct option.

## Manual Creation

Manual questions accept explicit `difficulty` and `purpose_type`.

```json
{
  "course_id": "uuid",
  "lesson_id": "uuid",
  "question_text": "What is supervised learning?",
  "difficulty": "easy",
  "purpose_type": "practice",
  "options": [
    { "option_text": "Learning from labeled data", "is_correct": true },
    { "option_text": "Learning without any data", "is_correct": false },
    { "option_text": "Only memorizing answers", "is_correct": false },
    { "option_text": "Drawing charts manually", "is_correct": false }
  ]
}
```

## AI Generation

Endpoint:

```text
POST /api/v1/question-bank/generate
```

Payload:

```json
{
  "course_id": "uuid",
  "lesson_id": "uuid",
  "question_count": 10
}
```

The frontend only asks for lesson and count. Difficulty and purpose are generated or assigned by backend logic.

## Difficulty Rules

The LLM prompt is in English and asks for Vietnamese question content.

Difficulty definitions:

- `easy`: basic knowledge and recall; direct concepts, definitions, or facts; little reasoning.
- `medium`: understanding and application; comparison, explanation, or short reasoning; not answerable by recall alone.
- `hard`: analysis and deeper reasoning; combines concepts or solves a problem; plausible distractors.

Distribution per generated set:

- `easy`: 40%
- `medium`: 40%
- `hard`: 20%

The backend validates the final JSON distribution before saving.

## Purpose Rules

After valid JSON is parsed, backend assigns `purpose_type` randomly inside each difficulty group:

- `practice`: 65%
- `shared`: 15%
- `assessment`: 20%

This keeps the LLM prompt focused on question quality and keeps purpose allocation deterministic in shape but random in assignment.

## Main Files

- Prompt: `llm/prompts/assignment_generator.py`
- Workflow: `llm/workflows/assignment_generator.py`
- Service: `apps/backend/app/services/assignment_generator_service.py`
- API: `apps/backend/app/api/v1/question_bank.py`
- Schemas: `apps/backend/app/schemas/question_bank.py`
- UI: `apps/frontend/src/app/(main)/question-bank/page.tsx`

## Tests

```bash
python -m pytest -q tests/test_question_generation_metadata.py
```

## Known Gaps

- No approval queue for generated questions.
- No bulk import/export.
- No duplicate detection.
- Assignments still copy question content instead of referencing Question Bank records.
- No dedicated assessment module yet.
