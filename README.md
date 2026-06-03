# AI Workflow Automation Platform

A lightweight FastAPI-based AI workflow automation platform for managing users, projects, chats, documents, workflows, and agent runs.

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
docker exec -it ai-platform-postgres psql -U postgres -d ai_platform
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

## Notes

- A `.gitignore` file is included to exclude local environment files, build artifacts, editor files, and sensitive configuration.
- Keep environment variables in a local `.env` file or another file that is not checked into source control.

### Application security layer

- `config.py` → settings
- `database.py` → engine + session + Base + `get_db`
- `models/` → Base import
- `services/` → DB dependency
- `api/` → `get_db` dependency

### Architecture domain feature layered structure:

```
            Route
              ↓
            Service
              ↓
            Model
              ↓
            DB / ORM
```

- Route:
  - HTTP concerns
  - status codes
  - auth dependencies

- Service:
  - business logic

- Model:
  - persistence

- Schema:
  - API contracts

### Chat and messages flow:

```
User
 → owns Project
 → creates Chat inside Project
 → sends Messages
 → gets chat history
```

### AI architecture layer

- route only handles HTTP
- service handles DB + orchestration
- AI service handles LLM provider

gemma2:2b - the model is actually a good choice at this stage because:

It’s lightweight (1.6 GB) → fast on local machines
It’s sufficient for:

- chat responses
- basic assistant behavior
- API wiring / architecture testing

Then move to:

- llama3
- mistral
- qwen2.5

### Chat Context (Memory Upgrade)

```
        user message
              ↓
        load chat history (DB)
              ↓
        send full context to Ollama
              ↓
        AI response
              ↓
        save both messages
```

## System Prompts + AI Context Architecture

### Core AI backend concepts:

- prompt engineering
- context injection
- AI orchestration
- conversational control
- instruction hierarchy

### Core idea of an automation platform instead of just chat.

```
      User Request
            ↓
      Workflow
            ↓
      Multiple AI Steps
            ↓
      Structured Output
```

Example workflows:

- blog generation
- research pipeline
- code review
- summarization
- SEO generation
- email automation

### Backend infrastructure for now:

```
      Auth Layer
            ↓
      Ownership Layer
            ↓
      Domain Layer
            ↓
      Conversation Layer
            ↓
      Agent Layer
            ↓
      Workflow Layer
            ↓
      AI Service Layer
            ↓
      Ollama
```

### Workflow Steps Engine

```
      Goal:

            Workflow
              ↓
            Step 1
            Step 2
            Step 3
              ↓
            Final output

      Example:

            Input:
            "Write article about FastAPI"

            Step 1 → Research topic
            Step 2 → Create outline
            Step 3 → Write final article
```

### Streaming execution design

```
      WorkflowService
            ↓
      step-by-step execution
            ↓
      stream progress events to frontend
```

Frontend behavior:

- show live step progress
- render execution timeline
- debug workflow runs in real-time
- build “agent execution UI

The clean architecture separation:

- workflows → definition (CRUD, metadata, steps structure)
- workflow_steps → step configuration (templates, order, prompts)
- workflow_runs → execution layer (runtime, logs, streaming, results)
  - run_workflow() → core engine (no streaming)
  - run_workflow_stream() → wraps core engine and yields events

```
      - Workflows = Blueprint
      - Steps = Instructions
      - WorkflowRuns = Execution Engine
      - Streaming = Runtime telemetry
```

## Workflow engine full testing guide

This guide validates the full workflow execution pipeline:

- Workflow Runs
- Workflow Step Runs (execution persistence)
- Workflow Run Events (event bus)
- Retry logic
- Streaming (SSE)
- Error handling

1. Preconditions

```
1.1 Database must contain:
                  SELECT * FROM workflows;
                  SELECT * FROM workflow_steps;

Expected:

                  At least 1 workflow
                  At least 2–3 steps per workflow

Example:

                  workflow_id = 2
                  steps:
                  1 → research
                  2 → summarize
                  3 → final output

1.2 Tables must exist
                  \dt

You must see:

                  workflow_runs
                  workflow_step_runs
                  workflow_run_events

If missing → run migrations.
```

2. Test NON-STREAM workflow execution

```
2.1 Run workflow

Use API:
                  POST /workflows/{workflow_id}/run

Example:
                  {
                  "input": "How to test workflow system"
                  }

2.2 Expected API response

                  {
                  "workflow_id": 2,
                  "input": "...",
                  "output": "final AI result",
                  "status": "completed"
                  }

2.3 Verify workflow_runs table

                  SELECT * FROM workflow_runs ORDER BY id DESC;

Expected:

                  New row inserted
                  output NOT NULL
                  status = completed

2.4 Verify workflow_step_runs table

                  SELECT * FROM workflow_step_runs ORDER BY id DESC;

Expected:
                  field	expected
                  workflow_run_id	matches run
                  step_order	1..N
                  input	prompt with injected variables
                  output	AI response
                  status	completed
                  execution_time_ms	> 0
                  retry_count	>= 0

If empty → step execution is not running.

2.5 Verify event log table

                  SELECT * FROM workflow_run_events ORDER BY id DESC;

Expected events:

                  step_start
                  step_done
                  workflow_done

Each row should contain:

                  workflow_run_id
                  event_type
                  payload JSON
```

