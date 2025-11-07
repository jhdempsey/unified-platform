# 🤖 ML Models

Custom machine learning models for the AI Incubator Platform.

## 📁 Structure

```
ml/models/
├── common/
│   ├── __init__.py
│   └── utils.py                 # Shared utilities (preprocessing, MLflow)
│
├── demand_forecasting/
│   ├── __init__.py
│   ├── data.py                  # Synthetic data generation
│   ├── train.py                 # Training script (scikit-learn)
│   └── train_pytorch.py         # Training script (PyTorch)
│
├── inventory_optimization/      # Future model
│   └── ...
│
└── supplier_reliability/        # Future model
    └── ...
```

## 🚀 Quick Start

### Train a Model Locally

```bash
# From project root
python -m ml.models.demand_forecasting.train \
  --model=random_forest \
  --n-samples=5000 \
  --output-dir=./local_models
```

### Train on Kubernetes

```bash
# Deploy training job
kubectl apply -f k8s/ml-training-job.yaml

# Monitor training
kubectl logs -l app=ml-training -f

# View results in MLflow
# Open: http://YOUR_MLFLOW_IP:5000
```

## 📊 Available Models

### 1. Demand Forecasting

**Purpose:** Predict order fulfillment time based on supply chain factors

**Features:**
- `product_category` - Product type (Dairy, Produce, Meat, Bakery, Frozen)
- `order_quantity` - Number of units
- `warehouse_distance` - Distance from warehouse (miles)
- `day_of_week` - Day of week (0=Monday, 6=Sunday)
- `season` - Season (0=Winter, 1=Spring, 2=Summer, 3=Fall)
- `supplier_reliability` - Supplier rating (0-100)
- `weather_condition` - Weather (0=Clear, 1=Rain, 2=Snow)

**Target:**
- `fulfillment_hours` - Time to fulfill order (2-72 hours)

**Models:**
- Random Forest: MAE ~2.5 hours, R² ~0.85
- Gradient Boosting: MAE ~2.7 hours, R² ~0.83
- PyTorch NN: MAE ~2.8 hours, R² ~0.82

**API Endpoint:**
```bash
POST /predict/demand
{
  "product_category": "Dairy",
  "order_quantity": 500,
  "warehouse_distance": 150.5,
  ...
}
```

### 2. Inventory Optimization (Coming Soon)

**Purpose:** Optimize inventory levels based on demand patterns

### 3. Supplier Reliability (Coming Soon)

**Purpose:** Predict supplier performance and reliability scores

## 🔧 Development

### Adding a New Model

1. **Create model directory:**
```bash
mkdir -p ml/models/your_model_name
touch ml/models/your_model_name/{__init__.py,data.py,train.py,model.py}
```

2. **Implement data generation** (`data.py`):
```python
def generate_data(n_samples=5000):
    # Generate synthetic or load real data
    return dataframe
```

3. **Implement training** (`train.py`):
```python
from ml.models.common.utils import init_mlflow, log_model_to_mlflow

def train():
    init_mlflow("your_experiment_name")
    # Training logic
    log_model_to_mlflow(model, ...)
```

4. **Update inference service** (`services/model-inference/main.py`):
```python
@app.post("/predict/your_model")
def predict_your_model(request: YourRequest):
    # Prediction logic
    return response
```

5. **Create Kubernetes job:**
```yaml
# k8s/ml-training-your-model.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ml-training-your-model
spec:
  template:
    spec:
      containers:
      - name: trainer
        command: ["python", "-m", "ml.models.your_model_name.train"]
```

## 📈 MLflow Integration

All models automatically log to MLflow:

- **Experiments:** Each model type gets its own experiment
- **Runs:** Each training run logs:
  - Parameters (hyperparameters)
  - Metrics (MAE, RMSE, R², MAPE)
  - Artifacts (model file, preprocessor)
  - Tags (model_type, model_name)

**View Experiments:**
```bash
# Get MLflow URL
kubectl get svc mlflow

# Open in browser
open http://YOUR_MLFLOW_IP:5000
```

## 🧪 Testing

### Unit Tests

```bash
# Test data generation
python -m ml.models.demand_forecasting.data

# Test training (small sample)
python -m ml.models.demand_forecasting.train --n-samples=100
```

### Integration Tests

```bash
# Test full pipeline
./scripts/test-ml-inference.sh
```

## 📚 Code Standards

### Data Generation
- Use `np.random.seed()` for reproducibility
- Generate realistic distributions
- Include business logic in target calculation
- Provide `split_data()` function

### Training
- Use `BasePreprocessor` from `common/utils.py`
- Log all experiments to MLflow
- Save both model and preprocessor
- Calculate comprehensive metrics
- Print feature importance

### Model Classes
- Inherit from a base model class (optional)
- Implement `fit()`, `predict()`, `save()`, `load()`
- Document expected input/output formats

## 🔐 Best Practices

1. **Version Control:** All model code in git
2. **Reproducibility:** Fixed random seeds, tracked experiments
3. **Monitoring:** Log predictions for drift detection
4. **Documentation:** Clear docstrings and README
5. **Testing:** Unit tests for data and training
6. **Scalability:** Batch prediction support

## 📊 Performance Benchmarks

| Model | Training Time | Inference Latency | Memory |
|---|---|---|---|
| Random Forest (100 trees) | ~30s | ~10ms | 50MB |
| Gradient Boosting (100 est) | ~45s | ~8ms | 40MB |
| PyTorch NN (3 layers) | ~2min | ~5ms | 30MB |

*Benchmarks on n1-standard-2 (2 vCPU, 7.5GB RAM)*

## 🐛 Troubleshooting

### "Module not found: ml.models"
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

### "MLflow connection refused"
```bash
# Verify MLflow service
kubectl get svc mlflow

# Port-forward if needed
kubectl port-forward svc/mlflow 5000:5000
export MLFLOW_TRACKING_URI=http://localhost:5000
```

### "Model file not found"
```bash
# Check if model was saved
ls -la ./local_models/

# For K8s, check PVC
kubectl exec -it POD_NAME -- ls -la /data/models/
```

## 📖 References

- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)

---

**Questions?** Check the main [README.md](../../README.md) or [INTEGRATE-ML.md](../../INTEGRATE-ML.md)
