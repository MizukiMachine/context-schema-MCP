"""RAG (Retrieval-Augmented Generation) Context Management Service.

Provides document indexing,semantic search,
and context integration for RAG workflows.
"""

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Document:
    """Represents an indexed document."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""

    document: Document
    score: float
    highlights: list[str] = field(default_factory=list)


class SimpleEmbedding:
    """Simple embedding using TF-IDF-like scoring.

    This is a lightweight alternative to neural embeddings
    suitable for demo purposes. In production, use
    OpenAI embeddings or sentence-transformers.
    """

    def __init__(self) -> None:
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.document_count = 0

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        # Convert to lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = []
        current_token = []

        for char in text:
            if char.isalnum():
                current_token.append(char)
            else:
                if current_token:
                    tokens.append("".join(current_token))
                    current_token = []

        if current_token:
            tokens.append("".join(current_token))

        return [t for t in tokens if len(t) > 1]

    def fit(self, documents: list[str]) -> None:
        """Build vocabulary and IDF from documents."""
        self.document_count = len(documents)
        doc_freq: dict[str, int] = defaultdict(int)

        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                if token not in self.vocabulary:
                    self.vocabulary[token] = len(self.vocabulary)
                doc_freq[token] += 1

        # Calculate IDF
        for token, freq in doc_freq.items():
            self.idf[token] = math.log(self.document_count / (1 + freq)) + 1

    def encode(self, text: str) -> list[float]:
        """Encode text to embedding vector."""
        tokens = self._tokenize(text)
        token_freq: dict[str, int] = defaultdict(int)

        for token in tokens:
            token_freq[token] += 1

        # Create TF-IDF-like vector
        vector = [0.0] * len(self.vocabulary)

        for token, freq in token_freq.items():
            if token in self.vocabulary:
                idx = self.vocabulary[token]
                tf = freq / len(tokens) if tokens else 0
                tfidf = tf * self.idf.get(token, 1.0)
                vector[idx] = tfidf

        # Normalize
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector


class RAGContextManager:
    """Manages document indexing and retrieval for RAG."""

    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self.embeddings = SimpleEmbedding()
        self._fitted = False

    def _generate_id(self, content: str) -> str:
        """Generate unique document ID."""
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def add_document(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> Document:
        """
        Add a document to the index.

        Args:
            content: Document text content
            metadata: Optional metadata dictionary
            doc_id: Optional custom document ID

        Returns:
            The created Document
        """
        doc_id = doc_id or self._generate_id(content)
        metadata = metadata or {}

        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata,
        )

        self.documents[doc_id] = doc

        # Refit embeddings with all documents
        self._rebuild_index()

        return doc

    def _rebuild_index(self) -> None:
        """Rebuild embedding index with all documents."""
        contents = [doc.content for doc in self.documents.values()]
        if contents:
            self.embeddings.fit(contents)
            # Update document embeddings
            for doc in self.documents.values():
                doc.embedding = self.embeddings.encode(doc.content)
            self._fitted = True

    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the index.

        Args:
            doc_id: Document ID to remove

        Returns:
            True if document was removed, False if not found
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._rebuild_index()
            return True
        return False

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            top_k: Maximum number of results to return
            threshold: Minimum similarity score threshold

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not self._fitted or not self.documents:
            return []

        # Encode query
        query_embedding = self.embeddings.encode(query)

        # Calculate similarities
        scored_docs: list[tuple[Document, float]] = []

        for doc in self.documents.values():
            if doc.embedding:
                score = self._cosine_similarity(query_embedding, doc.embedding)
                if score >= threshold:
                    scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Take top_k and create results
        results = []
        for doc, score in scored_docs[:top_k]:
            highlights = self._extract_highlights(query, doc.content)
            results.append(SearchResult(document=doc, score=score, highlights=highlights))

        return results

    def _extract_highlights(self, query: str, content: str) -> list[str]:
        """Extract relevant highlights from content based on query."""
        query_terms = set(self.embeddings._tokenize(query))

        highlights = []
        sentences = content.replace("。", ".").replace("！", "!").replace("？", "?").split(".")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = sentence.lower()
            matching_terms = sum(1 for term in query_terms if term in sentence_lower)

            if matching_terms > 0:
                # Truncate long sentences
                if len(sentence) > 150:
                    sentence = sentence[:147] + "..."
                highlights.append(sentence)

                if len(highlights) >= 3:
                    break

        return highlights

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Get combined context for a RAG query.

        Args:
            query: User query
            max_tokens: Maximum tokens to include in context
            top_k: Number of documents to consider

        Returns:
            Dictionary with combined context and metadata
        """
        results = self.search(query, top_k=top_k)

        if not results:
            return {
                "context": "",
                "sources": [],
                "total_tokens": 0,
                "document_count": 0,
            }

        # Build context within token limit
        context_parts = []
        total_tokens = 0
        sources = []

        for result in results:
            doc = result.document
            tokens_estimate = len(doc.content) // 4

            if total_tokens + tokens_estimate > max_tokens:
                # Include partial if we have room
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:
                    partial_content = doc.content[: remaining_tokens * 4]
                    context_parts.append(f"[{doc.id}] {partial_content}...")
                    total_tokens += remaining_tokens
                break

            context_parts.append(f"[{doc.id}] {doc.content}")
            total_tokens += tokens_estimate

            sources.append(
                {
                    "id": doc.id,
                    "score": result.score,
                    "highlights": result.highlights,
                    "metadata": doc.metadata,
                }
            )

        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "total_tokens": total_tokens,
            "document_count": len(sources),
        }

    def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID."""
        return self.documents.get(doc_id)

    def list_documents(self) -> list[Document]:
        """List all documents."""
        return list(self.documents.values())

    def clear(self) -> None:
        """Clear all documents."""
        self.documents.clear()
        self._fitted = False


# Global instance for easy access
_rag_manager: RAGContextManager | None = None


def get_rag_manager() -> RAGContextManager:
    """Get the global RAG manager instance."""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGContextManager()
    return _rag_manager
