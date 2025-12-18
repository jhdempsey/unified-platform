FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML models
COPY ml/ ./ml/

# Copy application code
COPY *.py ./

# Create writable model directory for cached models
RUN mkdir -p /app/models && chmod 777 /app/models

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
