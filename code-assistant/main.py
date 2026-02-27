"""
Entry point for Code Documentation Assistant
Routes requests to FastAPI app and serves frontend
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import FastAPI app from src
from main import app as api_app

# Create combined app
app = FastAPI()

# Mount API routes under /api
app.mount("/api", api_app)

# Serve static files (frontend)
frontend_path = Path(__file__).parent / 'frontend'
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Serve index.html as root
@app.get("/")
async def serve_root():
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "Code Documentation Assistant is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
