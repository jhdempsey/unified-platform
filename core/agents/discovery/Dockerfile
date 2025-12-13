FROM python:3.11-slim

WORKDIR /app

# Install dependencies (updated anthropic to latest stable)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    kafka-python==2.0.2 \
    confluent-kafka==2.3.0 \
    avro-python3==1.10.2 \
    requests==2.31.0 \
    pydantic==2.5.0 \
    anthropic>=0.40.0 \
    httpx>=0.27.0 \
    python-dotenv==1.0.0

# Copy shared config (build context is project root)
COPY core/shared /app/shared

# Copy agent directories
COPY core/agents/product-recommender-agent/ ./product-recommender-agent/
COPY core/agents/discovery/src/ ./src/

# Set Python path so all imports work
ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "src.catalog_api:app", "--host", "0.0.0.0", "--port", "8004"]
