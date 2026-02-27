# CODE DOCUMENTATION ASSISTANT - DESIGN DOCUMENT

**Project Status**: DESIGN PHASE (Locked for Review)
**Repository**: https://github.com/AyushMishra1006/endee-code-assistant
**Date**: Feb 27, 2026
**Timeline**: Complete in ONE sitting (Est. 5-6 hours)

---

## 📋 PROJECT OVERVIEW

**Name**: Code Documentation Assistant
**Elevator Pitch**: Upload any GitHub repository → Semantic search through code → RAG-powered answers about implementation details

**Problem Solved**:
- Developers struggle to understand unfamiliar codebases
- Grepping through code is inefficient
- Need semantic understanding, not just keyword matching
- Current docs are often incomplete

**Solution**:
- Intelligent code indexing with Endee (vector DB)
- Natural language queries ("How does authentication work?")
- Returns relevant code snippets + AI-generated explanations

---

## 🎯 SCOPE DEFINITION

### ✅ IN SCOPE (What We Build)

#### Core Features
1. **GitHub Repository Input**
   - User provides GitHub repo URL
   - System clones repo automatically
   - Support public repos only

2. **Code Parsing & Indexing**
   - Parse Python files (.py)
   - Intelligent chunking: function/class level
   - Extract: function names, docstrings, type hints, implementation
   - Store metadata: file path, line numbers

3. **Semantic Search with Endee**
   - Index code embeddings in Endee vector DB
   - Search by natural language queries
   - Retrieve top-5 most relevant code chunks

4. **RAG-Powered Answers**
   - Use Gemini 2.5 Flash for answer generation
   - Send relevant code + user question to LLM
   - Generate clear explanations

5. **Web UI**
   - Simple, clean interface
   - Input: GitHub repo URL
   - Process status: (cloning → parsing → indexing → ready)
   - Query: Natural language questions
   - Output: Answers + source code + line numbers

6. **Deployment**
   - Deploy to Hugging Face Spaces
   - Live, shareable URL

### ❌ OUT OF SCOPE (What We DON'T Build)

- ❌ Multi-language support (Python only)
- ❌ Dependency graph visualization
- ❌ Code refactoring suggestions
- ❌ Performance optimization analysis
- ❌ User authentication / multiple users
- ❌ Database persistence (ephemeral is OK)
- ❌ Real-time collaboration
- ❌ IDE plugins / CLI tools
- ❌ Test generation
- ❌ Advanced visualizations (keep UI simple)

---

## 🛠️ TECHNICAL STACK (FINAL)

### Backend
```
FastAPI                    # Web framework (async, modern)
Python 3.10+               # Runtime
google-generativeai        # Gemini API (RAG)
sentence-transformers      # Free embeddings (local, no API calls)
ast (built-in module)      # Code parsing (SAFER than tree-sitter)
gitpython                  # Clone repos
endee                      # Vector database (forked)
```

### Frontend
```
HTML5 / CSS3               # UI layout
JavaScript (Vanilla)       # Interactivity
Highlight.js               # Code syntax highlighting
Fetch API                  # Backend communication
```

### Deployment
```
Hugging Face Spaces        # Free hosting (Docker type)
Docker                     # Container for reliable HF deployment
GitHub                     # Version control
```

### NOT Used
- ❌ Claude API (using Gemini instead - free)
- ❌ Flask (using FastAPI - faster, async)
- ❌ Tree-sitter (using Python ast - built-in, reliable)
- ❌ React/Vue (vanilla JS - keep it simple)
- ❌ PostgreSQL (ephemeral storage OK for MVP)

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      USER (Web Browser)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ GitHub Repo URL
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │ GitHub Cloning   │    │ Code Parsing     │               │
│  │ (GitPython)      │───▶│ (Tree-sitter)    │               │
│  └──────────────────┘    └────────┬─────────┘               │
│                                   │                          │
│                          ┌────────▼─────────┐               │
│                          │ Code Chunking    │               │
│                          │ (Func/Class)     │               │
│                          └────────┬─────────┘               │
│                                   │                          │
│                   ┌───────────────▼───────────────┐          │
│                   │ Embedding Generation         │          │
│                   │ (Sentence-Transformers)      │          │
│                   └───────────────┬───────────────┘          │
│                                   │                          │
│                    ┌──────────────▼──────────────┐           │
│                    │  ENDEE VECTOR DB INDEXING  │           │
│                    │  (Store embeddings + meta)  │           │
│                    └──────────────┬──────────────┘           │
│                                   │                          │
└───────────────────────────────────┼───────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   USER QUERY (Natural Lang)    │
                    └───────────────┬────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────┐
