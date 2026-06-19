# Architecture

This project is a FastAPI-based AI workflow automation platform. It manages users,
projects, chats, messages, documents, workflow definitions, workflow runs, step
runs, agent runs, and workflow events.

## System Layers

The backend follows a layered structure:

```text
HTTP client
  -> FastAPI app and routers
  -> dependencies and ownership guards
  -> services for business workflows
  -> repositories for persistence
  -> SQLAlchemy async models
  -> PostgreSQL
```

### App Entrypoint

- `app/main.py` creates the FastAPI application and mounts the API router.
- `app/api/router.py` composes route modules for auth, projects, chats,
  messages, documents, workflows, workflow steps, workflow runs, and agent runs.
- `/docs` and `/redoc` are provided by FastAPI for local API exploration.

### Routers

Routers translate HTTP requests into application actions. They are responsible
for request parsing, response models, dependency injection, ownership checks, and
transaction boundaries when a service does not own the full transaction.

Important route groups:

- `app/api/routes/auth.py`: registration, login, and current-user lookup.
- `app/api/routes/projects.py`: project CRUD scoped to the authenticated user.
- `app/api/routes/chats.py`: chat CRUD scoped through project or chat ownership.
- `app/api/routes/messages.py`: message creation and AI response generation.
- `app/api/routes/documents.py`: project document listing and upload.
- `app/api/routes/workflows.py`: workflow CRUD, synchronous runs, and streaming
  runs.
- `app/api/routes/workflow_runs.py`: run lookup, resume, and run events.

### Dependencies

`app/dependencies/` contains reusable FastAPI dependency functions:

- Authentication and current-user resolution.
- Ownership guards such as owned project, chat, workflow, and workflow run.
- Repository factories.
- Service factories.

These dependencies keep route handlers smaller and centralize authorization
rules that must be reused across endpoints.

### Services

Services contain business workflows that span multiple repositories or external
systems.

Current service areas:

- `AuthService`: user creation and credential validation.
- `AIService`: chat completion integration through the configured local AI
  provider.
- `WorkflowService`: creates workflow runs, delegates execution to the DAG
  engine, emits completion events, commits completed runs, and resumes runs.
- `DAGEngine`: resolves dependencies between workflow steps, detects cycles,
  evaluates simple conditions, executes ready steps in parallel, records step
  runs, and emits workflow events.
- `DocumentService`, `ChunkService`, and `EmbeddingService`: planned document
  processing pipeline surfaces.

### Repositories

Repositories wrap SQLAlchemy async persistence and expose model-specific data
access methods.

Examples:

- `ProjectRepository`: create, list, fetch, and delete projects.
- `ChatRepository` and `MessageRepository`: chat and message persistence.
- `DocumentRepository`: document creation and project/user-scoped document
  lookup.
- `WorkflowRepository`, `WorkflowStepRepository`, `WorkflowRunRepository`,
  `WorkflowStepRunRepository`, and `WorkflowEventRepository`: workflow
  persistence and run history.

Repositories should not commit transactions. They add, query, delete, and flush
entities. Routes or services decide when a transaction is complete.

### Models and Schemas

- `app/models/` contains SQLAlchemy ORM models and relationships.
- `app/schemas/` contains Pydantic request and response contracts.
- `app/enums/` contains shared status and type values.

The API should expose schemas, not raw internal assumptions. SQLAlchemy models
remain the persistence layer.

## Data Flow

### Authenticated CRUD Flow

```text
Client request with Bearer token
  -> route handler
  -> get_current_user dependency
  -> ownership dependency when resource-specific access is needed
  -> repository query or mutation
  -> db.commit() for writes
  -> Pydantic response model
```

Example: creating a project.

```text
POST /projects
  -> get_current_user
  -> ProjectRepository.create()
  -> commit and refresh
  -> ProjectResponse
```

### Chat Flow

```text
POST /chats/{chat_id}/messages
  -> verify chat ownership
  -> save user message
  -> load chat history
  -> resolve configured agent prompt
  -> call AIService
  -> save assistant message
  -> commit
  -> return both messages
```

