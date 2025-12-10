FROM python:3.11-slim

WORKDIR /app

# Install dependencies (added fastavro)
RUN pip install --no-cache-dir \
    confluent-kafka==2.3.0 \
    fastavro==1.9.0 \
    anthropic==0.39.0 \
    httpx==0.27.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    pydantic==2.5.0

# Copy shared config
COPY core/shared /app/shared

# Copy agent code
COPY core/agents/stream-analysis-agent/*.py /app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# No port - this is a background consumer
CMD ["python", "main.py"]
