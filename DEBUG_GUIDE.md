# 🐛 Debugging Guide: "Failed to Index Chunks" Error

## Quick Diagnosis Checklist

- [ ] Is Endee Docker container running?
- [ ] Are embeddings valid (no NaN values)?
- [ ] Are chunks valid (required fields present)?
- [ ] Are vector dimensions correct (384)?

---

## Issue 1: Endee Server Not Running ❌

### Symptom
```
[ERROR] Failed to connect to Endee: Connection refused
[INFO] Make sure Endee server is running: docker-compose up -d
```

### How to Check
```bash
# List running containers
docker ps

# Look for: endeeio/endee-server
```

### How to Fix
```bash
# Start Endee with Docker Compose
cd c:/Users/Ayush\ Mishra/OneDrive/Desktop/Endee
docker-compose up -d

# Verify it's running
docker ps | grep endee

# Check logs
docker-compose logs -f endee
```

---

## Issue 2: Embeddings Contain NaN Values 🔍

### What are NaN values?
```python
import numpy as np

# Valid embedding (good ✅)
emb = [0.123, 0.456, 0.789]  # All numbers

# Invalid embedding (bad ❌)
emb = [0.123, nan, 0.789]    # Contains NaN
```

### How to Identify NaN
New code now checks automatically! Look for:
```
[ERROR] Found 5/100 embeddings with NaN values!
[DEBUG] This usually means sentence-transformers failed to encode text.
```

### Why NaN Happens
1. **Text is empty or corrupted**
   ```python
   text = ""  # Empty string → NaN
   embedding = model.encode(text)  # Results in NaN
   ```

2. **Sentence-Transformers encounters bad input**
   ```python
   text = "!@#$%^&*()"  # Only special chars → NaN
   ```

3. **Memory issue during encoding**
   - Too many large texts at once
   - GPU running out of memory

### How to Debug in Console
```bash
# When you see embedding error, check the console logs
# Look for patterns like:

[WARNING] Empty text passed to embed_text, returning zeros
[ERROR] Embedding contains NaN values for text: "def foo(...)..."
[ERROR] Could not embed text: [actual error]
```

### How to Fix
```python
# In code_parser.py, validate text before embedding:

def chunk_for_storage(chunk):
    combined_text = chunk.get('combined_text', '').strip()

    # VALIDATION: Check if text is empty
    if not combined_text:
        print(f"[WARNING] Chunk {chunk['id']} has empty text!")
        combined_text = "No code available"  # Fallback

    # VALIDATION: Check if text is too long
    if len(combined_text) > 50000:
        print(f"[WARNING] Chunk too large ({len(combined_text)} chars)")
        combined_text = combined_text[:50000]

    return {
        ...
        'combined_text': combined_text,
        ...
    }
```

---

## Issue 3: Missing or Invalid Chunk Metadata ❌

### Required Fields
Every chunk MUST have:
```python
{
    'id': 'unique_identifier',           # ✅ Required
    'file_path': 'src/utils.py',        # ✅ Required
    'name': 'function_name',             # ✅ Required
    'class_name': 'ClassName',           # ❌ Optional
    'source_code': 'def foo(): ...',      # ❌ Optional
    'docstring': '"""..."""',             # ❌ Optional
}
```

### How to Check
New code now validates:
```
[WARNING] Chunk 5 missing required fields. Skipping.
[ERROR] No valid vectors to upsert after validation!
```

### How to Fix
Check `code_parser.py` - ensure every chunk includes `id`, `file_path`, and `name`.

---

## Issue 4: Vector Dimension Mismatch 🔢

### Expected Dimension
All embeddings MUST be **384-dimensional** (Sentence-Transformers output).

### How to Check
```bash
# In console, look for:
[WARNING] Embedding 0 has dimension 768, expected 384
```

### Why It Happens
- Using wrong embedding model (e.g., OpenAI = 1536 dimensions)
- Corrupted embedding file

### How to Fix
Verify model in `embeddings.py`:
```python
self.model = SentenceTransformer('all-MiniLM-L6-v2')  # ✅ Must be 384-dim
# NOT: SentenceTransformer('paraphrase-MiniLM-L12-v2')  # Wrong model
```

---

## How to Debug Step-by-Step 🔧

