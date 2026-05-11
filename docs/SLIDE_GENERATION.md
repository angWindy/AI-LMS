# Slide Generation

## Scope

Slide Generation creates AI-assisted lecture slide decks for a lesson.

- Instructor and Admin can generate, preview, publish, and delete slide decks.
- Learner can only access published slide decks for courses they are enrolled in.
- The feature creates lesson-level lecture material, similar in level to live session and assignment content.
- The output includes structured slide JSON and a generated PDF file for display in the lesson.

This feature does not handle custom themes, design editing, or PDF layout customization. The current renderer produces a simple lecture-ready PDF from the generated slide JSON.

## User Flow

### Instructor/Admin

1. Open a course lesson in Lesson Studio:
   - `/courses/[slug]/lessons/[lessonId]/studio`
2. In the `Slide bài giảng` section, choose `Tạo slide`.
3. Enter:
   - `title` (optional)
   - `slide_count` from 1 to 50
4. Submit the request.
5. The backend generates:
   - Intermediate Representation JSON (IR)
   - Slides JSON
   - PDF file
6. Review the slide preview and PDF.
7. Publish the deck when it is ready for learners.

### Learner

1. Open the lesson video room:
   - `/lessons/[id]/video`
2. Published slide PDFs appear in the quick navigation area.
3. Learners can open the PDF directly from the lesson.

## Generation Pipeline

Slide generation intentionally uses a two-step LLM workflow:

```text
course_context + lesson_context
        |
        v
Document IR JSON
        |
        v
Slides JSON
        |
        v
PDF file
```

The LLM does not generate final slides directly from course and lesson context. The IR is the source of truth for the second step.

### Step 1: Context to IR

Prompt helper:

```python
build_document_to_ir_prompt(course_context: str, lesson_context: str) -> str
```

Location:

```text
llm/prompts/slide_generator.py
```

The prompt asks the model to return only valid JSON in Vietnamese. It prioritizes the provided course and lesson context, while allowing general teaching/domain knowledge for explanations and examples when useful. It must not invent unsupported course-specific facts, citations, statistics, or claims.

Current IR shape:

```json
{
  "document_title": "...",
  "domain": "...",
  "summary": "...",
  "learning_objectives": ["..."],
  "key_concepts": [
    {
      "name": "...",
      "definition": "...",
      "importance": "...",
      "examples": ["..."]
    }
  ],
  "main_sections": [
    {
      "id": 1,
      "heading": "...",
      "summary": "...",
      "key_points": ["..."],
      "teaching_suggestions": ["..."],
      "possible_visuals": ["..."]
    }
  ]
}
```

### Step 2: IR to Slides

Prompt helper:

```python
build_ir_to_slides_prompt(ir_json: str, slide_count: int) -> str
```

The prompt asks the model to generate exactly `slide_count` slides. The IR is the source of truth, and each slide references source section ids from `main_sections`.

Output shape:

```json
{
  "document_type": "slides",
  "title": "...",
  "slides": [
    {
      "id": 1,
      "slide_type": "title",
      "title": "...",
      "content": ["..."],
      "speaker_notes": "...",
      "source_sections": [1]
    }
  ]
}
```

Allowed `slide_type` values:

- `title`
- `objectives`
- `concept`
- `comparison`
- `example`
- `summary`
- `quiz`

## Backend Components

### Prompt Helpers

```text
llm/prompts/slide_generator.py
```

Exports:

- `build_document_to_ir_prompt`
- `build_ir_to_slides_prompt`

### LLM Workflow

```text
llm/workflows/slide_generator.py
```

Main functions:

- `generate_document_ir(course_context, lesson_context)`
- `generate_slides_from_ir(ir_json, slide_count)`
- `generate_slides_from_context(course_context, lesson_context, slide_count)`

`generate_slides_from_context` always runs the two-step pipeline:

```text
context -> IR JSON -> slides JSON
```

The workflow timeout is configured for long-running AI generation:

```text
1800 seconds / 30 minutes
```

### Application Service

```text
apps/backend/app/services/slide_generator_service.py
```

Responsibilities:

- Build course and lesson context.
- Call the LLM workflow.
- Validate IR and slide JSON structure.
- Generate a PDF file from the slide JSON.
- Provide a mock generation path when the LLM provider is configured as mock.

### API Router

```text
apps/backend/app/api/v1/slides.py
```

Registered under:

```text
/api/v1/slides
```

### Database Model

```text
apps/backend/app/models/slide_deck.py
```

Table:

```text
slide_decks
```

Key fields:

| Column | Purpose |
| --- | --- |
| `id` | Slide deck id |
| `course_id` | Owning course |
| `lesson_id` | Lesson that owns the deck |
| `title` | Display title |
| `slide_count` | Requested number of slides |
| `ir_json` | Intermediate Representation JSON |
| `slides_json` | Generated slides JSON |
| `pdf_url` | Stored PDF URL |
| `pdf_file_size` | PDF size in bytes |
| `pdf_mime_type` | PDF MIME type |
| `provider`, `model` | LLM provider metadata |
| `is_published` | Learner visibility flag |
| `order_index` | Course-level ordering |
| `created_at`, `updated_at` | Audit timestamps |