│                    QUERY PROCESSING                            │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │ Query Embedding  │    │ Endee Search     │                 │
│  │ (Same model)     │───▶│ (Semantic Search)│                 │
│  └──────────────────┘    └────────┬─────────┘                 │
│                                   │ Top-5 results             │
│                          ┌────────▼─────────┐                 │
│                          │  Context Building │                 │
│                          │ (Code snippets)   │                 │
│                          └────────┬─────────┘                 │
│                                   │                           │
│                   ┌───────────────▼────────────────┐           │
│                   │  GEMINI 2.5 FLASH (RAG)       │           │
│                   │ Generate Answer + Explanation │           │
│                   └───────────────┬────────────────┘           │
│                                   │                           │
└───────────────────────────────────┼───────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   RESPONSE TO USER             │
                    │ - Answer                       │
                    │ - Source Code Snippets         │
                    │ - File Path + Line Numbers     │
                    └───────────────────────────────┘
```

---

## 🔄 HOW ENDEE IS USED (CORE)

### Step 1: Indexing Phase
```python
from endee import Endee

# Initialize Endee vector database
vector_db = Endee()

# Add code chunks with embeddings
vector_db.add(
    ids=["chunk_1", "chunk_2", ...],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    metadata=[
        {"file": "auth.py", "start_line": 45, "end_line": 67, "function": "login"},
        {"file": "auth.py", "start_line": 68, "end_line": 90, "function": "logout"},
        ...
    ]
)
```

### Step 2: Query Phase
```python
# User asks: "How does authentication work?"
question = "How does authentication work?"
question_embedding = embed_text(question)  # Same model as training

# Search Endee
results = vector_db.search(
    query=question_embedding,
    top_k=5,
    return_metadata=True
)

# Results contain:
# - Chunk ID
# - Similarity score
# - Metadata (file, line numbers, function name)
# - Original code text (retrieved from storage)
```

### Step 3: RAG Phase
```python
# Build context from Endee results
context = "\n".join([f"File: {r['metadata']['file']}\n{r['text']}"
                      for r in results])

# Generate answer with Gemini
prompt = f"Based on this code:\n{context}\n\nAnswer: {question}"
answer = gemini_model.generate_content(prompt).text
```

**Endee is NOT optional** - it's the core semantic search engine.

---

## 📊 DATA FLOW EXAMPLE

**Input**: GitHub repo URL
**Example**: https://github.com/pallets/flask

**Processing**:
```
1. Clone repo locally (tmp directory)
2. Find all .py files (recursive)
3. Parse each file with tree-sitter
4. Extract functions/classes:
   - Function: authenticate_user(username, password)
   - Docstring: "Validates user credentials"
   - Code: 15 lines
   - File: src/auth.py, lines 45-60

5. Create embeddings using sentence-transformers
   - Same embedding for similar code logic
   - Different embeddings for different purposes

6. Store in Endee:
   ID: "flask_auth_authenticate_user_v1"
   Embedding: [0.234, -0.123, ..., 0.456]
   Metadata: {file: "src/auth.py", lines: "45-60", ...}

