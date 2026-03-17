"""RAG Context Management API router.

Provides endpoints for document indexing and semantic search.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.rag import (
    DocumentCreate,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.rag_service import get_rag_manager

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/documents", response_model=DocumentResponse)
async def add_document(data: DocumentCreate) -> DocumentResponse:
    """Add a document to the RAG index."""
    manager = get_rag_manager()
    doc = manager.add_document(data.content, metadata=data.metadata)
    return DocumentResponse(
        id=doc.id,
        content=doc.content,
        metadata=doc.metadata,
        created_at=doc.created_at,
    )


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """Search for similar documents."""
    manager = get_rag_manager()
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    results = manager.search(request.query, top_k=request.top_k)
    return SearchResponse(
        query=request.query,
        results=[
            {
                "id": r.document.id,
                "content": r.document.content[:500],  # Truncate for display
                "metadata": r.document.metadata,
                "score": r.score,
                "highlights": r.highlights,
            }
            for r in results
        ],
        total=len(results),
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str) -> DocumentResponse:
    """Get a document by ID."""
    manager = get_rag_manager()
    doc = manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        content=doc.content,
        metadata=doc.metadata,
        created_at=doc.created_at,
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict:
    """Delete a document from the index."""
    manager = get_rag_manager()
    if not manager.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": doc_id}


@router.post("/context/build", response_model=dict)
async def build_context(query: str, max_sources: int = 3) -> dict:
    """Build a RAG context from search results."""
    manager = get_rag_manager()
    results = manager.search(query, top_k=max_sources)

    context = manager.build_context(query, results)
    return {
        "query": query,
        "sources": len(results),
        "context": context,
        "tokens_estimate": len(context) // 4,
    }
