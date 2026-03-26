Cấu trúc frontend (Next.js)
apps/web
│
├── app                 # routes
│   ├── dashboard
│   ├── course
│   └── login
│
├── components          # UI components
│
├── features
│   ├── auth
│   ├── course
│   ├── assignment
│   └── ai-assistant
│
├── lib
│   ├── api-client.ts
│   └── utils.ts
│
├── hooks
├── styles
└── public

Nguyên tắc:

UI → components

logic theo module → features

API call → lib