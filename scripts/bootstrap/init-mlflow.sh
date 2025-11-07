#!/bin/bash
# Initialize MLflow experiments

# Use environment variable or default to localhost for local dev
MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-http://localhost:5001}"
VERTICAL="${1:-supply-chain}"

echo "🔬 Initializing MLflow"
echo "   Tracking URI: $MLFLOW_TRACKING_URI"
echo "   Vertical: $VERTICAL"

python3 << EOF
import mlflow
import sys

try:
    mlflow.set_tracking_uri('${MLFLOW_TRACKING_URI}')
    
    # Supply chain experiments
    if '${VERTICAL}' == 'supply-chain':
        experiments = [
            'demand-forecasting',
            'inventory-optimization',
            'supplier-reliability'
        ]
    else:
        experiments = ['${VERTICAL}-default']
    
    for exp_name in experiments:
        try:
            mlflow.create_experiment(exp_name)
            print(f"✅ Created experiment: {exp_name}")
        except:
            print(f"ℹ️  Experiment exists: {exp_name}")
            
except Exception as e:
    print(f"❌ MLflow initialization failed: {e}")
    sys.exit(1)

print("✅ All experiments initialized")
EOF

echo "✅ MLflow initialization complete"
