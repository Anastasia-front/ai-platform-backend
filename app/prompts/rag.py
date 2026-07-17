class RAGPromptBuilder:
    """
    Pure prompt construction logic for RAG.
    No DB, no HTTP, no side effects.
    """

    def build_system_prompt(
        self,
        *,
        base_prompt: str,
        context: str,
    ) -> str:
        if not context:
            return base_prompt

        return f"""
{base_prompt}

You are allowed to use the following retrieved context.

Rules:
- Use context as primary source of truth
- If context is insufficient, say you don't know
- Do not hallucinate information
- Prefer concise answers

Context:
{context}
""".strip()

    def build_agent_orchestrator_prompt(
        self,
        *,
        base_prompt: str,
        used_document_search: bool,
        context: str,
        retrieval_queries: list[str],
    ) -> str:
        tool_summary = "No tools were needed."
        if used_document_search:
            tool_summary = (
                "Tool used: search_project_documents\n"
                "Queries:\n"
                + "\n".join(f"- {query}" for query in retrieval_queries)
            )

        prompt = f"""
{base_prompt}

Agent execution rules:
- You are receiving the result of completed internal tool calls
- Do not ask the user to provide uploaded documents
- Do not ask the user to extract, summarize, describe, paste, or check document content
- Complete the delegated work yourself using the retrieved project context
- If document search was used, answer from retrieved project context only
- If retrieved context is insufficient, say what is missing
- When comparing multiple files, produce a per-file or per-entity answer
- Include concrete evidence from the retrieved context, not generic process steps
- Keep planning and chain-of-thought private
- Return only the final user-facing answer

{tool_summary}
""".strip()

        if not context:
            return prompt

        return f"""
{prompt}

Retrieved project context:
{context}
""".strip()

    def build_context(
        self,
        chunks: list,
    ) -> str:
        if not chunks:
            return ""

        blocks = []
        for i, c in enumerate(chunks, start=1):
            blocks.append(
                f"[Source {i}]\n"
                f"Document: {c.document_id}\n\n"
                f"ChunkId: {c.chunk_id}\n\n"
                f"ChunkIndex: {c.chunk_index}\n\n"
                f"Score: {c.score}\n\n"
                f"{c.text}"
            )

        return "\n\n".join(blocks)
