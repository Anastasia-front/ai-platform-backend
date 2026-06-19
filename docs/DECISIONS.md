# Decisions

This file records technical decisions that shape the project. It should stay
lightweight: add a new entry when a decision changes the system direction or
prevents repeated debate.

## Decision Format

Each decision should include:

- Status: proposed, accepted, superseded, or deprecated.
- Context: what problem or constraint led to the decision.
- Decision: the chosen approach.
- Consequences: what this enables and what tradeoffs it creates.

## Accepted Decisions

### Use FastAPI for the API Layer

Status: accepted

Context: The platform needs a Python API framework with strong async support,
automatic OpenAPI docs, dependency injection, and Pydantic integration.

Decision: Use FastAPI as the HTTP API framework.

Consequences:

- API docs are available locally through `/docs` and `/redoc`.
- Route dependencies can handle auth, ownership checks, repositories, and
  services.
- Pydantic request and response models fit naturally into route handlers.
- Long-running work still needs careful handling through streaming or background
  workers because HTTP request lifetimes are finite.

### Use SQLAlchemy Async with PostgreSQL

Status: accepted

Context: The platform stores relational data for users, projects, chats,
documents, workflows, runs, step runs, and events. It also needs a future path to
vector storage.

Decision: Use SQLAlchemy 2.x async ORM with `asyncpg` and PostgreSQL.

Consequences:

- The code can use async request handling and database calls.
- PostgreSQL gives durable relational storage and a strong migration path.
- Future `pgvector` support can live in the same database.
- Async ORM code requires explicit session and transaction discipline.

### Use Alembic for Database Migrations

Status: accepted

Context: The schema is evolving quickly and needs repeatable local and future
deployment migrations.

Decision: Use Alembic migrations.

Consequences:

- Schema changes are versioned.
- Local development and deployment can apply the same migration chain.
- Developers must keep models and migrations in sync.

### Use the Repository Pattern for Persistence

Status: accepted

Context: Route handlers and services need database operations without spreading
SQLAlchemy query details throughout the API layer.

Decision: Put model-specific data access in repository classes under
`app/repositories/`.

Consequences:

- Routes and services can express intent more clearly.
- Ownership-aware query helpers can be reused.
- Repositories remain easy to test in isolation.
- Repositories should not hide transaction boundaries; callers still commit.

### Keep Transaction Boundaries Outside Repositories

Status: accepted

Context: Many operations involve multiple repository calls that should succeed
or fail together.

Decision: Repositories may add, delete, query, and flush. Routes or services own
`db.commit()`.

Consequences:

- Multi-step operations can be atomic.
- Rollback behavior is easier to reason about.
- Callers must be consistent about committing write operations.

### Use Dependency Functions for Auth, Ownership, Repositories, and Services

Status: accepted

Context: Many routes need the same current-user, ownership, repository, and
service wiring.

Decision: Use FastAPI dependencies in `app/dependencies/` for shared route
requirements.

Consequences:

- Authorization checks are reusable.
- Route signatures show required resources clearly.
- Dependency code must remain focused and avoid becoming hidden business logic.

### Use Local File Storage for Initial Uploads

Status: accepted

Context: The document feature needs a simple upload path before production file
storage requirements are known.

Decision: Save uploaded files under local `uploads/` and store document metadata
and filepath in PostgreSQL.

Consequences:

- The implementation is simple and fast for local development.
- It avoids adding object storage before it is necessary.
- It is not sufficient for multi-instance deployment, strong backup guarantees,
  or untrusted filename handling without further hardening.
- Future deployments may move files to S3, GCS, MinIO, or another object store.

### Plan for `pgvector` for Embedding Search

Status: accepted

Context: RAG requires vector similarity search over document chunks. The project
already uses PostgreSQL.

Decision: Plan to use PostgreSQL with `pgvector` for embeddings once the
document chunk model and embedding provider are implemented.

Consequences:

- Relational metadata and vectors can stay in one database.
- Project and document filters can be applied near vector search.
- The team avoids introducing a separate vector database while the platform is
  small.
- Very large vector volumes may require revisiting this decision later.

### Use Pluggable Extractor, Chunking, and Embedding Services

Status: accepted

Context: Document processing will need file-type-specific extraction,
deterministic chunking, and interchangeable embedding providers.

Decision: Keep extraction, chunking, and embedding concerns in separate service
modules.

Consequences:

- TXT, PDF, and DOCX support can evolve independently.
- Embedding providers can be swapped without rewriting document orchestration.
- `DocumentService` can become the pipeline coordinator instead of mixing all
  processing logic into routes.

### Keep Workflow Execution in a Service and DAG Engine

Status: accepted

Context: Workflow execution includes dependency resolution, retries, conditions,
parallel step execution, event emission, and persistence.

Decision: Route workflow run requests through `WorkflowService`, with DAG logic
in `DAGEngine`.

Consequences:

- The route layer stays smaller for complex workflow behavior.
- DAG execution can be tested independently.
- Future worker-based execution can reuse the same service/engine boundary.

### Use Local AI Provider Configuration First

Status: accepted

Context: The settings include Ollama base URL and model configuration, and local
development benefits from a local-first AI path.

Decision: Keep AI generation behind `AIService` and configure the local provider
through environment settings.

Consequences:

- Development can proceed without committing to a hosted provider.
- AI provider details are isolated from most route handlers.
- Embeddings and chat generation may later use different providers.

## Proposed / Future Decisions

### Background Worker Choice

Status: proposed

Context: Document processing and long workflow runs may outgrow request-bound
execution.

Decision to make: Choose whether to use a queue-backed worker system such as
Celery, Dramatiq, RQ, or a smaller async worker.

Factors:

- Deployment complexity.
- Retry and scheduling requirements.
- Visibility into job status.
- Whether Redis or another broker is acceptable.

### Object Storage Choice

Status: proposed

Context: Local upload storage is enough for development but weak for production.

Decision to make: Choose S3, GCS, MinIO, or another object storage target when
deployment requirements are clear.

Factors:

- Hosting environment.
- Backup and retention requirements.
- File size limits.
- Private file access patterns.

### Embedding Provider

Status: proposed

Context: RAG needs embeddings. The project may choose local embeddings or a
hosted provider.

Decision to make: Choose the first embedding provider for the MVP.

Options:

- Local SentenceTransformers.
- Ollama embeddings.
- OpenAI embeddings.
- Another hosted embedding API.

Factors:

- Cost.
- Latency.
- Local development convenience.
- Quality on the expected document types.
- Embedding dimensions and vector index implications.
