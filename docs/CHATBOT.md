# Chatbot

Two chatbot modes share the `llm` provider abstraction and persist history in
`ai_conversations` and `ai_messages`.

## API

```text
GET  /api/v1/chatbot/providers
POST /api/v1/chatbot/ask
POST /api/v1/chatbot/assignment/preload
POST /api/v1/chatbot/assignment/ask
GET  /api/v1/chatbot/conversations?limit=20
GET  /api/v1/chatbot/conversations/{conversation_id}/messages?limit=100
```

## General Chatbot

Uses any provided:

- course/lesson scope
- recent conversation history
- explicit text context
- automatic RAG context
- image contexts or image payloads

If the question directly refers to an image/screenshot, image mode is used and
RAG/text context is skipped for that turn. Otherwise provided images are ignored
and text/RAG context is used.

Prompts adapt tone, vocabulary, and depth to the course level.

## Assignment Tutor

Validates assignment access, builds sanitized assignment context without answer
keys, disables auto-RAG, and uses a prompt that gives hints without revealing
final answers.

Assignment tutor prompts also adapt to the course level.

## Main Files

- API/schema: `apps/backend/app/api/v1/chatbot.py`,
  `apps/backend/app/schemas/chatbot.py`
- Services: `apps/backend/app/services/chatbot_service.py`,
  `apps/backend/app/services/assignment_chatbot_service.py`
- Workflow/prompts: `llm/workflows/chatbot.py`, `llm/prompts/chatbot.py`,
  `llm/prompts/assignment_chatbot.py`
- Frontend: `apps/frontend/src/components/chat/ChatWindow.tsx`,
  `apps/frontend/src/components/chat/store.ts`,
  `apps/frontend/src/lib/api/chatbot.ts`

## Tests

```bash
python -m pytest -q tests/test_chatbot_context_selection.py
```

## Notes

- General chatbot frontend timeout: 4 minutes.
- Generation/assignment calls use longer 30-minute frontend timeouts.
- Gemini image input accepts PNG, JPEG, WEBP, GIF up to 10 MB per image.
