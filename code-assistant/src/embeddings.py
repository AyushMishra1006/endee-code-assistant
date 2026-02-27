"""
Embeddings Generator - Create embeddings for code chunks
Uses sentence-transformers for efficient, free embeddings
"""
from typing import Optional
import numpy as np


class EmbeddingsGenerator:
    """Generate embeddings for code chunks using sentence-transformers"""

    def __init__(self):
        """Initialize embeddings generator"""
        self.model = None
        self.dimension = None

    def initialize(self):
        """Lazy load model to avoid import issues"""
        try:
            from sentence_transformers import SentenceTransformer
            # Using a small, fast model suitable for code
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384  # Model dimension
        except Exception as e:
            print(f"Warning: Could not load embeddings model: {e}")
            self.model = None

    def embed_text(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if model not available
        """
        if self.model is None:
            self.initialize()

        if self.model is None:
            # Fallback: return random embedding (for testing)
            return [0.1] * 384

        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        except Exception as e:
            print(f"Warning: Could not embed text: {e}")
            return None

    def embed_texts(self, texts: list[str]) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.initialize()

        if self.model is None:
            # Fallback
            return [[0.1] * 384 for _ in texts]

        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return [e.tolist() if hasattr(e, 'tolist') else e for e in embeddings]
        except Exception as e:
            print(f"Warning: Could not embed texts: {e}")
            return [None] * len(texts)


# Global embeddings generator
_embeddings_gen = None


def get_embeddings_generator() -> EmbeddingsGenerator:
    """Get or create global embeddings generator"""
    global _embeddings_gen
    if _embeddings_gen is None:
        _embeddings_gen = EmbeddingsGenerator()
        _embeddings_gen.initialize()
    return _embeddings_gen


def embed_text(text: str) -> Optional[list[float]]:
    """Convenience function to embed a single text"""
    return get_embeddings_generator().embed_text(text)


def embed_texts(texts: list[str]) -> list[Optional[list[float]]]:
    """Convenience function to embed multiple texts"""
    return get_embeddings_generator().embed_texts(texts)
