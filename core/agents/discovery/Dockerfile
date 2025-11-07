FROM python:3.11-slim

WORKDIR /app

# Copy requirements from discovery agent
COPY discovery/requirements.txt* ./
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir \
            fastapi==0.104.1 \
            uvicorn[standard]==0.24.0 \
            kafka-python==2.0.2 \
            confluent-kafka==2.3.0 \
            avro-python3==1.10.2 \
            requests==2.31.0 \
            pydantic==2.5.0 \
            anthropic==0.25.0; \
    fi

# Copy ALL agent directories (build context is /core/agents)
COPY product-recommender-agent/ ./product-recommender-agent/
COPY discovery/src/ ./src/

# Set Python path so all imports work
ENV PYTHONPATH=/app/src:/app

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "src.catalog_api:app", "--host", "0.0.0.0", "--port", "8004"]