The current chat path is route-driven. If the flow grows to include retrieval,
tool calls, citations, retries, or streaming, it should move into a chat service
so the route remains thin.

### Workflow Run Flow

```text
POST /workflows/{workflow_id}/run
  -> verify workflow ownership
  -> WorkflowService.run_workflow()
  -> WorkflowRunRepository.create()
  -> DAGEngine.execute()
  -> WorkflowStepRunRepository records each step result
  -> EventBus emits run and step events
  -> WorkflowRunRepository.complete()
  -> commit
  -> WorkflowRunResponse
```

The DAG engine:

- Loads workflow steps for a workflow.
- Detects cycles before execution.
- Tracks completed steps and outputs.
- Evaluates step conditions using a restricted evaluator.
- Runs dependency-ready steps concurrently.
- Supports retry and continue-on-error behavior.
- Persists step-level output and status.

### Document Upload Flow

Current flow:

```text
POST /projects/{project_id}/documents
  -> verify project ownership
  -> write uploaded file to local uploads/
  -> create Document row with uploaded status
  -> commit
  -> DocumentResponse
```

Local file storage is intentionally simple for the early stage. The database
stores metadata and a filepath, while the raw document bytes live on disk.

## Planned Document and RAG Pipeline

The planned document pipeline should evolve from upload-only storage into a full
retrieval flow:

```text
Upload file
  -> create Document(status=uploaded)
  -> mark processing
  -> extract text by file type
  -> normalize text and metadata
  -> chunk text with overlap
  -> embed chunks
  -> store chunks and vectors
  -> mark indexed
  -> retrieve relevant chunks during chat/workflow execution
  -> generate answer with citations or source metadata
```

Planned components:

- Extractors in `app/services/extractors/` for TXT, PDF, and DOCX.
- `DocumentService.process()` to coordinate extraction, chunking, embedding,
  persistence, and status transitions.
- `ChunkService` for deterministic text splitting and overlap rules.
- `EmbeddingService` for provider-specific embedding generation.
- `DocumentChunkRepository` for chunk metadata and vector persistence.
- A retrieval service that accepts a project ID and query, embeds the query,
  runs nearest-neighbor search, and returns ranked chunks.

Planned statuses:

- `uploaded`: file has been saved and metadata exists.
- `processing`: extraction, chunking, or embedding is in progress.
- `indexed`: chunks and embeddings are available for retrieval.
- `failed`: processing failed and the document should be retried or inspected.

Near-term vector storage can start with plain chunk rows and provider-generated
embedding placeholders. The intended production path is PostgreSQL with
`pgvector` so project data, chunks, metadata, and vectors stay in one database
while the platform is still small.

## Transaction Boundaries

The current rule is:

- Repositories manipulate entities and flush when needed.
- Routes commit simple CRUD writes.
- Services commit larger business workflows when they own the full operation.

This keeps multi-step changes atomic and makes rollback behavior predictable.

## Storage Boundaries

Current storage:

- PostgreSQL stores users, projects, chats, messages, documents, workflows,
  steps, runs, step runs, agent runs, and workflow events.
- Local disk stores uploaded document files under `uploads/`.

Expected future storage:

- PostgreSQL plus `pgvector` for document chunk embeddings.
- Object storage such as S3, GCS, or MinIO if local uploads become unsuitable
  for deployment, multi-worker processing, or backups.

## External Integrations

The project is prepared for local AI integration through configured Ollama
settings. Future integrations may include:

- OpenAI or another hosted model provider for chat and embeddings.
- SentenceTransformers or Ollama embeddings for local-first development.
- Background workers for document indexing and long-running workflows.

## Architectural Principles

- Keep routes thin as orchestration grows.
- Put cross-repository business flows in services.
- Keep repositories focused on persistence, not policy.
- Keep ownership checks centralized in dependencies.
- Prefer explicit transaction boundaries.
- Make document processing restartable through durable statuses.
- Keep early infrastructure simple, but leave a clear path to async workers and
  vector search.
