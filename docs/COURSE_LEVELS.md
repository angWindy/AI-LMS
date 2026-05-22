# Course Levels

Every course must declare one academic learner level. The level is stored on
`courses.level`, exposed through the Course API, shown in the frontend, and
passed into every LMS LLM prompt.

## Supported Values

| API value | Label |
| --- | --- |
| `elementary` | Tiểu học |
| `middle_school` | Trung học cơ sở |
| `high_school` | Trung học phổ thông |
| `higher_education` | Đại học và sau đại học |

`POST /api/v1/courses` requires `level`. `PUT /api/v1/courses/{course_id}`
accepts `level` when changing it. `GET /api/v1/courses?level=...` filters
published courses by the same values.

Example create payload:

```json
{
  "title": "Khoa học tự nhiên 6",
  "description": "Các chủ đề nền tảng về vật chất và năng lượng.",
  "category": "science",
  "level": "middle_school",
  "language": "vi"
}
```

## Data Migration

Migration `20260519_1200_8b1c9f2d3a4e_course_levels.py` normalizes existing
course rows, maps known Vietnamese/English aliases, fills unknown or old
difficulty-style values with `higher_education`, and changes `courses.level` to
`NOT NULL` with default `higher_education`.

The old values `beginner`, `intermediate`, and `advanced` described difficulty,
not academic stage, so they are treated as unknown during migration.

## LLM Adaptation

All LMS LLM services receive level guidance:

- General chatbot: adapts explanations, analogies, examples, and practice
  suggestions to the course level.
- Assignment tutor: adapts hints and scaffolding while still refusing to reveal
  final answers.
- Assignment generator: adapts question wording, distractors, examples, and
  reasoning depth.
- Assignment feedback: adapts feedback vocabulary, explanation depth, and next
  steps without changing grading correctness.

The shared prompt helper is `llm/prompts/learning_level.py`.
