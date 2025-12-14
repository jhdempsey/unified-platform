FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    confluent-kafka==2.3.0 \
    python-dotenv==1.0.0 \
    pydantic==2.5.0

# Copy service code (build context is core/services/event-producer/)
COPY *.py ./

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Run the HTTP wrapper instead of load_generator
CMD ["python", "main.py"]