### Step 1: Check Endee is Running
```bash
docker ps
# Should see: endeeio/endee-server
```

### Step 2: Check Console Logs
When running Streamlit:
```bash
# Terminal will show detailed logs like:
[DEBUG] Validating 150 embeddings...
[OK] All embeddings valid (384-dim, no NaN)
[ERROR] Found 3 embeddings with NaN values!
```

### Step 3: Identify the Exact Problem
```
✅ Embeddings valid → Problem is Endee connection
❌ Embeddings have NaN → Problem is sentence-transformers
❌ Chunks missing fields → Problem is code_parser.py
```

### Step 4: Check Individual Chunks
Add debugging to `code_parser.py`:
```python
def parse_repository(repo_path, python_files):
    chunks = []
    for file in python_files:
        methods = extract_methods_from_file(file)
        for method in methods:
            chunk = {
                'id': f"{file}_{method['name']}_line_{method['start']}",
                'file_path': file,
                'name': method['name'],
                'source_code': method['code']
            }

            # DEBUG: Print first 3 chunks
            if len(chunks) < 3:
                print(f"[DEBUG] Chunk: id={chunk['id']}, name={chunk['name']}")
                print(f"[DEBUG] Code length: {len(chunk['source_code'])}")

            chunks.append(chunk)
    return chunks
```

---

## Testing Embeddings Locally 🧪

### Test Script: Check Embeddings Quality
```bash
# Create this test file: test_embeddings.py

import sys
sys.path.insert(0, 'src')
from embeddings import embed_texts
import numpy as np

# Test cases
test_texts = [
    "def hello_world(): print('hello')",
    "class MyClass: pass",
    "",  # Empty - should trigger warning
]

embeddings = embed_texts(test_texts)

for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
    if emb is None:
        print(f"❌ Text {i}: Failed to embed")
    else:
        emb_array = np.array(emb)
        has_nan = np.isnan(emb_array).any()
        print(f"✅ Text {i}: {len(emb)}-dim, NaN={has_nan}")

# Run it:
# python test_embeddings.py
```

---

## Testing Vector DB Locally 🧪

### Test Script: Check Vector DB Indexing
```bash
# Create this test file: test_vector_db.py

import sys
sys.path.insert(0, 'src')
from vector_db import get_vector_db, reset_vector_db

# Reset DB
reset_vector_db()
db = get_vector_db()

# Test data
test_chunks = [{
    'id': 'test_1',
    'file_path': 'test.py',
    'name': 'test_func',
    'source_code': 'def test(): pass'
}]

test_embeddings = [[0.1] * 384]  # 384-dimensional vector

# Try to index
success = db.add_chunks(test_chunks, test_embeddings)
print(f"Indexing result: {'✅ Success' if success else '❌ Failed'}")

# Run it:
# python test_vector_db.py
```

---

## Common Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Endee not running | `docker-compose up -d` |
| `NaN values found` | Bad text encoding | Validate empty text in parser |
| `Dimension 768, expected 384` | Wrong model | Use `all-MiniLM-L6-v2` |
| `Missing required fields` | Incomplete chunk | Add `id`, `file_path`, `name` |
| `Index not found` | Endee index deleted | Restart Endee: `docker-compose restart` |

---

## Pro Debugging Tips 💡

1. **Use print statements strategically**
   ```python
   print(f"[DEBUG] Processing {len(chunks)} chunks")
   print(f"[DEBUG] First embedding dims: {len(embeddings[0])}")
   print(f"[DEBUG] Has NaN: {any(math.isnan(v) for v in embeddings[0])}")
   ```

2. **Check logs in order**
   - Console logs show the actual error
   - Streamlit UI shows user-friendly message
   - Look in console first!

3. **Test each step independently**
   - Can you clone the repo?
   - Can you parse Python files?
   - Can you generate embeddings?
   - Can you index in Endee?

4. **Use Docker logs**
   ```bash
   docker-compose logs endee  # See Endee server logs
   docker-compose logs -f     # Follow all logs
   ```

---

## Need More Help?

Check these files:
- **Embeddings failing**: `src/embeddings.py`
- **Vector DB failing**: `src/vector_db.py`
- **Chunks invalid**: `src/code_parser.py`
- **General flow**: `app.py`

All now have better error messages to help you debug! 🚀
