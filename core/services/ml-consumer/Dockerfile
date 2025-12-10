FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install (using pure Python Kafka client)
COPY core/services/ml-consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/services/ml-consumer/*.py ./

# Add vertical models to path
ENV PYTHONPATH=/app:/app/vertical-models
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "ml_consumer_production.py"]
