# Rahalah Backend - Dockerfile for Cloud Run
# Supports two build modes:
#   A) Pre-built chroma_data: Run vectorDB_preperation.py locally first, then: docker build .
#   B) Build during image: docker build --build-arg HF_TOKEN=your-token .

FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy data and preparation script
COPY env.py vectorDB_preperation.py ./
COPY Data/ ./Data/

# Build ChromaDB (requires HF_TOKEN for LaBSE model)
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}
RUN python vectorDB_preperation.py

# --- Runtime stage ---
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend.py RAGLLM.py env.py rag_logger.py ./
COPY --from=builder /app/chroma_data ./chroma_data

ENV PORT=8080
EXPOSE 8080

CMD sh -c "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8080}"
