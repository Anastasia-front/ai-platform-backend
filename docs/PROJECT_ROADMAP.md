# Project Roadmap

This roadmap tracks the platform from the current CRUD and workflow foundation
toward document processing, embeddings, RAG, and stronger workflow operations.

## Completed

### Foundation

- FastAPI application structure with centralized API router.
- Async SQLAlchemy engine and session handling.
- Pydantic settings loaded from `.env`.
- PostgreSQL development database through Docker Compose.
- Alembic migrations for schema evolution.
- Core model and schema folders organized by domain.

### Authentication and Ownership

- User registration.
- Login with bearer token response.
- Current-user endpoint.
- Password hashing and JWT access-token support.
- Protected routes using `get_current_user`.
- Ownership dependencies for user-scoped resources.

### Project, Chat, and Message APIs

- Project create, list, fetch, and delete.
- Chat create, list, fetch, and delete.
- Message list and create.
- Agent prompt selection by chat `agent_name`.
- AI response generation through the AI service.

### Workflow Foundation

- Workflow create, list, fetch, delete, and run endpoints.
- Workflow step support.
- Workflow run and step run persistence.
- DAG execution engine with dependency resolution.
- Cycle detection.
- Conditional step execution.
- Parallel execution of ready steps.
- Retry and continue-on-error behavior.
- Workflow event persistence.
- Workflow run resume endpoint.
- Streaming run endpoint foundation.

### Document Foundation

- Project-scoped document list endpoint.
- Project-scoped file upload endpoint.
- Local file storage under `uploads/`.
- Document metadata persistence.
- Document status field with upload/indexing lifecycle values.
- Placeholder service surfaces for document processing, chunking, and embeddings.
- Extractor module structure for TXT, PDF, and DOCX.

## In Progress / Next

### Document Processing

- Implement real text extraction for supported file types.
- Add a document processing endpoint, for example:
  `POST /projects/{project_id}/documents/{document_id}/process`.
- Move upload and processing orchestration into `DocumentService`.
- Update document status transitions:
  `uploaded -> processing -> indexed` or `failed`.
- Store extraction errors in a durable field or event table.
- Add file validation for size, extension, MIME type, and duplicate filenames.
- Make upload paths collision-safe instead of using raw filenames directly.

### Chunk Storage

- Define or finish the `DocumentChunk` model.
- Implement `DocumentChunkRepository`.
- Persist chunk text, order, token/character offsets, document ID, project ID,
  and source metadata.
- Add deterministic chunking tests for overlap behavior and edge cases.

### Embeddings

- Choose the first embedding provider for development.
- Implement `EmbeddingService.embed_text()`.
- Add batch embedding support for document chunks.
- Store embedding model name and dimensions with chunk metadata.
- Add retry and failure handling around embedding calls.

### RAG

- Add query embedding and retrieval service.
- Add project-scoped nearest-neighbor search.
- Add a retrieval endpoint for manual inspection.
- Integrate retrieved context into chat responses.
- Integrate retrieved context into workflow steps where useful.
- Return source metadata or citations with generated answers.

### Workflow Improvements

- Add list endpoint for workflow runs with filters by workflow and status.
- Add pagination to workflow events.
- Improve streaming so callers receive step events as they happen, not only the
  final event.
- Clarify workflow status naming between workflow definitions and workflow runs.
- Add cancellation or timeout handling for long-running steps.
- Add stronger recovery behavior for interrupted runs.

## Later

### Background Processing

- Move document processing to a background worker.
- Move long-running workflow execution to a worker when request timeouts become
  a problem.
- Add a queue such as Redis/RQ, Celery, Dramatiq, or a lightweight async worker
  depending on deployment needs.
- Make document processing and workflow execution idempotent.

### Vector Search Infrastructure

- Add `pgvector` to PostgreSQL.
- Store embeddings in vector columns.
- Add approximate nearest-neighbor indexes once data volume requires them.
- Add filters for project ID, document ID, status, and metadata.

### API Hardening

- Add pagination to list endpoints.
- Add update endpoints where product workflows require them.
- Standardize error response shapes.
- Add request limits for uploads and AI calls.
- Add integration tests around authentication and ownership boundaries.

### Operations

- Add structured logging.
- Add health checks.
- Add migration and startup documentation for deployment.
- Add backup and restore notes for Postgres and uploaded files.
- Add observability for AI calls, document processing, and workflow step timing.

## Milestone Checklist

### Milestone 1: Document Processing MVP

- [ ] Implement TXT extraction.
- [ ] Implement PDF extraction.
- [ ] Implement DOCX extraction.
- [ ] Add process endpoint.
- [ ] Persist chunks without embeddings.
- [ ] Mark document status as indexed after successful chunk persistence.
- [ ] Add smoke-test steps to `API_CHECKLIST.md`.

### Milestone 2: Embeddings MVP

- [ ] Select embedding provider.
- [ ] Implement single-text embedding.
- [ ] Implement batch embeddings.
- [ ] Persist embeddings with chunks.
- [ ] Record embedding model and dimensions.
- [ ] Add failure handling and retry strategy.

### Milestone 3: RAG MVP

- [ ] Implement query embedding.
- [ ] Implement project-scoped retrieval.
- [ ] Add manual retrieval endpoint.
- [ ] Inject retrieved context into chat responses.
- [ ] Include source metadata in responses.
- [ ] Add tests for retrieval filtering and ownership.

### Milestone 4: Workflow Reliability

- [ ] Add workflow run listing and filters.
- [ ] Add event pagination.
- [ ] Stream intermediate workflow events.
- [ ] Add step timeout handling.
- [ ] Improve resume semantics.
- [ ] Add integration tests for DAG execution.
