FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    confluent-kafka==2.3.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# Copy shared config
COPY core/shared /app/shared

# Copy service code
COPY templates/supply-chain/services/product-service/*.py /app/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
