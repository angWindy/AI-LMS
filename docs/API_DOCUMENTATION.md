# API Documentation

FastAPI serves interactive OpenAPI docs at:

- Local: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Base prefix: `/api/v1`.

## Authentication

Most routes require a JWT bearer token.

Common auth routes:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`

## Courses And Lessons

- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `PUT /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `GET /lessons`
- `POST /lessons`
- `GET /lessons/{lesson_id}`
- `PUT /lessons/{lesson_id}`
- `DELETE /lessons/{lesson_id}`

Admin can manage all courses. Instructors can manage their own courses. Learners can access enrolled or published content according to route rules.

## Assignments

- `POST /assignments?course_id={course_id}`
- `POST /assignments/generate-draft?course_id={course_id}`
- `GET /assignments?course_id={course_id}`
- `GET /assignments/{assignment_id}`
- `PUT /assignments/{assignment_id}`
- `DELETE /assignments/{assignment_id}`
- `POST /assignments/{assignment_id}/publish`

AI-generated assignment drafts use the shared question generation workflow.

## Question Bank

- `GET /question-bank/courses`
- `GET /question-bank/questions`
- `POST /question-bank/questions`
- `POST /question-bank/generate`
- `PUT /question-bank/questions/{question_id}`
- `DELETE /question-bank/questions/{question_id}`

Generate payload:

```json
{
  "course_id": "uuid",
  "lesson_id": "uuid",
  "question_count": 10
}
```

Generation rules:

- One LLM prompt creates the full set.
- Each generated question must include `difficulty`.
- Backend validates `easy/medium/hard = 40/40/20`.
- Backend assigns `purpose_type` after generation as `practice/shared/assessment = 65/15/20` within each difficulty group.

## Slides

- `POST /slides/generate-draft?course_id={course_id}`
- `GET /slides?course_id={course_id}`
- `GET /slides/{slide_deck_id}`
- `POST /slides/{slide_deck_id}/publish`
- `DELETE /slides/{slide_deck_id}`

Slide generation creates structured slide JSON and a rendered PDF.

## RAG And Chatbot

- `POST /rag/ingest`
- `GET /rag/status`
- `POST /chatbot`

RAG routes depend on configured database, files, and Gemini API access.

## Error Shape

FastAPI errors generally return:

```json
{
  "detail": "message"
}
```
