FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        scikit-learn==1.3.0 \
        joblib==1.3.2 \
        mlflow==2.9.0

# Copy application code
COPY *.py ./

# Create writable model directory for cached models
RUN mkdir -p /app/models && chmod 777 /app/models

ENV PYTHONPATH=/app:/app/vertical-models

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
