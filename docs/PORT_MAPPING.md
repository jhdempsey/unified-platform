# Port Mapping Reference

## Container-to-Container (Internal Network)
When services talk to each other inside Docker network:

| Service | Internal Port | Container URL |
|---------|--------------|---------------|
| MLflow | 5000 | http://mlflow:5000 |
| Prometheus | 9090 | http://prometheus:9090 |
| Model Inference | 8001 | http://model-inference:8001 |
| RAG Service | 8005 | http://rag-service:8005 |
| Discovery Agent | 8004 | http://discovery-agent:8004 |
| AI Gateway | 8002 | http://ai-gateway:8002 |

## Host Access (From Your Browser)
When you access from localhost:

| Service | Host Port | Browser URL |
|---------|-----------|-------------|
| MLflow | 5001 | http://localhost:5001 |
| Prometheus | 9091 | http://localhost:9091 |
| Model Inference | 8001 | http://localhost:8001 |
| RAG Service | 8005 | http://localhost:8005 |
| Discovery Agent | 8004 | http://localhost:8004 |
| Dashboard | 8501 | http://localhost:8501 |

## Why Different?
Docker Compose maps container ports to host ports:
```yaml
ports:
  - "5001:5000"  # Host:Container
```

Inside the network, use **container port**.  
From your browser, use **host port**.
