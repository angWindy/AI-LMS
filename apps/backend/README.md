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
LLM_MODEL=gemini-3.1-flash-lite-preview
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
- Endpoint: `POST /api/v1/chatbot/assignment/preload`
- Endpoint: `POST /api/v1/chatbot/assignment/ask`
- Endpoint: `GET /api/v1/chatbot/conversations`
- Endpoint: `GET /api/v1/chatbot/conversations/{conversation_id}/messages`
- Yêu cầu đăng nhập (Bearer token)
- Google provider dùng SDK chính thức `google-genai`
- Thiết kế theo provider abstraction để sau này có thể mở rộng sang vLLM/OpenAI và tích hợp RAG.
- Hỗ trợ `conversation_id` để tiếp tục hội thoại theo từng user.
- Hỗ trợ `teaching_images` (base64 + mime_type) cho chatbot phòng học video.
- Response trả về `context.image_contexts` để hiển thị thông tin ảnh đã dùng trong lượt chat.

### Chatbot phòng học video

Luồng này dùng cho trang học video online:

- Backend tự ghép `course_id` / `lesson_id` vào prompt và context.
- Khi request có `course_id` / `lesson_id`, backend tự truy xuất RAG theo lesson trước, course sau.
- Nếu lesson có tài liệu PDF đã index: dùng `PRIMARY_LESSON_CONTEXT` làm context chính.
- Nếu course có tài liệu cấp course: dùng `SUPPORTING_COURSE_CONTEXT` làm context phụ.
- Nếu lesson chưa có tài liệu: course-level context được đánh dấu `PRIMARY_COURSE_CONTEXT`.
- System prompt luôn có tên khóa học, tên bài học/phòng học và vai trò trợ giảng.

### Chatbot hỗ trợ làm bài tập

Luồng này dùng cho trang làm bài của học sinh:

- Frontend gửi `assignment_id` và câu hỏi hiện tại.
- Backend preload và cache context bài tập khi học sinh vào trang.
- Mỗi lượt hỏi chỉ dùng dữ liệu bài tập đã lọc: tên khóa học, tên bài học, số thứ tự câu hỏi, nội dung câu hỏi, 4 lựa chọn.
- Backend không gửi `is_correct`, `explanation`, hay prompt LMS chung vào LLM.
- Phiên làm việc được khóa theo assignment để tránh trộn lịch sử giữa các bài khác nhau.

### RAG trong phòng học

Request mẫu:

```json
{
  "question": "Giải thích ngắn gọn nội dung chính của buổi học này",
  "course_id": "<course-uuid>",
  "lesson_id": "<lesson-uuid>"
}
```

Kiểm tra nhanh:

```bash
python -m llm.rag.test_chatbot_classroom_rag
python -m llm.rag.test_lms_integration
```
