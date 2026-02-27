"""
Code Parser - Extract functions and classes from Python code using AST
"""
import ast
import os
from typing import NamedTuple, Optional


class CodeChunk(NamedTuple):
    """Represents a chunk of code (function or class)"""
    id: str
    file_path: str
    name: str
    type: str  # "function" or "class"
    start_line: int
    end_line: int
    docstring: str
    source_code: str


def read_file_with_encoding(file_path: str) -> Optional[str]:
    """Read file with error handling for encoding"""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return None


def extract_docstring(node: ast.AST) -> str:
    """Extract docstring from AST node"""
    docstring = ast.get_docstring(node)
    return docstring if docstring else ""


def extract_chunks(file_path: str) -> list[CodeChunk]:
    """Extract all functions and classes from a Python file"""
    chunks = []

    # Read file
    content = read_file_with_encoding(file_path)
    if content is None:
        return chunks

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Skip files with syntax errors
        return chunks

    # Extract line numbers for each node
    source_lines = content.split('\n')
    relative_path = file_path.replace('\\', '/')

    # Process module-level functions and classes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            # Skip nested (inner) functions/classes for now - only get top-level
            if not hasattr(node, 'parent'):
                # Only include if it's at module level
                if node in tree.body:
                    chunk_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                    start_line = node.lineno
                    end_line = node.end_lineno if node.end_lineno else start_line

                    # Extract source code
                    source_code = '\n'.join(source_lines[start_line - 1:end_line])

                    # Limit chunk size
                    if len(source_code) > 5000:  # Max 5000 chars per chunk
                        source_code = source_code[:5000] + "..."

                    # Create chunk
                    chunk = CodeChunk(
                        id=f"{relative_path}_{node.name}_{start_line}",
                        file_path=relative_path,
                        name=node.name,
                        type=chunk_type,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=extract_docstring(node),
                        source_code=source_code
                    )
                    chunks.append(chunk)

    return chunks


def parse_repository(root_path: str, python_files: list[str]) -> list[CodeChunk]:
    """Parse all Python files and extract code chunks"""
    all_chunks = []

    for file_path in python_files:
        chunks = extract_chunks(file_path)
        all_chunks.extend(chunks)

    return all_chunks


def chunk_for_storage(chunk: CodeChunk) -> dict:
    """Convert CodeChunk to dictionary for storage"""
    return {
        "id": chunk.id,
        "file_path": chunk.file_path,
        "name": chunk.name,
        "type": chunk.type,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "docstring": chunk.docstring,
        "source_code": chunk.source_code,
        "combined_text": f"{chunk.name} {chunk.docstring} {chunk.source_code}"
    }
