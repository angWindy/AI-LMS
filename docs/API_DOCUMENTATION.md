# API Documentation

Base prefix: `/api/v1`.

Docs:

- Direct backend: `http://localhost:8000/docs`
- Nginx stack: `http://localhost/docs`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Auth

Bearer JWT is required for most routes.

Roles:

- `admin`: all users/content.
- `instructor`: owned courses/content.
- `learner`: published content, submissions, progress, chatbot.

Auth routes:

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
PUT  /auth/me
PUT  /auth/me/password
```

Login response:

```json
{ "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer" }
```

Errors usually return `{ "detail": "message" }`.

Pagination uses:

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0 }
```

## Users

Admin only:

```text
GET    /users?page=1&page_size=20&role=admin&is_active=true&search=name
POST   /users
GET    /users/{user_id}
PUT    /users/{user_id}
DELETE /users/{user_id}
POST   /users/{user_id}/activate
POST   /users/{user_id}/deactivate
POST   /users/{user_id}/verify
```

## Courses And Materials

```text
GET    /courses
POST   /courses
GET    /courses/{course_id}
GET    /courses/slug/{slug}
PUT    /courses/{course_id}
DELETE /courses/{course_id}
POST   /courses/{course_id}/publish
POST   /courses/{course_id}/archive
GET    /courses/{course_id}/lessons
GET    /courses/{course_id}/materials
POST   /courses/{course_id}/materials
DELETE /courses/materials/{material_id}
GET    /courses/my/teaching
```

`GET /courses` returns published courses. Filters: `status`, `category`,
`level`, `search`, `page`, `page_size`.

Course level values: `primary`, `lower_secondary`, `upper_secondary`,
`higher_ed`. `level` is required when creating or updating a course.

Material upload form fields: `title`, `description`, `type`, optional `file`,
optional `external_url`.

## Lessons

```text
POST   /lessons?course_id={course_id}
GET    /lessons/{lesson_id}
PUT    /lessons/{lesson_id}
DELETE /lessons/{lesson_id}
PATCH  /lessons/{lesson_id}/order
POST   /lessons/{lesson_id}/publish
GET    /lessons/{lesson_id}/materials
POST   /lessons/{lesson_id}/materials
DELETE /lessons/materials/{material_id}
POST   /lessons/{lesson_id}/progress
GET    /lessons/{lesson_id}/progress
```

Non-owners can read only published or preview lessons.

Progress payload:

```json
{ "watched_seconds": 300, "last_position": 300, "is_completed": false }
```

## Assignments And Tests

```text
POST   /assignments?course_id={course_id}
POST   /assignments/generate-draft?course_id={course_id}
POST   /assignments/generate-from-bank?course_id={course_id}
POST   /assignments/generate-test?course_id={course_id}
GET    /assignments?course_id={course_id}&include_unpublished=false
GET    /assignments/{assignment_id}
GET    /assignments/{assignment_id}/submission
POST   /assignments/{assignment_id}/submit
DELETE /assignments/{assignment_id}/submission
PUT    /assignments/{assignment_id}
DELETE /assignments/{assignment_id}
POST   /assignments/{assignment_id}/publish
```

Generation payloads:

```json
{ "lesson_id": "uuid", "question_count": 10, "title": "optional" }
```

```json
{ "lesson_ids": ["uuid"], "question_count": 20, "title": "optional" }
```

Learners do not receive answer keys. Submissions must include exactly one answer
per question:

```json
{ "answers": [{ "question_id": "uuid", "selected_option_id": "uuid" }] }
```

Essay answers use `answer_text`.

## Question Bank

```text
GET    /question-bank/courses
GET    /question-bank/questions
POST   /question-bank/questions
POST   /question-bank/generate
PUT    /question-bank/questions/{question_id}
DELETE /question-bank/questions/{question_id}
```

Filters: `course_id`, `lesson_id`, `difficulty`, `purpose_type`.

Generate:

```json
{ "course_id": "uuid", "lesson_id": "uuid", "question_count": 10 }
```

Generated difficulty distribution is `easy/medium/hard = 40/40/20`. Backend
assigns purpose distribution `practice/shared/assessment = 65/15/20` within
each difficulty group.

## Slides

```text
POST   /slides/generate-draft?course_id={course_id}
GET    /slides?course_id={course_id}&lesson_id={lesson_id}&include_unpublished=false
GET    /slides/{slide_deck_id}
POST   /slides/{slide_deck_id}/publish
DELETE /slides/{slide_deck_id}
```

Generate:

```json
{ "lesson_id": "uuid", "slide_count": 8, "title": "optional" }
```

## RAG

```text
POST   /rag/upload
POST   /rag/search
GET    /rag/documents
DELETE /rag/documents/{doc_id}
GET    /rag/stats
```

Search:

```json
{
  "query": "Explain the topic",
  "top_k": 5,
  "course_id": "uuid-or-null",
  "lesson_id": "uuid-or-null",
  "document_id": "optional"
}
```

Regular material uploads auto-index supported PDF/DOCX files.

## Chatbot

```text
GET  /chatbot/providers
POST /chatbot/ask
POST /chatbot/assignment/preload
POST /chatbot/assignment/ask
GET  /chatbot/conversations?limit=20
GET  /chatbot/conversations/{conversation_id}/messages?limit=100
```

General chatbot accepts `question`, optional `conversation_id`, `course_id`,
`lesson_id`, `history`, `context_docs`, `image_contexts`, `teaching_images`,
`temperature`, `max_output_tokens`, and `thinking_level`.

Assignment chatbot accepts `assignment_id`, `question`, optional
`conversation_id`, and `history`. It receives sanitized assignment context and
is prompted to give hints without revealing final answers.
