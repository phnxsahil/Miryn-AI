# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model permanently into the image
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.4/en_core_web_sm-3.7.4-py3-none-any.whl

ARG PRELOAD_HF_MODELS=false
ENV HF_HOME=/opt/hf
RUN if [ "$PRELOAD_HF_MODELS" = "true" ]; then \
        python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; m='j-hartmann/emotion-english-distilroberta-base'; AutoTokenizer.from_pretrained(m, cache_dir='/opt/hf'); AutoModelForSequenceClassification.from_pretrained(m, cache_dir='/opt/hf')" && \
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/opt/hf')"; \
    fi

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
