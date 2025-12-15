FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    anthropic \
    pydantic

COPY main.py .

ENV PORT=8080

EXPOSE 8080

CMD ["python", "main.py"]
