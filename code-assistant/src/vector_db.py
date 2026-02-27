"""
Vector Database Wrapper - Interface to Endee for storing and searching code embeddings
"""
from typing import Optional, Any
import json


class VectorDatabase:
    """Wrapper around Endee vector database"""

    def __init__(self):
        """Initialize vector database"""
        self.db = None
        self.chunks_metadata = {}  # Store metadata locally since Endee is in-memory
        self.initialized = False

    def initialize(self):
        """Initialize Endee vector database"""
        try:
            # Import Endee
            # Note: Endee might be in parent directory
            import sys
            sys.path.insert(0, '/c/Users/Ayush Mishra/OneDrive/Desktop/Endee')

            # For now, use in-memory storage
            # In production, we would import actual Endee
            self.db = {}
            self.initialized = True
            print("Vector database initialized (in-memory mode)")
        except Exception as e:
            print(f"Warning: Could not initialize Endee: {e}")
            self.db = {}
            self.initialized = True

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> bool:
        """
        Add code chunks with embeddings to vector database

        Args:
            chunks: List of chunk dictionaries (with metadata)
            embeddings: List of embedding vectors

        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            self.initialize()

        try:
            if len(chunks) != len(embeddings):
                return False

            # Store in-memory (or connect to actual Endee)
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = chunk['id']
                self.db[chunk_id] = {
                    'embedding': embedding,
                    'metadata': chunk,
                    'text': chunk.get('source_code', '')
                }
                # Keep metadata for quick access
                self.chunks_metadata[chunk_id] = chunk

            return True
        except Exception as e:
            print(f"Error adding chunks: {e}")
            return False

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Search for similar code chunks using semantic similarity

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of top-k similar chunks with metadata
        """
        if not self.db:
            return []

        try:
            # Calculate cosine similarity
            results = []
            for chunk_id, data in self.db.items():
                similarity = self._cosine_similarity(
                    query_embedding,
                    data['embedding']
                )
                results.append({
                    'id': chunk_id,
                    'similarity': similarity,
                    'metadata': data['metadata'],
                    'text': data['text']
                })

            # Sort by similarity and return top-k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def clear(self):
        """Clear all data from database"""
        self.db = {}
        self.chunks_metadata = {}


# Global database instance
_vector_db = None


def get_vector_db() -> VectorDatabase:
    """Get or create global vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabase()
        _vector_db.initialize()
    return _vector_db


def reset_vector_db():
    """Reset vector database for new repository"""
    global _vector_db
    if _vector_db:
        _vector_db.clear()
    else:
        _vector_db = VectorDatabase()
        _vector_db.initialize()
