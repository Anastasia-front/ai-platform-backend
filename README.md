# AI Workflow Automation Platform

A lightweight FastAPI-based AI workflow automation platform for managing users, projects, chats, documents, workflows, and agent runs.

## Project structure

```
app/
├── api/
│ ├── routes/
│ │ ├── auth.py
│ │ ├── projects.py
│ │ ├── chats.py
│ │ ├── messages.py
│ │ ├── documents.py
│ │ └── workflows.py
│ └── deps.py
│
├── core/
│ ├── config.py
│ ├── security.py
│ └── database.py
│
├── models/
│ ├── user.py
│ ├── project.py
│ ├── chat.py
│ ├── message.py
│ ├── document.py
│ └── workflow.py
│
├── schemas/
│ ├── auth.py
│ ├── project.py
│ ├── chat.py
│ ├── message.py
│ ├── document.py
│ └── workflow.py
│
├── services/
│ ├── auth_service.py
│ ├── ai_service.py
│ ├── chat_service.py
│ ├── document_service.py
│ └── workflow_service.py
│
├── repositories/
│ ├── project_repository.py
│ ├── chat_repository.py
│ └── document_repository.py
│
└── main.py
```

## Setup

1. Create and activate the virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

## Notes

- The repository now includes a `.gitignore` file to exclude local environment, build artifacts, editor files, and sensitive config files.
- If you use environment variables, keep them in `.env` files or other local files that are not checked into source control.

Application security layer
config.py → settings
database.py → engine + session + Base + get_db
models/ → Base import
services/ → db dependency
api/ → get_db dependency