7. Ready for queries
```

**Query**: "How do I authenticate users?"
```
1. Embed query (same model)
2. Search Endee (semantic match)
3. Get top-5 results with file/line info
4. Send to Gemini: "Here's the code... explain it"
5. Return answer + source code
```

---

## 📁 PROJECT STRUCTURE

```
endee-code-assistant/
│
├── endee/                          # Forked Endee (original code)
│   ├── src/
│   ├── tests/
│   └── ... (all Endee files)
│
├── src/                            # Our Code Assistant Implementation
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + routes
│   ├── code_parser.py              # Parse code, extract functions
│   ├── embeddings.py               # Create embeddings (sentence-transformers)
│   ├── vector_db.py                # Endee integration
│   ├── rag_handler.py              # Gemini RAG logic
│   └── utils.py                    # Helpers (repo cloning, etc)
│
├── frontend/                       # Web UI
│   ├── index.html                  # Main page
│   ├── style.css                   # Styling
│   └── app.js                      # Frontend logic
│
├── requirements.txt                # Dependencies
├── .gitignore
├── README.md                       # Project documentation
└── DESIGN_DOCUMENT.md             # This file (locked design)
```

---

## ⏱️ IMPLEMENTATION TIMELINE (REALISTIC - One Sitting)

### Phase 1: Setup (25 mins)
- [ ] Clone local copy of fork
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Test Endee installation
- [ ] Test Python ast module (safe fallback)

### Phase 2: Backend Implementation (150 mins)
**Core Logic**:
- [ ] Code parser (Python ast module - built-in, reliable)
  - Extract functions and classes with AST
  - Get line numbers, docstrings, source code
- [ ] Chunking strategy (break at function/class boundaries)
  - Max 500 lines per chunk
  - Include metadata (file, line range)
- [ ] Embedding generator (sentence-transformers - local)
  - Single model for both code & queries
  - Cached embeddings in memory
- [ ] Endee vector DB wrapper
  - Initialize Endee instance
  - Add chunks with embeddings + metadata
  - Search with similarity scoring
  - Handle metadata retrieval

**Infrastructure**:
- [ ] GitHub cloning utility (GitPython)
  - Validate repo URL
  - **Add repo size check: REJECT > 100MB**
  - Clone to /tmp with timeout
- [ ] FastAPI app structure
  - POST /analyze (upload repo)
  - POST /query (ask questions)
  - GET /status (check processing)
  - Error handling for all endpoints
- [ ] Gemini RAG handler
  - Build context from top-5 results
  - **Add chunk truncation: max 300 chars per chunk for RAG**
  - **Add token limit protection**
  - Format answer with source attribution
- [ ] Logging & Error handling
  - Graceful error messages
  - Detailed logs for debugging
  - Timeout protection on long operations

**Buffer for integration issues**: 20 mins built-in

### Phase 3: Frontend Implementation (50 mins)
- [ ] HTML structure
  - Input form for GitHub URL
  - Status display (cloning → parsing → indexing → ready)
  - Query input
  - Results display with code snippets
- [ ] CSS styling (clean, professional)
- [ ] JavaScript
  - Form submission & validation
  - Status polling during indexing
  - Display results with formatting
  - Code syntax highlighting (Highlight.js)
  - Error messages

### Phase 4: Integration & Testing (45 mins)
- [ ] Test end-to-end locally
  - Use small test repo (< 5MB)
  - Verify all components work together
- [ ] Test with real GitHub repo (medium-sized, 10-50MB)
- [ ] Test error cases
  - Repo too large (>100MB)
  - Invalid GitHub URL
  - Network issues
  - Endee failures
- [ ] Performance check
  - Time to index (should be < 5 mins)
  - Query latency (should be < 2 secs)

### Phase 5: Deployment (60 mins)
- [ ] Create Dockerfile for HF Spaces
  - Base: python:3.10-slim
  - Install dependencies
  - Run FastAPI with uvicorn
  - Expose port 7860
- [ ] Push to GitHub
- [ ] Create Hugging Face Space
  - **Type: Docker (NOT default template)**
  - Link to repository
  - Add GEMINI_API_KEY as secret
- [ ] Test deployment
  - Check logs for errors
  - Test live functionality
  - Fix any runtime issues

### Phase 6: Documentation (20 mins)
- [ ] Update README.md with:
  - Project overview & problem statement
  - System design & architecture diagram
  - How Endee is used (explicit)
  - Setup & installation instructions
  - Usage examples
  - Limitations & constraints
  - Design decisions & rationale
- [ ] Add comments to code (key sections)
- [ ] Verify all links work

**Total: ~7.5 hours (realistic with debugging buffer)**

---

## 🛡️ SAFEGUARDS & ERROR HANDLING (CRITICAL)

### Input Validation
```python
# Repo Size Check
MAX_REPO_SIZE = 100 * 1024 * 1024  # 100MB hard limit
if repo_size > MAX_REPO_SIZE:
    raise ValueError(f"Repo too large ({repo_size/1e6:.0f}MB). Max 100MB.")

