FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files
COPY *.py ./

ENV PYTHONUNBUFFERED=1

# Default to load_generator (can override in docker-compose)
CMD ["python", "load_generator.py"]
