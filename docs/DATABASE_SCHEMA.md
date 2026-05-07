# Database Schema Notes

## Question Bank

The question bank stores reusable questions for courses and lessons.

Tables:

- `question_bank_questions`
- `question_bank_options`

Question metadata:

- `difficulty`: `easy`, `medium`, `hard`; default `easy`.
- `purpose_type`: `practice`, `assessment`, `shared`; default `shared`.

Existing `assignment_questions` also includes `difficulty` and `purpose_type` for compatibility with current assignment data.

Follow-up work is tracked in [QUESTION_BANK.md](QUESTION_BANK.md). The important pending decision is how assignments and future assessments should reuse or snapshot question bank records.
