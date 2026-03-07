"""
Code Documentation Assistant - Streamlit Frontend
Upload GitHub repos and ask questions about code with AI
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from code_parser import parse_repository, chunk_for_storage
from embeddings import embed_texts
from vector_db import get_vector_db, reset_vector_db
from rag_handler import get_rag_handler
from utils import clone_repository, find_python_files, cleanup_repo
from cache_manager import get_cache

# Page config
st.set_page_config(
    page_title="Code Documentation Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        color: #155724;
        border-left: 4px solid #155724;
    }
    .error-box {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        color: #721c24;
        border-left: 4px solid #721c24;
    }
    .info-box {
        background: #cfe2ff;
        padding: 1rem;
        border-radius: 5px;
        color: #084298;
        border-left: 4px solid #084298;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-gradient">
    <h1>🔍 Code Documentation Assistant</h1>
    <p>Upload a GitHub repository and ask questions about your code using AI</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'repo_analyzed' not in st.session_state:
    st.session_state.repo_analyzed = False
if 'chunks_count' not in st.session_state:
    st.session_count = 0

# Sidebar
with st.sidebar:
    st.header("📤 Step 1: Analyze Repository")

    # Python focus messaging
    st.info("""
    **🎯 Currently Optimized For: Python Codebases**

    This system uses AST-based method-level parsing for superior semantic granularity.
    Python's Abstract Syntax Tree enables precise code boundaries that other languages cannot match.
    """)

    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/user/repo.git",
        help="Enter a public GitHub repository URL (Python repos recommended)"
    )

    if st.button("🚀 Analyze Repository", use_container_width=True, type="primary"):
        if not repo_url.strip():
            st.error("❌ Please enter a repository URL")
        else:
            progress_container = st.empty()
            status_container = st.empty()

            try:
                # CHECK CACHE FIRST (600x faster!)
                cache = get_cache()

                # Show cache checking status
                progress_container.info("🔍 Checking for cached analysis...")

                # Flag to track if we need to re-analyze
                cache_valid = False

                # Check if cache exists
                if cache.is_cached(repo_url):
                    progress_container.info("📋 Found cache file. Validating freshness...")

                    # Check if cache is valid (TTL + commit hash)
                    if cache.is_cache_valid(repo_url):  # FIXED: Check validity, not just existence
                        cache_valid = True
                        progress_container.info("✅ Cache is fresh! Loading from cache (instant analysis)...")
                        cached_data = cache.load_analysis(repo_url)
                        if cached_data:
                            chunks_dict, embeddings = cached_data
                            progress_container.info("💾 Restoring to vector database...")
                            reset_vector_db()
                            vector_db = get_vector_db()
                            success = vector_db.add_chunks(chunks_dict, embeddings)

                            if success:
                                st.session_state.repo_analyzed = True
                                st.session_state.chunks_count = len(chunks_dict)
                                progress_container.empty()
                                status_container.markdown(
                                    f'<div class="success-box">'
                                    f'✅ Cache is Fresh! Loaded {len(chunks_dict)} code chunks instantly!'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                            else:
                                status_container.error("❌ Failed to restore from cache")
                    else:
                        # Cache exists but is invalid (expired or changed)
                        progress_container.warning("⚠️ Cache is stale! Repository changed or TTL expired. Re-analyzing...")

                # If cache not valid, do full analysis
                if not cache_valid:
                    # Clone repo
                    progress_container.info("📥 Cloning repository...")
                    repo_path, error = clone_repository(repo_url)

                    if error:
                        status_container.error(f"❌ Error: {error}")
                    else:
                        # Find Python files
                        progress_container.info("🔍 Finding Python files...")
                        python_files = find_python_files(repo_path)

                        if not python_files:
                            status_container.error("❌ No Python files found in repository")
                            cleanup_repo(repo_path)
                        else:
                            # Parse repository
                            progress_container.info(f"📝 Parsing {len(python_files)} files...")
                            chunks = parse_repository(repo_path, python_files)

                            if not chunks:
                                status_container.error("❌ Could not extract code chunks")
                                cleanup_repo(repo_path)
                            else:
                                # Create embeddings
                                progress_container.info("🧠 Generating embeddings...")
                                chunks_dict = [chunk_for_storage(chunk) for chunk in chunks]
                                texts = [c['combined_text'] for c in chunks_dict]
                                embeddings = embed_texts(texts)

                                # Filter valid pairs
                                valid_pairs = [
                                    (chunk, emb) for chunk, emb in zip(chunks_dict, embeddings)
                                    if emb is not None
                                ]

                                if not valid_pairs:
                                    status_container.error("❌ Could not generate embeddings")
                                else:
                                    # Index in vector DB
                                    progress_container.info("💾 Indexing in vector database...")
                                    reset_vector_db()
                                    vector_db = get_vector_db()
                                    valid_chunks = [p[0] for p in valid_pairs]
                                    valid_embeddings = [p[1] for p in valid_pairs]
                                    success = vector_db.add_chunks(valid_chunks, valid_embeddings)

                                    if success:
                                        # SAVE TO CACHE for future analysis
                                        progress_container.info("💾 Saving to cache...")
                                        cache.save_analysis(repo_url, valid_chunks, valid_embeddings)

                                        st.session_state.repo_analyzed = True
                                        st.session_state.chunks_count = len(valid_chunks)
                                        progress_container.empty()
                                        status_container.markdown(
                                            f'<div class="success-box">'
                                            f'✅ Successfully analyzed {len(valid_chunks)} code chunks!'
                                            f'<br>💾 Cached for future use (instant re-analysis)'
                                            f'</div>',
                                            unsafe_allow_html=True
                                        )
                                    else:
                                        status_container.error("❌ Failed to index chunks")

                                cleanup_repo(repo_path)

            except Exception as e:
                status_container.error(f"❌ Error: {str(e)}")

# Main content
if st.session_state.repo_analyzed:
    st.header("❓ Step 2: Ask Questions")

    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input(
            "Ask about your code",
            placeholder="e.g., How does authentication work?",
            help="Ask in natural language"
        )
    with col2:
        search = st.button("🔍 Search", use_container_width=True, type="primary")

    if search and question.strip():
        try:
            # Embed question
            question_embedding = embed_texts([question])[0]

            if question_embedding is None:
                st.error("❌ Could not embed question")
            else:
                # Search vector DB
                vector_db = get_vector_db()
                results = vector_db.search(question_embedding, top_k=20)

                if not results:
                    st.info("ℹ️ No relevant code found for your question")
                else:
                    # Generate answer with RAG
                    with st.spinner("🤖 Generating answer..."):
                        rag_handler = get_rag_handler()
                        answer = rag_handler.generate_answer(question, results)

                    # Display answer
                    st.subheader("💡 Answer")
                    st.markdown(f"> {answer}")

                    # Display sources
                    if results:
                        st.subheader("📚 Source Code")
                        for i, result in enumerate(results[:3], 1):
                            metadata = result.get('metadata', {})
                            with st.expander(
                                f"Source {i}: {metadata.get('file', 'Unknown')} "
                                f"(Lines {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')})"
                            ):
                                st.code(
                                    result.get('text', ''),
                                    language="python"
                                )
                                st.write(f"**Function/Class**: {metadata.get('name', 'Unknown')}")
                                st.write(f"**Relevance**: {result.get('similarity', 0):.1%}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

else:
    # Landing page
    st.markdown("""
    ## System Design

    **Current Focus: Python Codebases**

    This system is architecturally optimized for Python through AST-based method-level extraction.
    This enables superior semantic granularity compared to class-level or line-level chunking.

    ### Why This Approach?
    - **AST Parsing**: Python's Abstract Syntax Tree provides exact method boundaries
    - **Semantic Specificity**: Each method is an independent semantic unit
    - **Endee Optimization**: Vector search performs optimally with this granularity
    - **Future Ready**: Architecture designed to extend to JavaScript, Go, Java

    ### How It Works

    1. **Analyze**: Paste a Python GitHub repository URL
    2. **Parse**: Extract methods using Python AST (not classes or files)
    3. **Embed**: Convert to semantic vectors via Sentence-Transformers
    4. **Index**: Store in Endee Vector Database for semantic search
    5. **Query**: Ask questions in natural language
    6. **Explain**: Get AI-powered answers with full code context (no truncation)

    ### Key Features
    - 🔍 **Semantic Search**: Find code by MEANING via Endee, not keywords
    - 📦 **Method-Level Chunking**: Superior semantic specificity
    - 🤖 **Full-Context RAG**: Complete code sent to LLM (no truncation)
    - ⚡ **Smart Caching**: 600x faster on repeated repos
    - 💾 **Persistent Storage**: Data survives restarts

    ### Technology Stack
    - **Vector DB**: Endee (core semantic engine)
    - **Embeddings**: Sentence-Transformers (384-dimensional)
    - **LLM**: Gemini 2.5 Flash (RAG generation)
    - **Parser**: Python AST (method extraction)
    - **Storage**: Pickle + JSON (persistent indexes)
    - **Frontend**: Streamlit

    ---

    **Get started**: Enter a Python GitHub repo URL in the sidebar! →
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("Made for **Endee.io Internship**")
with col2:
    st.markdown("[GitHub](https://github.com/AyushMishra1006/endee-code-assistant)")
with col3:
    st.markdown("By **Ayush Mishra**")
