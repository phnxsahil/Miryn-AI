# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

WORKDIR /app

# Install system deps for psycopg2, cryptography, and native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.6.0 && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model permanently into the image
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Set stable cache paths for HuggingFace models
ENV HF_HOME=/opt/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/huggingface
RUN mkdir -p /opt/huggingface && chmod -R a+rX /opt/huggingface

COPY . .

# Render injects PORT env var — default to 8000 for local
ENV PORT=8000

EXPOSE ${PORT}

# Production-ready: 2 workers, graceful shutdown, access logs
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --timeout-keep-alive 30 --access-log"]
