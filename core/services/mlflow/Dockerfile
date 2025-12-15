FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    mlflow==2.9.2 \
    psycopg2-binary \
    google-cloud-storage \
    gunicorn

# Create mlflow user
RUN useradd -m mlflow
USER mlflow

# Environment variables (set via Cloud Run)
ENV PORT=8080
ENV MLFLOW_HOST=0.0.0.0

EXPOSE 8080

# Start MLflow server
CMD mlflow server \
    --host ${MLFLOW_HOST} \
    --port ${PORT} \
    --backend-store-uri ${MLFLOW_BACKEND_STORE_URI} \
    --default-artifact-root ${MLFLOW_ARTIFACT_ROOT} \
    --serve-artifacts
