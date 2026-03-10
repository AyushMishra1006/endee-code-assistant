"""
Vector Database Wrapper - Using Endee Vector Database
Provides persistent, high-performance vector storage and semantic search
"""
from typing import Optional, List
import time


class VectorDatabase:
    """Endee-based Vector Database with production-grade interface"""

    def __init__(self, endee_url: str = "http://localhost:8080"):
        """
        Initialize connection to Endee vector database

        Args:
            endee_url: URL where Endee server is running
        """
        self.endee_url = endee_url
        self.index_name = "code_chunks"
        self.client = None
        self.index = None
        self.initialized = False

        self._connect_to_endee()

    def _connect_to_endee(self):
        """Connect to Endee server"""
        try:
            from endee import Endee
            self.client = Endee()  # Default connects to localhost:8080
            self.initialized = True
            print("[OK] Connected to Endee vector database")
        except ImportError:
            print("[ERROR] Endee SDK not installed. Run: pip install endee")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to connect to Endee: {e}")
            print("[INFO] Make sure Endee server is running: docker-compose up -d")
            raise

    def initialize(self):
        """Initialize Endee index for code chunks"""
        if not self.initialized:
            raise RuntimeError("Not connected to Endee. Check if server is running.")

        try:
            # Create or get the index
            self.client.create_index(
                name=self.index_name,
                dimension=384,  # Sentence-Transformers output dimension
                space_type="cosine",  # Cosine similarity for semantic search
                precision="float32"  # Full precision for best accuracy
            )
            print("[OK] Endee index initialized (384-dim, cosine space, INT8 precision)")
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e):
                print("[OK] Endee index already exists")
            else:
                raise

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> bool:
        """
        Add code chunks with embeddings to Endee database

        Args:
            chunks: List of chunk dictionaries with metadata
            embeddings: List of embedding vectors (384-dimensional)

        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            print("[ERROR] Endee not initialized")
            return False

        if len(chunks) != len(embeddings):
            print(f"[ERROR] Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")
            return False

        try:
            self.initialize()  # Ensure index exists
            index = self.client.get_index(self.index_name)

            # Prepare vectors for Endee
            vectors_to_upsert = []
            for chunk, embedding in zip(chunks, embeddings):
                vectors_to_upsert.append({
                    "id": chunk['id'],
                    "vector": embedding,
                    "meta": {
                        "file_path": chunk['file_path'],
                        "name": chunk['name'],
                        "class_name": chunk.get('class_name', ''),
                        "type": chunk.get('type', 'function'),
                        "start_line": chunk.get('start_line', 0),
                        "end_line": chunk.get('end_line', 0),
                        "docstring": chunk.get('docstring', ''),
                        "source_code": chunk.get('source_code', '')
                    }
                })

            # Upsert to Endee (insert or update)
            index.upsert(vectors_to_upsert)
            print(f"[OK] Indexed {len(chunks)} chunks in Endee (total in index: {len(vectors_to_upsert)})")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to add chunks to Endee: {e}")
            return False

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Search for similar code chunks using Endee

        Args:
            query_embedding: Query vector (384-dimensional)
            top_k: Number of top results to return

        Returns:
            List of similar chunks with metadata and similarity scores
        """
        if not self.initialized:
            print("[ERROR] Endee not initialized")
            return []

        if not query_embedding or len(query_embedding) != 384:
            print("[ERROR] Query embedding must be 384-dimensional")
            return []

        try:
            index = self.client.get_index(self.index_name)

            # Search in Endee (returns results ordered by similarity)
            results = index.query(
                vector=query_embedding,
                top_k=top_k
            )

            # Format results to match expected interface
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result['id'],
                    'similarity': result['similarity'],  # Cosine similarity score (0-1)
                    'metadata': result['meta'],
                    'text': result['meta'].get('source_code', ''),
                    'class_name': result['meta'].get('class_name', '')
                })

            return formatted_results

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def clear(self):
        """Clear all vectors from the index"""
        try:
            if self.initialized:
                self.client.delete_index(self.index_name)
                print("[OK] Cleared Endee index")
                self.initialize()  # Recreate empty index
        except Exception as e:
            print(f"[WARNING] Failed to clear index: {e}")

    def get_stats(self) -> dict:
        """Get database statistics"""
        try:
            if self.initialized:
                index = self.client.get_index(self.index_name)
                # Endee SDK doesn't expose vector count directly
                # Return basic info about the index
                return {
                    "index_name": self.index_name,
                    "database": "Endee",
                    "dimension": 384,
                    "space_type": "cosine",
                    "status": "connected"
                }
        except Exception as e:
            print(f"[WARNING] Could not get stats: {e}")

        return {
            "index_name": self.index_name,
            "database": "Endee",
            "status": "error"
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
