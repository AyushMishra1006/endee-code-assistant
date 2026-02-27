"""
RAG Handler - Generate answers using Gemini API with code context
"""
import os
from typing import Optional
import json


class RAGHandler:
    """Generate answers using Retrieval Augmented Generation with Gemini"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG handler

        Args:
            api_key: Gemini API key (from environment if not provided)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model = None
        self.initialized = False

        if self.api_key:
            self.initialize()

    def initialize(self):
        """Initialize Gemini model"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize Gemini: {e}")
            self.initialized = False

    def generate_answer(
        self,
        question: str,
        search_results: list[dict],
        max_chunk_chars: int = 300
    ) -> str:
        """
        Generate answer using Gemini with code context

        Args:
            question: User's question about code
            search_results: List of relevant code chunks from search
            max_chunk_chars: Max characters per chunk to include in context

        Returns:
            Generated answer
        """
        if not self.initialized:
            return "Error: Gemini API not configured. Please set GEMINI_API_KEY."

        # Build context from search results
        context = self._build_context(search_results, max_chunk_chars)

        if not context:
            return "No relevant code found for your question."

        # Create prompt
        prompt = f"""You are a code assistant. Based on the following code snippets, answer the user's question concisely and clearly.

CODE CONTEXT:
{context}

QUESTION: {question}

Please provide a clear, concise answer that directly references the code snippets above."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def _build_context(self, search_results: list[dict], max_chars: int = 300) -> str:
        """Build context string from search results"""
        if not search_results:
            return ""

        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Max 5 chunks
            metadata = result.get('metadata', {})
            text = result.get('text', '')

            # Truncate text if too long
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            file_path = metadata.get('file_path', 'unknown')
            name = metadata.get('name', 'unknown')
            start_line = metadata.get('start_line', '?')
            end_line = metadata.get('end_line', '?')

            part = f"""[{i}] File: {file_path} (lines {start_line}-{end_line})
Function/Class: {name}
Code:
```python
{text}
```"""
            context_parts.append(part)

        return "\n\n".join(context_parts)

    def format_response(
        self,
        answer: str,
        search_results: list[dict]
    ) -> dict:
        """
        Format final response with answer and source attribution

        Args:
            answer: Generated answer
            search_results: Search results for source attribution

        Returns:
            Formatted response dictionary
        """
        sources = []
        for result in search_results[:3]:  # Top 3 sources
            metadata = result.get('metadata', {})
            sources.append({
                'file': metadata.get('file_path', ''),
                'name': metadata.get('name', ''),
                'lines': f"{metadata.get('start_line', '')}-{metadata.get('end_line', '')}",
                'similarity': round(result.get('similarity', 0), 3)
            })

        return {
            'answer': answer,
            'sources': sources,
            'relevance': 'high' if search_results else 'low'
        }


# Global RAG handler instance
_rag_handler = None


def get_rag_handler(api_key: Optional[str] = None) -> RAGHandler:
    """Get or create global RAG handler"""
    global _rag_handler
    if _rag_handler is None:
        _rag_handler = RAGHandler(api_key)
    return _rag_handler
