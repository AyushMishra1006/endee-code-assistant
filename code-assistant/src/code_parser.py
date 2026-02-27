"""
Code Parser - Extract functions and classes from Python code using AST
"""
import ast
import os
from typing import NamedTuple, Optional


class CodeChunk(NamedTuple):
    """Represents a chunk of code (function or method)"""
    id: str
    file_path: str
    name: str
    type: str  # "function" or "method"
    start_line: int
    end_line: int
    docstring: str
    source_code: str
    class_name: str = ""  # Empty for module-level functions, set for methods


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
    """Extract all functions and methods from a Python file - METHOD LEVEL GRANULARITY"""
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

    # Process module-level items
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # Module-level function
            chunk = _create_chunk(node, relative_path, source_lines, class_name="")
            if chunk:
                chunks.append(chunk)

        elif isinstance(node, ast.ClassDef):
            # Class-level methods (extract each method separately)
            class_name = node.name

            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    chunk = _create_chunk(method, relative_path, source_lines, class_name=class_name)
                    if chunk:
                        chunks.append(chunk)

    return chunks


def _create_chunk(node: ast.FunctionDef, file_path: str, source_lines: list, class_name: str = "") -> Optional[CodeChunk]:
    """Create a CodeChunk from a function/method node"""
    start_line = node.lineno
    end_line = node.end_lineno if node.end_lineno else start_line

    # Extract source code
    source_code = '\n'.join(source_lines[start_line - 1:end_line])

    # Limit chunk size (truncate if too large)
    if len(source_code) > 5000:
        source_code = source_code[:5000] + "\n... [truncated]"

    # Determine chunk type
    chunk_type = "method" if class_name else "function"

    # Create unique ID
    if class_name:
        chunk_id = f"{file_path}_{class_name}_{node.name}_{start_line}"
    else:
        chunk_id = f"{file_path}_{node.name}_{start_line}"

    # Create chunk
    chunk = CodeChunk(
        id=chunk_id,
        file_path=file_path,
        name=node.name,
        type=chunk_type,
        start_line=start_line,
        end_line=end_line,
        docstring=extract_docstring(node),
        source_code=source_code,
        class_name=class_name
    )

    return chunk


def parse_repository(root_path: str, python_files: list[str]) -> list[CodeChunk]:
    """Parse all Python files and extract code chunks"""
    all_chunks = []

    for file_path in python_files:
        chunks = extract_chunks(file_path)
        all_chunks.extend(chunks)

    return all_chunks


def chunk_for_storage(chunk: CodeChunk) -> dict:
    """Convert CodeChunk to dictionary for storage with class context for semantic search"""

    # Build combined text with class context for better semantic search
    if chunk.class_name:
        # Method: include class name for context
        combined_text = f"{chunk.class_name}.{chunk.name} {chunk.docstring}\n{chunk.source_code}"
    else:
        # Module-level function
        combined_text = f"{chunk.name} {chunk.docstring}\n{chunk.source_code}"

    return {
        "id": chunk.id,
        "file_path": chunk.file_path,
        "name": chunk.name,
        "class_name": chunk.class_name,
        "type": chunk.type,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "docstring": chunk.docstring,
        "source_code": chunk.source_code,
        "combined_text": combined_text
    }
