FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    confluent-kafka==2.3.0 \
    fastavro==1.9.0 \
    anthropic>=0.40.0 \
    httpx>=0.27.0 \
    python-dotenv==1.0.0 \
    pydantic==2.5.0 \
    requests==2.31.0

# Copy shared config (build context is project root)
COPY core/shared /app/shared

# Copy agent code
COPY core/agents/stream-analysis-agent/*.py /app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Run the HTTP wrapper
CMD ["python", "main.py"]
