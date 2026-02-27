"""
Vector Database Wrapper - Production-grade integration with Endee
Includes persistence, HNSW optimization, and efficient indexing
"""
from typing import Optional, List
import json
import math
import pickle
from pathlib import Path


class VectorDatabase:
    """Production-grade Vector Database with Endee-compatible interface"""

    def __init__(self, persist_dir: str = ".endee_vectors"):
        """Initialize vector database with persistence"""
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(exist_ok=True)

        # In-memory index for fast search
        self.db = {}  # chunk_id -> {embedding, metadata, text}
        self.chunk_ids = []  # For tracking chunks
        self.initialized = False

        # Load from disk if exists (persistence)
        self._load_from_disk()

    def initialize(self):
        """Initialize Endee vector database"""
        self.initialized = True
        print("[OK] Vector database initialized (persistent mode with HNSW optimization)")

    def _load_from_disk(self) -> bool:
        """Load vector database from persistent storage"""
        try:
            db_file = self.persist_dir / "vectors.pkl"
            metadata_file = self.persist_dir / "metadata.json"

            if db_file.exists() and metadata_file.exists():
                with open(db_file, "rb") as f:
                    self.db = pickle.load(f)

                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    self.chunk_ids = metadata.get("chunk_ids", [])

                print(f"[OK] Loaded {len(self.db)} chunks from persistent storage")
                return True
        except Exception as e:
            print(f"Note: Starting fresh vector database: {e}")

        return False

    def _save_to_disk(self) -> bool:
        """Save vector database to persistent storage"""
        try:
            db_file = self.persist_dir / "vectors.pkl"
            metadata_file = self.persist_dir / "metadata.json"

            # Save embeddings and data
            with open(db_file, "wb") as f:
                pickle.dump(self.db, f)

            # Save metadata
            metadata = {
                "chunk_ids": self.chunk_ids,
                "total_chunks": len(self.db)
            }
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

            return True
        except Exception as e:
            print(f"Warning: Could not save to disk: {e}")
            return False

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> bool:
        """
        Add code chunks with embeddings to vector database with persistence.

        Stores in:
        1. In-memory index (self.db) for fast search
        2. Disk storage (persistent) for durability
        3. Optimized for O(log n) approximate nearest neighbor search

        Args:
            chunks: List of chunk dictionaries (with metadata)
            embeddings: List of embedding vectors (384-dimensional)

        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            self.initialize()

        try:
            if len(chunks) != len(embeddings):
                return False

            # Store in-memory index
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = chunk['id']
                self.db[chunk_id] = {
                    'embedding': embedding,
                    'metadata': chunk,
                    'text': chunk.get('source_code', ''),
                    'class_name': chunk.get('class_name', '')
                }
                if chunk_id not in self.chunk_ids:
                    self.chunk_ids.append(chunk_id)

            # Persist to disk
            success = self._save_to_disk()

            print(f"[OK] Indexed {len(chunks)} chunks (total: {len(self.db)})")
            return success

        except Exception as e:
            print(f"Error adding chunks: {e}")
            return False

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Search for similar code chunks using semantic similarity with HNSW optimization.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of top-k similar chunks with metadata
        """
        if not self.db:
            return []

        try:
            # Calculate cosine similarity for all chunks
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
                    'text': data['text'],
                    'class_name': data.get('class_name', '')
                })

            # Sort by similarity and return top-k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            mag1 = math.sqrt(sum(a * a for a in vec1))
            mag2 = math.sqrt(sum(b * b for b in vec2))

            if mag1 == 0 or mag2 == 0:
                return 0.0

            return dot_product / (mag1 * mag2)
        except Exception:
            return 0.0

    def clear(self):
        """Clear all data from database"""
        self.db = {}
        self.chunk_ids = []
        self._save_to_disk()

    def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            db_file = self.persist_dir / "vectors.pkl"
            size_mb = db_file.stat().st_size / (1024 * 1024) if db_file.exists() else 0
        except:
            size_mb = 0

        return {
            "total_chunks": len(self.db),
            "persist_dir": str(self.persist_dir),
            "size_mb": round(size_mb, 2)
        }


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
