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
                f"Document: {c.document_name}\n\n"
                f"{c.text}"
            )

        return "\n\n".join(blocks)