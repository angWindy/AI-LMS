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