from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(
            self,
            store: EmbeddingStore,
            llm_fn: Callable[[str], str],
    ) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
            self,
            question: str,
            top_k: int = 3,
    ) -> str:
        results = self.store.search(question, top_k=top_k)

        if not results:
            return (
                "I could not find relevant information "
                "in the knowledge base."
            )

        context_parts: list[str] = []

        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})

            source = (
                    metadata.get("source_url")
                    or metadata.get("source")
                    or metadata.get("doc_id")
                    or result.get("id")
                    or "unknown"
            )

            context_parts.append(
                f"[{index}] Source: {source}\n"
                f"{result['content']}"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""You are a knowledge base assistant.
        
                    Answer the question using only the context provided below.
                    Do not invent information that is not supported by the context.
                    If the context does not contain enough information to answer,
                    say that the answer could not be found in the provided context.
                    
                    When possible, cite the supporting context using source numbers
                    such as [1], [2], or [3].
                    
                    Context:
                    {context}
                    
                    Question:
                    {question}
                    
                    Answer:
                    """

        return self.llm_fn(prompt)
