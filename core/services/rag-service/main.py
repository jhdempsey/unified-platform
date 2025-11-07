"""RAG API Service."""

import os
from typing import List

from embeddings import VertexAIEmbeddings
from fastapi import FastAPI, HTTPException
from generator import AIGatewayGenerator
from pydantic import BaseModel
from vectorstore import PineconeVectorStore

# Set project ID
os.environ["GCP_PROJECT_ID"] = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0282248851")

app = FastAPI(title="Supply Chain RAG API", version="1.0.0")

# Initialize services
embedder = VertexAIEmbeddings()
vectorstore = PineconeVectorStore()
generator = AIGatewayGenerator()


class QueryRequest(BaseModel):
    """Query request model."""

    question: str
    top_k: int = 3
    team_id: str = "rag-demo"


class QueryResponse(BaseModel):
    """Query response model."""

    question: str
    answer: str
    sources: List[dict]
    provider: str
    cost: float


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-api"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system."""
    try:
        # Generate query embedding
        query_vector = embedder.embed_query(request.question)

        # Search vector store
        results = vectorstore.query(query_vector, top_k=request.top_k)

        if not results:
            raise HTTPException(status_code=404, detail="No relevant documents found")

        # Build context from retrieved chunks
        context_parts = []
        sources = []

        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}]: {result['metadata']['text']}")
            sources.append(
                {
                    "filename": result["metadata"]["filename"],
                    "score": float(result["score"]),
                    "document_id": result["metadata"]["document_id"],
                }
            )

        context = "\n\n".join(context_parts)

        # Generate answer using AI Gateway
        answer = generator.generate_answer(
            question=request.question,
            context=context,
            sources=sources,
            team_id=request.team_id,
        )

        return QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            provider="ai-gateway",
            cost=0.0,  # Could extract from generator if needed
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/ingest")
async def ingest_documents():
    """Trigger document ingestion."""
    try:
        from ingest_documents import ingest_documents

        ingest_documents()
        return {"status": "success", "message": "Documents ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
