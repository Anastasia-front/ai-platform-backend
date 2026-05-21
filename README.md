# AI Workflow Automation Platform

A lightweight FastAPI-based AI workflow automation platform for managing users, projects, chats, documents, workflows, and agent runs.

## Project structure

```text
app/
├── api/
│   ├── deps.py
│   └── routes/
│       ├── auth.py
│       ├── projects.py
│       ├── chats.py
│       ├── messages.py
│       ├── documents.py
│       └── workflows.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── database.py
├── models/
│   ├── user.py
│   ├── project.py
│   ├── chat.py
│   ├── message.py
│   ├── document.py
│   └── workflow.py
├── schemas/
│   ├── auth.py
│   ├── project.py
│   ├── chat.py
│   ├── message.py
│   ├── document.py
│   └── workflow.py
├── services/
│   ├── auth_service.py
│   ├── ai_service.py
│   ├── chat_service.py
│   ├── document_service.py
│   └── workflow_service.py
├── repositories/
│   ├── project_repository.py
│   ├── chat_repository.py
│   └── document_repository.py
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

- A `.gitignore` file is included to exclude local environment files, build artifacts, editor files, and sensitive configuration.
- Keep environment variables in a local `.env` file or another file that is not checked into source control.

### Application security layer

- `config.py` → settings
- `database.py` → engine + session + Base + `get_db`
- `models/` → Base import
- `services/` → DB dependency
- `api/` → `get_db` dependency

---

## Commands & Workflow

### 1. Generate JWT secret key

Generate a secure secret for authentication:

```bash
python3 -c "import secrets; print(secrets.token_hex(64))"
```

Copy the output into your `.env` file:

```text
SECRET_KEY=your_generated_secret_here
```

**Best practice (production systems)**

```
generate secret once
store in:
AWS Secrets Manager / GCP Secret Manager / Vault
never in .env in production
```

### 2. Create environment file

```bash
cp .env.example .env
```

Then ensure `.env` contains:

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_platform
SECRET_KEY=your_generated_secret_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Verify environment setup

```bash
python3 -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### 4. Docker (Database)

Start infrastructure:

```bash
docker compose up -d
```

Stop infrastructure:

```bash
docker compose down
```

Stop and reset database (DELETE ALL DATA):

```bash
docker compose down -v
docker compose up -d
```

Check running containers:

```bash
docker ps
```

### 5. Database (Postgres)

Open Postgres CLI:

```bash
docker exec -it ai-platform-postgres psql -U postgres
```

Inside psql:

```sql
\l      -- list databases
\c ai_platform      -- connect to DB
\dt      -- list tables
```

### 6. Database migrations (Alembic)

Create a new migration:

```bash
alembic revision --autogenerate -m "message here"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback one migration:

```bash
alembic downgrade -1
```

Check migration history:

```bash
alembic history
```

### 7. Development server (FastAPI)

Run the API server:

```bash
uvicorn app.main:app --reload
```

Default API URL:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

### 8. Auth testing

Register user:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

Access protected route:

```bash
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Code quality / debugging

Run a Python file:

```bash
python3 file.py
```

Check imports / environment issues:

```bash
python3 -c "import app; print('OK')"
```

Check installed packages:

```bash
pip list
```

### 10. Project reset (full clean restart)

⚠️ Deletes DB and rebuilds everything

```bash
docker compose down -v
docker compose up -d
alembic upgrade head
```

### 11. Quick health check

```bash
curl http://127.0.0.1:8000/docs
```

or

```bash
curl http://127.0.0.1:8000/health
```

### Recommended workflow

Daily development loop:

```bash
docker compose up -d
source venv/bin/activate
uvicorn app.main:app --reload
```

When model changes:

```bash
alembic revision --autogenerate -m "update"
alembic upgrade head
```
