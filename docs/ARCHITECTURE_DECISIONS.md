# Backend Architecture Decisions

Update this file whenever a meaningful backend architecture, infrastructure, data model, processing pipeline, security model, provider abstraction, or project structure changes.

## Table of Contents

- [Use FastAPI for the API Layer](#use-fastapi-for-the-api-layer)
- [Keep the Backend API-Only](#keep-the-backend-api-only)
- [Use PostgreSQL as the Primary Database](#use-postgresql-as-the-primary-database)
- [Use SQLAlchemy and Alembic for Persistence](#use-sqlalchemy-and-alembic-for-persistence)
- [Use JWT Authentication](#use-jwt-authentication)
- [Separate the Backend into Independent Layers](#separate-the-backend-into-independent-layers)
- [Model Projects as the Ownership Boundary](#model-projects-as-the-ownership-boundary)
- [Keep Chats and Messages Separate](#keep-chats-and-messages-separate)
- [Keep Documents, Chunks, and Embeddings Separate](#keep-documents-chunks-and-embeddings-separate)
- [Keep Workflows, Steps, Runs, Step Runs, and Events Separate](#keep-workflows-steps-runs-step-runs-and-events-separate)
- [Use a Provider Abstraction for Chat AI](#use-a-provider-abstraction-for-chat-ai)
- [Configure Chat and Embedding Providers Separately](#configure-chat-and-embedding-providers-separately)
- [Make RAG Project-Scoped](#make-rag-project-scoped)
- [Separate Document Processing from Embedding Management](#separate-document-processing-from-embedding-management)
- [Run Workflows Through a Dedicated Engine](#run-workflows-through-a-dedicated-engine)
- [Use Redis and Celery for Background Work](#use-redis-and-celery-for-background-work)
- [Keep PostgreSQL as the Source of Truth for Job State](#keep-postgresql-as-the-source-of-truth-for-job-state)
- [Use Environment Variables for Configuration](#use-environment-variables-for-configuration)
- [Support Local and S3 File Storage Through a Storage Interface](#support-local-and-s3-file-storage-through-a-storage-interface)
- [Use Docker and Terraform for Deployment Infrastructure](#use-docker-and-terraform-for-deployment-infrastructure)
- [Restrict Database Access to the EC2 Security Group](#restrict-database-access-to-the-ec2-security-group)
- [Recover Interrupted Workflow Runs from Persisted State](#recover-interrupted-workflow-runs-from-persisted-state)

## Use FastAPI for the API Layer

**Status:** Inferred

### Context

The backend exposes HTTP endpoints for authentication, projects, chats, documents, providers, embeddings, workflows, workflow runs, and health checks.

### Decision

Use FastAPI as the backend HTTP framework.

### Why

FastAPI fits the current backend because the application is route-heavy, dependency-driven, schema-based, and asynchronous around database and external provider calls.

### Consequences

The backend gets a compact endpoint layer, dependency injection, async handlers, and generated API schemas. Long-running work still needs workers instead of request-bound execution.

### Evidence in code

- `app/main.py`
- `app/api/router.py`
- `app/api/routes/`
- `app/dependencies/`
- `README.md`

## Keep the Backend API-Only

**Status:** Inferred

### Context

The backend contains API routes, services, database models, tasks, and infrastructure, but no frontend pages or frontend build pipeline.

### Decision

Keep this backend as an API-only service separated from frontend concerns.

### Why

The API-only shape lets backend code focus on persistence, authentication, background jobs, AI provider integration, document processing, and workflow execution.

### Consequences

Frontend applications can consume the API independently. Cross-origin, deployment, and contract stability become important API concerns.

### Evidence in code

- `app/api/routes/`
- `app/schemas/`
- `app/main.py`
- `Dockerfile`
- `.github/workflows/deploy.yml`

## Use PostgreSQL as the Primary Database

**Status:** Accepted

### Context

The backend needs durable relational storage for users, projects, chats, messages, documents, chunks, embeddings, workflows, runs, events, provider configuration, and job state.

### Decision

Use PostgreSQL as the primary database.

### Why

PostgreSQL supports the relational model already used by the backend, PostgreSQL-specific JSONB fields, and vector embeddings through pgvector.

### Consequences

The backend has strong relational integrity and can store vector data near the rest of the domain state. It also couples the app to PostgreSQL-specific features such as JSONB and pgvector.

### Evidence in code

- `app/core/database.py`
- `app/models/message.py`
- `app/models/chunk_embedding.py`
- `docker-compose.yml`
- `infra/modules/rds/main.tf`
- `requirements.txt`

## Use SQLAlchemy and Alembic for Persistence

**Status:** Accepted

### Context

The backend has many related entities and recurring schema changes across users, projects, documents, embeddings, provider configuration, workflows, and background-job tracking.

### Decision

Use SQLAlchemy async ORM for database access and Alembic for migrations.

### Why

SQLAlchemy maps the domain models to PostgreSQL while repositories keep query code separate from routes. Alembic records schema evolution for local development and deployed environments.

### Consequences

Database changes are reviewable and repeatable. The trade-off is migration maintenance and the need to keep models and migrations aligned.

### Evidence in code

- `app/core/database.py`
- `app/models/`
- `app/repositories/`
- `alembic/env.py`
- `alembic/versions/`
- `alembic.ini`

## Use JWT Authentication

**Status:** Accepted

### Context

The API needs authenticated user access and ownership checks across projects, chats, documents, workflows, and runs.

### Decision

Use JWT access and refresh tokens with OAuth2 bearer-token extraction.

### Why

JWTs allow stateless API authentication while ownership validation still resolves the current user and owned resources from PostgreSQL.

### Consequences

The API does not need server-side session storage for normal requests. Token secrets, expiration, refresh behavior, and invalidation strategy become security-sensitive.

### Evidence in code

- `app/core/security.py`
- `app/dependencies/auth.py`
- `app/api/routes/auth.py`
- `app/core/config.py`
- `.env.example`

## Separate the Backend into Independent Layers

**Status:** Accepted

### Context

The backend handles HTTP endpoints, database access, business workflows, dependency injection, API contracts, persistence models, shared constants, background tasks, provider integrations, and infrastructure configuration.

### Decision

Organize the backend into routes, repositories, services, dependencies, schemas, models, enums, tasks, core, providers, and workflow-engine modules.

### Why

Routes stay focused on HTTP behavior. Repositories isolate database operations. Services hold business logic. Dependencies wire services and enforce ownership. Schemas define API contracts. Models define persistence. Enums centralize shared status/provider constants. Tasks hold asynchronous work. Core holds configuration and shared infrastructure. Providers isolate external AI APIs. The workflow engine stays separate from endpoints.

### Consequences

The architecture improves maintainability, testability, onboarding, replacement of implementations, and future extraction of services. The trade-off is more files and stricter discipline around where logic belongs.

### Evidence in code

- `app/api/routes/`
- `app/repositories/`
- `app/services/`
- `app/dependencies/`
- `app/schemas/`
- `app/models/`
- `app/enums/`
- `app/tasks/`
- `app/core/`
- `app/services/ai/providers/`
- `app/services/workflow/`

## Model Projects as the Ownership Boundary

**Status:** Accepted

### Context

Chats, documents, workflows, and retrieval all need a shared user-owned scope.

### Decision

Use `Project` as the parent entity for chats, documents, workflows, and project embedding sync state.

### Why

Project ownership gives routes and services one consistent boundary for authorization, retrieval scope, and grouped AI work.

### Consequences

Project-scoped operations are easier to protect and reason about. Cross-project retrieval or workflows would need explicit design rather than accidental joins.

### Evidence in code

- `app/models/project.py`
- `app/dependencies/project.py`
- `app/repositories/projects.py`
- `app/repositories/retrieval.py`
- `app/services/retrieval.py`

## Keep Chats and Messages Separate

**Status:** Accepted

### Context

The backend needs persistent chat threads and individual user, assistant, or system messages with optional RAG citations.

### Decision

Store chats and messages as separate entities.

### Why

A chat represents conversation metadata and project membership, while messages represent ordered conversational content and sources.

### Consequences

Messages can grow independently from chat metadata and can store per-response citations. The trade-off is extra joins and ownership validation through the chat/project relationship.

### Evidence in code

- `app/models/chat.py`
- `app/models/message.py`
- `app/repositories/chats.py`
- `app/repositories/messages.py`
- `app/services/chat.py`
- `app/api/routes/chats.py`
- `app/api/routes/messages.py`

## Keep Documents, Chunks, and Embeddings Separate

**Status:** Accepted

### Context

Uploaded files need metadata, extracted text, smaller retrieval units, and provider/model-specific vector embeddings.

### Decision

Store documents, document chunks, and chunk embeddings as separate entities.

### Why

Documents track upload and processing state. Chunks preserve retrieval-sized text units. Embeddings can be regenerated per provider and model without replacing document or chunk records.

### Consequences

The backend can rebuild embeddings, support multiple providers/models, and cite source documents. Processing requires careful status transitions and cleanup of dependent rows.

### Evidence in code

- `app/models/document.py`
- `app/models/document_chunk.py`
- `app/models/chunk_embedding.py`
- `app/repositories/documents.py`
- `app/repositories/document_chunks.py`
- `app/repositories/chunk_embeddings.py`
- `app/services/document.py`
- `app/services/embedding_management.py`
- `alembic/versions/5bdef629d629_add_chunk_embeddings.py`
- `alembic/versions/9f10682fc7f2_support_multiple_embedding_providers.py`

## Keep Workflows, Steps, Runs, Step Runs, and Events Separate

**Status:** Accepted

### Context

The backend needs reusable workflow definitions, step configuration, execution attempts, per-step runtime records, and event history.

### Decision

Store workflow definitions, workflow steps, workflow runs, workflow step runs, and workflow run events separately.

### Why

Definitions can be reused across runs. Steps define DAG structure and prompts. Runs track execution status and output. Step runs track progress and retry results. Events provide a persisted activity stream.

### Consequences

Workflow execution becomes inspectable, resumable, and debuggable. The trade-off is a more complex persistence model and stricter consistency requirements.

### Evidence in code

- `app/models/workflow.py`
- `app/models/workflow_step.py`
- `app/models/workflow_run.py`
- `app/models/workflow_step_run.py`
- `app/models/workflow_run_event.py`
- `app/services/workflow/`
- `app/repositories/workflow_runs.py`
- `app/repositories/workflow_step_runs.py`
- `app/repositories/workflow_events.py`
- `alembic/versions/91cc967ec6f2_dag_execution.py`
- `alembic/versions/75ee3bb85ff1_add_workflow_runs_and_step_runs.py`

## Use a Provider Abstraction for Chat AI

**Status:** Accepted

### Context

The backend supports multiple chat providers and should avoid wiring provider-specific HTTP details into routes or workflow logic.

### Decision

Put chat generation behind `AIService` and provider classes implementing a common `AIProvider` interface.

### Why

The service can select Ollama, Gemini, OpenRouter, or Groq while callers only ask for a chat response.

### Consequences

Provider replacement is localized. Provider-specific capabilities still need adapter code and shared error handling.

### Evidence in code

- `app/services/ai/service.py`
- `app/services/ai/providers/base.py`
- `app/services/ai/providers/ollama.py`
- `app/services/ai/providers/gemini.py`
- `app/services/ai/providers/openrouter.py`
- `app/services/ai/providers/groq.py`
- `app/enums/llm_provider.py`

## Configure Chat and Embedding Providers Separately

**Status:** Accepted

### Context

The best provider for chat generation may differ from the best provider for embeddings, and some providers do not support both modes.

### Decision

Maintain separate chat and embedding provider configuration.

### Why

Chat and embedding calls have different models, dimensions, endpoints, and capability constraints.

### Consequences

The backend can mix providers, change embedding dimensions, and store provider/model-specific vectors. Configuration and validation must handle two active provider kinds.

### Evidence in code

- `app/services/provider_config.py`
- `app/models/provider_config.py`
- `app/schemas/provider.py`
- `app/services/ai/service.py`
- `app/services/embedding.py`
- `app/enums/llm_provider.py`
- `alembic/versions/aa4c5b9e2d10_add_provider_configs.py`
- `alembic/versions/9f10682fc7f2_support_multiple_embedding_providers.py`

## Make RAG Project-Scoped

**Status:** Accepted

### Context

Retrieval-augmented chat must search the correct user's documents without leaking context between projects.

### Decision

Run retrieval by `project_id` and `user_id`, then build RAG prompts from the matching chunks.

### Why

Project-scoped retrieval matches the ownership model and keeps retrieved context tied to the current project.

### Consequences

RAG answers are isolated by project and can return source citations. Cross-project knowledge search requires a separate feature.

### Evidence in code

- `app/services/rag.py`
- `app/services/retrieval.py`
- `app/repositories/retrieval.py`
- `app/prompts/rag.py`
- `app/models/message.py`
- `app/services/chat.py`

## Separate Document Processing from Embedding Management

**Status:** Accepted

### Context

Documents need extraction and chunking, while embeddings need provider-aware vector generation, rebuilds, and project sync.

### Decision

Keep upload/extraction/chunking in `DocumentService` and embedding rebuild/sync in `EmbeddingManagementService`.

### Why

Document processing and embedding lifecycle change for different reasons. Separating them lets embeddings be regenerated without re-uploading or re-extracting files.

### Consequences

Embedding maintenance can run as background work and can target documents or projects. Coordination is needed between document status and embedding status.

### Evidence in code

- `app/services/document.py`
- `app/services/chunk.py`
- `app/services/extractors/`
- `app/services/embedding.py`
- `app/services/embedding_management.py`
- `app/tasks/documents.py`
- `app/tasks/embeddings.py`

## Run Workflows Through a Dedicated Engine

**Status:** Accepted

### Context

Workflow execution needs dependency validation, cycle detection, conditional execution, retries, per-step output, and event persistence.

### Decision

Keep workflow orchestration in `WorkflowService` and DAG execution in `DAGEngine`, separate from API endpoints.

### Why

The engine encapsulates workflow behavior while routes only create, enqueue, resume, or fetch runs.

### Consequences

Workflow logic can run from API routes, streaming paths, or Celery workers. The engine remains a complex component that needs targeted tests around DAG behavior and recovery.

### Evidence in code

- `app/services/workflow/workflow.py`
- `app/services/workflow/dag_engine.py`
- `app/services/workflow/ai_executor.py`
- `app/services/workflow/event_bus.py`
- `app/api/routes/workflows.py`
- `app/api/routes/workflow_runs.py`
- `app/tasks/workflows.py`

## Use Redis and Celery for Background Work

**Status:** Accepted

### Context

Document processing, embedding rebuilds, project embedding sync, and workflow execution can exceed normal HTTP request lifetimes.

### Decision

Use Celery tasks with Redis as the broker for background execution.

### Why

Celery moves slow work out of FastAPI requests, while Redis provides a lightweight queue transport for workers.

### Consequences

API endpoints can return accepted responses and expose status through persisted rows. Operations now depend on Redis and worker processes being available.

### Evidence in code

- `app/core/celery_app.py`
- `app/services/background_jobs.py`
- `app/tasks/documents.py`
- `app/tasks/embeddings.py`
- `app/tasks/workflows.py`
- `docker-compose.yml`
- `.env.example`
- `README.md`

## Keep PostgreSQL as the Source of Truth for Job State

**Status:** Accepted

### Context

The API and frontend need durable status, progress, output, and error information for long-running work.

### Decision

Persist job state in PostgreSQL instead of relying on Celery task results.

### Why

Domain rows already represent documents, embedding syncs, workflow runs, and workflow events. Keeping status there makes the API independent of Celery result storage.

### Consequences

Redis can remain a broker-only component. Workers must carefully update PostgreSQL status and recover failed operations.

### Evidence in code

- `app/core/celery_app.py`
- `app/models/document.py`
- `app/models/project.py`
- `app/models/workflow_run.py`
- `app/models/workflow_run_event.py`
- `app/tasks/documents.py`
- `app/tasks/embeddings.py`
- `app/tasks/workflows.py`
- `alembic/versions/d1a4c9b7f210_add_celery_job_tracking_columns.py`

## Use Environment Variables for Configuration

**Status:** Accepted

### Context

The backend runs locally, in containers, workers, and on EC2 with different database URLs, provider settings, secrets, storage settings, and broker URLs.

### Decision

Load configuration from environment variables through Pydantic settings and provision deployment values through SSM/Terraform.

### Why

Environment-driven configuration keeps deploy-time settings out of application code and lets API and worker processes share the same configuration surface.

### Consequences

Missing or stale environment variables can break deployments. Secrets must be managed carefully in `.env`, SSM, and CI/CD.

### Evidence in code

- `app/core/config.py`
- `.env.example`
- `docker-compose.yml`
- `infra/modules/ssm/main.tf`
- `infra/main.tf`
- `.github/workflows/deploy.yml`

## Support Local and S3 File Storage Through a Storage Interface

**Status:** Accepted

### Context

Document upload and processing need file persistence in local development and deployed environments.

### Decision

Use a `StorageService` interface with local and S3 implementations selected by configuration.

### Why

The document service can save and read files without knowing whether storage is local disk or S3.

### Consequences

Storage can be replaced without rewriting document processing. Deployed S3 access requires IAM, bucket configuration, and consistent file paths.

### Evidence in code

- `app/services/storage/base.py`
- `app/services/storage/local.py`
- `app/services/storage/s3.py`
- `app/dependencies/services.py`
- `app/services/document.py`
- `infra/modules/s3/`
- `infra/modules/iam/main.tf`

## Use Docker and Terraform for Deployment Infrastructure

**Status:** Accepted

### Context

The backend needs repeatable local dependencies, containerized application builds, and AWS infrastructure for EC2, RDS, S3, ECR, IAM, networking, and SSM parameters.

### Decision

Use Docker for runtime packaging/local services and Terraform for AWS infrastructure.

### Why

Docker gives a repeatable app image and local service stack. Terraform codifies the AWS resources that the deployed backend needs.

### Consequences

Deployments can be automated through CI/CD and ECR. Infrastructure changes require Terraform discipline and state management.

### Evidence in code

- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/deploy.yml`
- `infra/main.tf`
- `infra/modules/ec2/`
- `infra/modules/rds/`
- `infra/modules/s3/`
- `infra/modules/ecr/`
- `infra/modules/iam/`
- `infra/modules/ssm/`

## Restrict Database Access to the EC2 Security Group

**Status:** Accepted

### Context

The deployed API needs database access, but PostgreSQL should not be publicly reachable.

### Decision

Create an RDS security group that allows port 5432 only from the EC2 security group.

### Why

This limits direct database access to the application host security boundary.

### Consequences

The database is less exposed. Direct administration requires access through approved network paths rather than public RDS access.

### Evidence in code

- `infra/modules/network/main.tf`
- `infra/modules/rds/main.tf`
- `infra/main.tf`

## Recover Interrupted Workflow Runs from Persisted State

**Status:** Accepted

### Context

Workers or API processes can restart while workflow runs are pending or running.

### Decision

Recover stale workflow runs at API startup by re-enqueuing pending runs or resuming running runs from persisted step state.

### Why

The DAG engine persists completed step runs, so resumed execution can avoid starting from scratch.

### Consequences

Workflow execution is more resilient to worker crashes. Recovery must avoid double execution by checking staleness and task claim status.

### Evidence in code

- `app/main.py`
- `app/services/workflow/recovery.py`
- `app/services/workflow/dag_engine.py`
- `app/repositories/workflow_runs.py`
- `app/tasks/workflows.py`