3. Test RETRY logic

```
3.1 Force failure (temporary test)

Modify AIService to temporarily fail:
raise Exception("TEST FAILURE")

3.2 Run workflow again

Expected:

                  retry_count increases (1–3)
                  multiple retry events appear:
                  SELECT * FROM workflow_run_events WHERE event_type = 'retry';

3.3 Expected behavior

                  step_run still created
                  status = failed (if max retries exceeded)
                  error_message populated
```

4. Test STREAMING (SSE)

```
4.1 Run streaming endpoint

                  POST /workflows/{workflow_id}/stream

4.2 Use curl to verify SSE

                  curl -N http://localhost:8000/workflows/2/stream \
                  -H "Content-Type: application/json" \
                  -d '{"input":"test streaming workflow"}'

4.3 Expected SSE format

                  event: step_start
                  data: {...}

                  event: step_done
                  data: {...}

                  event: workflow_done
                  data: {...}

4.4 Verify DB events still written

                  SELECT * FROM workflow_run_events;

Expected:

                  step_start
                  step_done
                  retry (if any)
                  workflow_done
```

5. Validate FULL PIPELINE CONSISTENCY

```
After execution:

5.1 workflow_runs
                  SELECT id, status, output FROM workflow_runs;

Expected:

                  status = completed
                  output NOT NULL

5.2 workflow_step_runs

                  SELECT step_order, status, execution_time_ms FROM workflow_step_runs;

Expected:

                  All steps executed in correct order
                  execution_time_ms populated
                  no missing steps

5.3 workflow_run_events

                  SELECT event_type, COUNT(*)
                  FROM workflow_run_events
                  GROUP BY event_type;

Expected:

                  step_start > 0
                  step_done > 0
                  workflow_done = 1
```

6. Debug checklist (if something is broken)

```
6.1 No step_runs created

Check:

                  _execute_steps() is actually called
                  db.add(step_run) executed
                  await db.commit() reached
                  no silent exception before commit

6.2 No events created

Check:

                  _emit_event() is called
                  await db.flush() not failing
                  workflow_run.id exists (flush before execution)

6.3 workflow_runs created but empty output

Likely causes:

                  AI service returned None
                  exception swallowed in retry loop
                  final_output never assigned

6.4 SQL table missing errors

Run migrations:

                  alembic upgrade head

or recreate DB schema.
```

7. Success Criteria (FULL SYSTEM READY)

```
System is correct if ALL are true:

                  Execution
                  workflow_runs created
                  workflow_steps executed in order
                  workflow_step_runs populated
                  Reliability
                  retry logic works
                  errors stored in DB
                  Observability
                  workflow_run_events populated
                  SSE stream emits events correctly
                  Output
                  workflow_run.output is never NULL
```

### DAG execution model

```
        Step A
       /      \
   Step B    Step C
       \      /
        Step D
         |
      Step E
```

Key capabilities:

- parallel execution (B & C run concurrently)
- dependency resolution
- conditional routing
- step-level isolation
- partial failure handling

2. Core conceptual shift

- Old model

Each step depends on: previous_output

- New model

Each step depends on:

```
dependencies = [step_ids]
inputs = resolved dependency outputs
```

No global "previous_output" anymore.

```
            File -> Responsibility

workflow_service.py  -> orchestration
dag_engine.py        -> DAG scheduling
step_executor.py     -> AI execution
event_bus.py         -> SSE + events
```

#### For now architecture becomes:

- Layer 1 — DAG Storage - Workflow - WorkflowStep - dependencies - conditions - tools - models
- Layer 2 — Runtime Engine - scheduler - executor - retry manager - timeout manager - event bus - parallel runner
- Layer 3 — Agent Runtime - tool calls - memory - context - reflection - routing - planning

workflow/
├── workflow.py # orchestration
├── dag_engine.py # scheduler
├── ai_executor.py # LLM calls
├── event_bus.py # events
├── repositories/
│ ├── workflow_runs.py
│ ├── workflow_steps.py
│ └── workflow_events.py

Production version is to build tasks explicitly:

```
Step 14 = success
Step 15 = raises AttributeError

=> results contains:

- success result for 14
- failed result for 15

=> workflow can:

- continue_on_error=True -> keep going
- continue_on_error=False -> stop cleanly
```
