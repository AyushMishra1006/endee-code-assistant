"""
Main FastAPI application - Code Documentation Assistant
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from utils import clone_repository, find_python_files, cleanup_repo
from code_parser import parse_repository, chunk_for_storage
from embeddings import embed_texts
from vector_db import get_vector_db, reset_vector_db
from rag_handler import get_rag_handler

app = FastAPI(
    title="Code Documentation Assistant",
    description="Search and understand code repositories using semantic search and RAG",
    version="1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
current_repo_info = {
    "repo_url": None,
    "status": "idle",
    "chunks_count": 0
}


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request to analyze a GitHub repository"""
    repo_url: str


class AnalyzeResponse(BaseModel):
    """Response after analyzing repository"""
    status: str
    chunks_count: int
    error: Optional[str] = None


class QueryRequest(BaseModel):
    """Request to query the analyzed code"""
    question: str


class QueryResponse(BaseModel):
    """Response to a code query"""
    answer: str
    sources: list
    relevance: str


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    """
    Analyze a GitHub repository

    1. Clone the repository
    2. Parse Python files
    3. Create embeddings
    4. Index in vector database
    """
    global current_repo_info

    try:
        current_repo_info["status"] = "cloning"

        # Clone repository
        repo_path, error = clone_repository(request.repo_url)
        if error:
            return AnalyzeResponse(
                status="error",
                chunks_count=0,
                error=error
            )

        current_repo_info["status"] = "parsing"

        # Find Python files
        python_files = find_python_files(repo_path)
        if not python_files:
            cleanup_repo(repo_path)
            return AnalyzeResponse(
                status="error",
                chunks_count=0,
                error="No Python files found in repository"
            )

        # Parse repository
        chunks = parse_repository(repo_path, python_files)
        if not chunks:
            cleanup_repo(repo_path)
            return AnalyzeResponse(
                status="error",
                chunks_count=0,
                error="No code chunks could be extracted"
            )

        current_repo_info["status"] = "embedding"

        # Convert chunks to storage format
        chunks_dict = [chunk_for_storage(chunk) for chunk in chunks]

        # Generate embeddings
        texts_to_embed = [c['combined_text'] for c in chunks_dict]
        embeddings = embed_texts(texts_to_embed)

        # Filter out failed embeddings
        valid_pairs = [
            (chunk, emb) for chunk, emb in zip(chunks_dict, embeddings) if emb is not None
        ]

        if not valid_pairs:
            cleanup_repo(repo_path)
            return AnalyzeResponse(
                status="error",
                chunks_count=0,
                error="Could not generate embeddings"
            )

        current_repo_info["status"] = "indexing"

        # Reset vector database
        reset_vector_db()

        # Add to vector database
        valid_chunks = [pair[0] for pair in valid_pairs]
        valid_embeddings = [pair[1] for pair in valid_pairs]

        vector_db = get_vector_db()
        success = vector_db.add_chunks(valid_chunks, valid_embeddings)

        # Cleanup
        cleanup_repo(repo_path)

        if not success:
            return AnalyzeResponse(
                status="error",
                chunks_count=0,
                error="Failed to index chunks in vector database"
            )

        current_repo_info["status"] = "ready"
        current_repo_info["repo_url"] = request.repo_url
        current_repo_info["chunks_count"] = len(valid_chunks)

        return AnalyzeResponse(
            status="success",
            chunks_count=len(valid_chunks)
        )

    except Exception as e:
        current_repo_info["status"] = "error"
        return AnalyzeResponse(
            status="error",
            chunks_count=0,
            error=f"Unexpected error: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse)
async def query_code(request: QueryRequest):
    """
    Query the analyzed code repository

    1. Embed the question
    2. Search vector database for similar code
    3. Generate answer using RAG with Gemini
    """
    if current_repo_info["status"] != "ready":
        raise HTTPException(
            status_code=400,
            detail="No repository analyzed yet. Please call /analyze first."
        )

    try:
        # Embed question
        question_embedding = embed_texts([request.question])[0]
        if question_embedding is None:
            raise HTTPException(
                status_code=500,
                detail="Could not embed question"
            )

        # Search vector database
        vector_db = get_vector_db()
        search_results = vector_db.search(question_embedding, top_k=5)

        if not search_results:
            return QueryResponse(
                answer="No relevant code found for your question.",
                sources=[],
                relevance="low"
            )

        # Generate answer using RAG
        rag_handler = get_rag_handler()
        answer = rag_handler.generate_answer(
            request.question,
            search_results,
            max_chunk_chars=300
        )

        # Format response
        formatted = rag_handler.format_response(answer, search_results)

        return QueryResponse(
            answer=formatted['answer'],
            sources=formatted['sources'],
            relevance=formatted['relevance']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying: {str(e)}"
        )


@app.get("/status")
async def get_status():
    """Get current analysis status"""
    return {
        "status": current_repo_info["status"],
        "repo_url": current_repo_info["repo_url"],
        "chunks_count": current_repo_info["chunks_count"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