# URL Validation
if not is_valid_github_url(url):
    raise ValueError("Invalid GitHub URL format")

# Timeout Protection
CLONE_TIMEOUT = 60  # seconds
PARSING_TIMEOUT = 300  # 5 minutes per repo
```

### Data Processing Safeguards
```python
# Chunk Size Limits
MAX_LINES_PER_CHUNK = 500
MAX_CHARS_PER_CHUNK = 5000  # for storage

# RAG Context Truncation
MAX_CHARS_FOR_RAG = 300  # per chunk for Gemini
MAX_CHUNKS_IN_CONTEXT = 5  # never send more than top-5

# Token Limit Protection
GEMINI_MAX_TOKENS = 2000
ESTIMATED_PROMPT_SIZE = 1000
MAX_CONTEXT_SIZE = GEMINI_MAX_TOKENS - ESTIMATED_PROMPT_SIZE
```

### Error Handling Strategy
```python
# All endpoints return clear error messages
{
    "status": "error",
    "error": "Repo too large (450MB). Please use a repo < 100MB",
    "suggestion": "Try with a smaller repo or specific subdirectory"
}

# Never let system crash silently
try-except on:
- Repo cloning
- File parsing
- Embedding generation
- Endee operations
- Gemini API calls
```

### Deployment Safeguards
- Docker container for reliable HF deployment
- Environment variable validation (GEMINI_API_KEY must exist)
- Health check endpoint for monitoring
- Graceful shutdown on errors
- Comprehensive logging

## 🔐 CONSTRAINTS & LIMITATIONS

### Technical Constraints
- **Repo Size**: Max 100MB (enforced, with clear error messages)
- **File Count**: Max 5,000 files (practical for processing)
- **Code Size**: ~500k lines of code max (reasonable limits)
- **Query Time**: <2 seconds (Endee is fast)
- **Processing Time**: 2-5 minutes per repo (depends on size)
- **Chunk Size**: Max 500 lines per chunk (manageable context)
- **RAG Context**: Max 300 chars per chunk (Gemini token protection)

### Language Support
- **Phase 1 (MVP)**: Python only (.py files)
- **Not in scope**: JavaScript, Java, C++, etc.

### Storage & Persistence
- Ephemeral (no persistent DB needed for MVP)
- Vector DB data stored in memory during session
- Cleaned up after each request

---

## 📋 SUCCESS CRITERIA

### MVP Requirements
- ✅ Accept GitHub repo URL
- ✅ Index code with Endee
- ✅ Answer code questions via semantic search
- ✅ Show source code + line numbers
- ✅ Deploy to Hugging Face Spaces
- ✅ Comprehensive README

### Evaluation Criteria (Hiring)
- ✅ Clean system design document
- ✅ Proper Endee integration (core, not peripheral)
- ✅ Working live demo
- ✅ Good code quality & comments
- ✅ Shows technical depth (chunking strategy, ranking, etc.)

---

## 🚨 SCOPE CHANGES PROTOCOL

**If requirements change during implementation:**

1. Document the change here (with timestamp & reason)
2. Assess impact on timeline
3. Update timeline
4. Proceed only if approved

**Changes Log** (to be filled):
- None yet

---

## 📚 DEPENDENCIES (Final List)

```
fastapi==0.109.0
google-generativeai==0.4.0
sentence-transformers==2.2.2
gitpython==3.1.40
tree-sitter==0.21.1
uvicorn==0.27.0
python-dotenv==1.0.0
```

---

## 🎯 KEY DECISIONS & RATIONALE

| Decision | Choice | Reason | Trade-offs |
|----------|--------|--------|-----------|
| **LLM** | Gemini 2.5 Flash | Free, fast, reliable RAG performance | Limited to 12k req/min but enough for demo |
| **Embeddings** | Sentence-transformers | Free, local, no API calls, no costs | Smaller model (6MB), but good enough for code |
| **Backend Framework** | FastAPI | Async, type-safe, modern Python | Slightly steeper learning curve but worth it |
| **Code Parser** | **Python `ast` (not tree-sitter)** | **Built-in, zero dependencies, 100% reliable** | **Can't parse invalid syntax, but that's OK** |
| **Vector DB** | Endee (forked) | Required by project, performant | Learning curve, but well-documented |
| **Frontend** | Vanilla JS | Simple, no build step, no runtime | Less code reuse, but MVP-appropriate |
| **Deployment** | HF Spaces (Docker) | Free, easy, reliable | 30-60 sec startup time |

### Why NOT Tree-sitter?
- Requires C bindings compilation
- Can fail silently on HF Spaces
- Over-engineered for Python-only MVP
- **ast module is production-grade for Python**

### Why Chunk Truncation?
- Gemini has token limits
- Large code chunks = silent failures
- Truncation = guaranteed reliability

### Why Repo Size Validation?
- Prevents system hangs
- Graceful error messages
- Shows production thinking

---

## 🐳 DEPLOYMENT WITH DOCKER (HF Spaces)

### Dockerfile Template
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY main.py .

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Why Docker?
- ✅ Guarantees dependencies install correctly
- ✅ No PATH/environment issues on HF
- ✅ Reproducible across machines
- ✅ Industry standard practice

### HF Spaces Setup
1. Create Space → Select "Docker" type (NOT Gradio/Streamlit)
2. Connect to GitHub repository
3. Add Secret: `GEMINI_API_KEY` (your API key)
4. HF builds image automatically
5. Deployment happens in 2-3 minutes

### Health Check Endpoint
```python
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0"}
```
This ensures HF Spaces knows app is running.

---

## 📝 DESIGN CHANGES MADE (v2)

**From Original Design to v2**:
1. ✅ Changed parser: Tree-sitter → **Python ast** (reliability)
2. ✅ Updated timeline: 5.5 hrs → **7.5 hrs** (realistic buffer)
3. ✅ Added safeguards: Repo size, chunk truncation, error handling
4. ✅ Deployment: Standard → **Docker for HF Spaces** (guaranteed reliability)
5. ✅ Added Dockerfile template and deployment guide

**Rationale**: These changes trade minimal complexity for maximum reliability. We're engineering a solid product, not a fragile MVP.

---

## ✅ FINAL APPROVAL CHECKLIST

**Design Phase Complete** ✅

- [x] Scope is clear (IN vs OUT) - Python-only, specific features listed
- [x] Tech stack approved - FastAPI, Gemini, ast, Endee, Docker
- [x] Timeline is realistic - 7.5 hours with buffer
- [x] Architecture makes sense - Clear data flow, safeguards included
- [x] How Endee is used is explicit - Core to indexing & search
- [x] Success criteria are understood - MVP + hiring evaluation criteria
- [x] Safeguards documented - Size limits, truncation, error handling
- [x] Deployment strategy clear - Docker for HF Spaces
- [x] Ready to execute with NO changes unless critical

---

## 🎯 NEXT STEP: START CODING

**Design is LOCKED. No more changes unless critical.**

**Execution Plan**:
1. Clone local fork
2. Set up environment (Phase 1)
3. Build backend with safeguards (Phase 2)
4. Build frontend (Phase 3)
5. Test end-to-end (Phase 4)
6. Deploy to HF (Phase 5)
7. Document (Phase 6)

**Status**: Ready to execute 🚀

---

**Document Version**: 2.0 (Safeguards & Deployment Edition)
**Last Updated**: Feb 27, 2026
**Status**: LOCKED FOR EXECUTION