## API

All endpoints require authentication.

### Generate Draft

```http
POST /api/v1/slides/generate-draft?course_id={course_id}
```

Roles:

- Admin
- Course instructor

Request body:

```json
{
  "lesson_id": "00000000-0000-0000-0000-000000000000",
  "slide_count": 12,
  "title": "Bài giảng: Tổng quan hệ thống"
}
```

Rules:

- `slide_count` must be between 1 and 50.
- The lesson must belong to the selected course.
- The generated deck is created as unpublished by default.

Success response: `201 Created`

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "course_id": "00000000-0000-0000-0000-000000000000",
  "lesson_id": "00000000-0000-0000-0000-000000000000",
  "title": "Bài giảng: Tổng quan hệ thống",
  "slide_count": 12,
  "ir_json": {},
  "slides_json": {},
  "pdf_url": "/storage/slides/lesson-id/deck-id.pdf",
  "pdf_file_size": 123456,
  "pdf_mime_type": "application/pdf",
  "provider": "gemini",
  "model": "gemini-...",
  "is_published": false,
  "order_index": 1,
  "created_at": "2026-05-11T00:00:00Z",
  "updated_at": "2026-05-11T00:00:00Z"
}
```

### List Slide Decks

```http
GET /api/v1/slides?course_id={course_id}&lesson_id={lesson_id}&include_unpublished=true
```

Query parameters:

| Parameter | Required | Purpose |
| --- | --- | --- |
| `course_id` | Yes | Course scope |
| `lesson_id` | No | Filter by lesson |
| `include_unpublished` | No | Owner/admin can include drafts |

Visibility:

- Instructor/Admin can see drafts when `include_unpublished=true`.
- Learner only sees published decks.

### Get One Slide Deck

```http
GET /api/v1/slides/{slide_deck_id}
```

Returns one deck if the current user has access.

### Publish Slide Deck

```http
POST /api/v1/slides/{slide_deck_id}/publish
```

Roles:

- Admin
- Course instructor

Sets `is_published=true`.

### Delete Slide Deck

```http
DELETE /api/v1/slides/{slide_deck_id}
```

Roles:

- Admin
- Course instructor

Deletes the database record and associated PDF file.

## Frontend Components

### Lesson Studio

Route:

```text
/courses/[slug]/lessons/[lessonId]/studio
```

Main behavior:

- Shows slide decks attached to the lesson.
- Opens a create dialog with title and slide count.
- Calls the 30-minute frontend request timeout for AI generation.
- Shows JSON slide preview and embedded PDF preview when `pdf_url` is available.
- Allows opening the PDF in a new tab.
- Allows deleting draft or generated decks.

### Lesson Video Room

Route:

```text
/lessons/[id]/video
```

Main behavior:

- Loads published slide decks for the lesson.
- Displays PDF links in quick navigation for learners and allowed users.

## Operational Notes

AI slide generation can take several minutes. The frontend request timeout and backend LLM timeout are set to 30 minutes. Production reverse proxies must also allow long-running requests; otherwise the backend can finish successfully while the browser sees a failed request.

For Nginx deployments, align proxy timeouts with the AI timeout:

```nginx
proxy_connect_timeout 1800s;
proxy_send_timeout 1800s;
proxy_read_timeout 1800s;
send_timeout 1800s;
```

## Testing

Relevant tests:

```bash
rtk python -m pytest -q tests/test_slide_generator_prompts.py tests/test_slide_pdf_render.py
```

Full backend test command:

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

- Slide generation is currently synchronous from the browser perspective.
- PDF rendering is intentionally simple and not theme-aware.
- There is no slide editor yet.
- There is no background job progress tracking yet.
- Duplicate slide deck detection is not enforced.
- There is no retry/resume mechanism if the browser request is interrupted after the backend has started generation.
- There is no partial result view while the LLM is still generating IR or slides.
- There is no per-slide image generation, chart rendering, or visual asset pipeline yet.
- There is no PowerPoint export.
- There is no learner-facing in-app slide viewer beyond opening or embedding the generated PDF.
- There is no version comparison between multiple generated decks for the same lesson.
- There is no automated content quality grading beyond JSON structure validation.
- Published slide decks are not automatically inserted into lesson order/navigation outside the current quick PDF links.

## Not Done Yet

The following items are intentionally not implemented in the current scope:

- Background job queue for long-running slide generation.
- Progress API or polling UI for slide generation status.
- Editable slide canvas or drag-and-drop slide builder.
- Theme selection, brand templates, or custom PDF layout controls.
- Export to `.pptx`, image sequences, or HTML slides.
- Automatic regeneration of only one slide inside an existing deck.
- Automatic deduplication against previous slide decks.
- Human approval workflow beyond the current publish/unpublish flag.
