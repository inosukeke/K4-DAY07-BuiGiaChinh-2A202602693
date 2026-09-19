from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    In-memory vector store for text chunks.

    The embedding_fn parameter allows injection of mock or real embeddings.
    One Document corresponds to one stored record; chunking happens outside
    of the store.
    """

    def __init__(
            self,
            collection_name: str = "documents",
            embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name

        # CP4 intentionally uses the in-memory implementation.
        # This keeps behavior deterministic and independent of whether
        # chromadb happens to be installed on the machine.
        self._use_chroma = False
        self._collection = None
        self._store: list[dict[str, Any]] = []

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """
        Normalize one Document into the internal record format.

        metadata is copied so the caller's dictionary is not mutated.
        doc_id identifies the original document and is required by
        delete_document().
        """
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
            self,
            query: str,
            records: list[dict[str, Any]],
            top_k: int,
    ) -> list[dict[str, Any]]:
        """Run similarity search over the provided candidate records."""
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)

        scored: list[dict[str, Any]] = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])

            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)

        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed and store each Document.

        Chunking is deliberately not performed here:
        one Document passed in equals one stored record.
        """
        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(
            self,
            query: str,
            top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find the top_k most similar stored records."""
        return self._search_records(
            query=query,
            records=self._store,
            top_k=top_k,
        )

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(
            self,
            query: str,
            top_k: int = 3,
            metadata_filter: dict = None,
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        Metadata filtering happens before similarity ranking so irrelevant
        records cannot occupy top-k slots.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(
                    record["metadata"].get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]

        return self._search_records(
            query=query,
            records=candidates,
            top_k=top_k,
        )

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to an original document.

        Returns True if at least one stored record was removed.
        """
        size_before = len(self._store)

        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]

        return len(self._store) < size_before
