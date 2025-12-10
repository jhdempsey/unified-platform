FROM python:3.11-slim

WORKDIR /app

# Install dependencies (fixed anthropic version, added fastavro)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    confluent-kafka==2.3.0 \
    fastavro==1.9.0 \
    anthropic==0.39.0 \
    httpx==0.27.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# Copy shared config
COPY core/shared /app/shared

# Copy agent code
COPY core/agents/product-generator-agent/*.py /app/

ENV PYTHONPATH=/app
EXPOSE 8003

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003"]
