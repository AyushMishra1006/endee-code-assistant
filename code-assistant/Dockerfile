FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY code-assistant/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY code-assistant/src /app/src
COPY code-assistant/frontend /app/frontend

# Copy main entry point
COPY code-assistant/main.py /app/

# Expose port for HF Spaces
EXPOSE 7860

# Set environment
ENV PYTHONUNBUFFERED=1

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
