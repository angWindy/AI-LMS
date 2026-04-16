Folder thể hiện các chức năng của Backend ( FastAPI )

Cấu trúc backend (FastAPI)

Backend nên tổ chức theo modular architecture.

apps/backend
│
├── app
│   ├── main.py
│
│   ├── core
│   │   ├── config.py
│   │   └── security.py
│
│   ├── db
│   │   ├── session.py
│   │   └── base.py
│
│   ├── modules
│   │   ├── auth
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schema.py
│   │   │   └── model.py
│   │   │
│   │   ├── courses
│   │   ├── materials
│   │   └── assignments
│
│   └── utils
│
└── requirements.txt

Nguyên tắc:

chia theo feature/module

mỗi module có:

router

service

model

schema

Cách modular này giúp dự án dễ mở rộng và maintain hơn.

## Chatbot smoke test (Google AI Studio)

1. Cập nhật biến môi trường trong `.env` ở root project:

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=1.0
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
- Yêu cầu đăng nhập (Bearer token)
- Google provider dùng SDK chính thức `google-genai`
- Thiết kế theo provider abstraction để sau này có thể mở rộng sang vLLM/OpenAI và tích hợp RAG.