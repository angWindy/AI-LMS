Folder thể hiện các chức năng của Backend (FastAPI).

Cấu trúc backend hiện tại:

apps/backend
├── app
│   ├── main.py
│   ├── api/v1/          # Routers theo nhóm API
│   ├── core/            # Config, security, dependencies
│   ├── db/              # Session, base, migrations
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── utils/           # Helper utilities
├── scripts/             # Smoke tests / utilities
├── storage/             # Uploaded assets
└── requirements.txt

Nguyên tắc tổ chức:

- Chia theo layer rõ ràng (API, service, data model, schema).
- Tránh giữ các placeholder/legacy file rỗng gây nhiễu.
- Ưu tiên import qua namespace `app.*` để nhất quán.

## Chatbot smoke test (Google AI Studio)

1. Cập nhật biến môi trường trong `.env` ở root project:

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_THINKING_LEVEL=low
GOOGLE_AI_API_KEY=your_google_ai_studio_key
```

2. Chạy test script từ thư mục `apps/backend`:

```bash
python scripts/test_google_ai_studio.py --question "Hay tra loi ngan gon: thu do Viet Nam la gi?"
```

3. Nếu thành công, terminal sẽ in:
- `[OK] Request success`
- Provider/model đang dùng
- Câu trả lời từ Gemini

## API chatbot

- Endpoint: `POST /api/v1/chatbot/ask`
- Endpoint: `GET /api/v1/chatbot/conversations`
- Endpoint: `GET /api/v1/chatbot/conversations/{conversation_id}/messages`
- Yêu cầu đăng nhập (Bearer token)
- Google provider dùng SDK chính thức `google-genai`
- Thiết kế theo provider abstraction để sau này có thể mở rộng sang vLLM/OpenAI và tích hợp RAG.
- Hỗ trợ `conversation_id` để tiếp tục hội thoại theo từng user (mỗi học sinh một thread).
- Hỗ trợ `teaching_images` (base64 + mime_type) để gửi ảnh màn hình bài giảng trước khi LLM trả lời.
- Response trả về `context.image_contexts` để hiển thị thông tin ảnh đã dùng trong lượt chat.