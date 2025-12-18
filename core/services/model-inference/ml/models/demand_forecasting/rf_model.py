"""
Random Forest Model for Supply Chain Fulfillment Time Prediction
Integrates with MLflow for tracking and model registry
Auto-detects environment (local vs Kubernetes)
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


class SupplyChainRFModel:
    """Random Forest model for predicting order fulfillment time"""

    def __init__(self, model_name: str = "supply_chain_rf"):
        self.model_name = model_name
        self.version = "2.0.0"
        self.model: Optional[RandomForestRegressor] = None
        self.feature_names = [
            "product_category",
            "order_quantity",
            "warehouse_distance",
            "day_of_week",
            "season",
            "supplier_reliability",
            "weather_condition",
        ]
        self.trained = False
        self.mlflow_run_id: Optional[str] = None
        self.mlflow_model_uri: Optional[str] = None

    def _get_mlflow_artifact_path(self) -> str:
        """
        Get writable artifact path based on environment
        """
        if "KUBERNETES_SERVICE_HOST" in os.environ:
            # Kubernetes - use mounted volume
            return "/mlflow/artifacts"
        else:
            # Local development - use user's home directory

            local_artifacts = os.path.expanduser("~/.mlflow/artifacts")
            os.makedirs(local_artifacts, exist_ok=True)
            return local_artifacts

    def _get_mlflow_uri(self) -> str:
        """
        Auto-detect MLflow URI based on environment
        Priority:
        1. MLFLOW_TRACKING_URI env var (explicit override)
        2. Kubernetes service (if KUBERNETES_SERVICE_HOST exists)
        3. Public MLflow IP (fallback for local dev)
        """
        # 1. Check for explicit override
        if "MLFLOW_TRACKING_URI" in os.environ:
            return os.environ["MLFLOW_TRACKING_URI"]

        # 2. Check if running in Kubernetes
        if "KUBERNETES_SERVICE_HOST" in os.environ:
            # Use internal Kubernetes service DNS
            return "http://mlflow.default.svc.cluster.local:5000"

        # 3. Fallback to public IP for local development
        return "http://34.135.31.127:5000"

    def generate_training_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic supply chain data for training"""
        np.random.seed(42)

        data = {
            "product_category": np.random.randint(0, 5, n_samples),  # 5 categories
            "order_quantity": np.random.randint(10, 1000, n_samples),
            "warehouse_distance": np.random.uniform(5, 500, n_samples),
            "day_of_week": np.random.randint(0, 7, n_samples),
            "season": np.random.randint(0, 4, n_samples),
            "supplier_reliability": np.random.uniform(60, 100, n_samples),
            "weather_condition": np.random.randint(
                0, 3, n_samples
            ),  # Clear, Rain, Snow
        }

        df = pd.DataFrame(data)

        # Generate realistic fulfillment time based on features
        base_time = 24.0  # Base 24 hours

        # Category impact (Dairy=faster, Frozen=slower)
        category_impact = df["product_category"] * 2

        # Quantity impact
        quantity_impact = (df["order_quantity"] / 100) * 0.5

        # Distance impact
        distance_impact = df["warehouse_distance"] / 50

        # Reliability impact (higher = faster)
        reliability_impact = -(df["supplier_reliability"] - 70) / 10

        # Weather impact
        weather_impact = df["weather_condition"] * 3

        # Combine with noise
        df["fulfillment_hours"] = (
            base_time
            + category_impact
            + quantity_impact
            + distance_impact
            + reliability_impact
            + weather_impact
            + np.random.normal(0, 2, n_samples)  # Noise
        )

        # Ensure positive values
        df["fulfillment_hours"] = df["fulfillment_hours"].clip(lower=4)

        return df

    def train(
        self,
        data: Optional[pd.DataFrame] = None,
        n_estimators: int = 100,
        max_depth: int = 10,
        log_to_mlflow: Optional[bool] = None,
    ) -> "SupplyChainRFModel":
        """
        Train Random Forest model

        Args:
            data: Training dataframe (if None, generates synthetic data)
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            log_to_mlflow: Whether to log to MLflow
        """
        # Generate data if not provided
        if data is None:
            print("📊 Generating synthetic training data...")
            data = self.generate_training_data(n_samples=1000)

        # Prepare features and target
        X = data[self.feature_names]
        y = data["fulfillment_hours"]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Determine MLflow logging behavior if not explicitly set
        if log_to_mlflow is None:
            log_to_mlflow = os.getenv("ENABLE_MLFLOW_LOGGING", "1") == "1"

        # Start MLflow run if enabled
        if log_to_mlflow:
            # Auto-detect environment and set appropriate MLflow URI
            mlflow_uri = self._get_mlflow_uri()

            print(f"🔗 Connecting to MLflow: {mlflow_uri}")

            try:
                mlflow.set_tracking_uri(mlflow_uri)
                mlflow.set_experiment("supply-chain.predictions")

            except Exception as e:
                print(f"⚠️  MLflow connection failed: {e}")
                print("   Continuing training without MLflow tracking...")
                log_to_mlflow = False  # Disable MLflow for this run

        # Train model
        print(f"🌲 Training Random Forest with {n_estimators} trees...")
        self.model = RandomForestRegressor(
            n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
        )

        if log_to_mlflow:
            with mlflow.start_run(
                run_name=f"rf_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ) as run:
                self.mlflow_run_id = run.info.run_id

                # Log parameters
                mlflow.log_param("n_estimators", n_estimators)
                mlflow.log_param("max_depth", max_depth)
                mlflow.log_param("model_type", "RandomForest")
                mlflow.log_param("training_samples", len(X_train))

                # Train
                self.model.fit(X_train, y_train)

                # Evaluate
                train_pred = self.model.predict(X_train)
                test_pred = self.model.predict(X_test)

                train_mae = mean_absolute_error(y_train, train_pred)
                test_mae = mean_absolute_error(y_test, test_pred)
                train_r2 = r2_score(y_train, train_pred)
                test_r2 = r2_score(y_test, test_pred)

                # Log metrics
                mlflow.log_metric("train_mae", train_mae)
                mlflow.log_metric("test_mae", test_mae)
                mlflow.log_metric("train_r2", train_r2)
                mlflow.log_metric("test_r2", test_r2)

                # Log feature importance
                feature_importance = dict(
                    zip(
                        self.feature_names,
                        self.model.feature_importances_,
                        strict=False,
                    )
                )
                for feat, imp in feature_importance.items():
                    mlflow.log_metric(f"feature_importance_{feat}", imp)

                # Log model to MLflow
                mlflow.sklearn.log_model(
                    self.model, "model", registered_model_name=self.model_name
                )

                self.mlflow_model_uri = f"runs:/{run.info.run_id}/model"

                print(f"✅ Model logged to MLflow: {self.mlflow_model_uri}")
                print(f"   Test MAE: {test_mae:.2f} hours")
                print(f"   Test R²: {test_r2:.3f}")
        else:
            self.model.fit(X_train, y_train)

            # Evaluate without MLflow
            test_pred = self.model.predict(X_test)
            test_mae = mean_absolute_error(y_test, test_pred)
            test_r2 = r2_score(y_test, test_pred)

            print("✅ Model trained (no MLflow tracking)")
            print(f"   Test MAE: {test_mae:.2f} hours")
            print(f"   Test R²: {test_r2:.3f}")

        self.trained = True
        return self

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction

        Args:
            features: Dictionary with keys matching self.feature_names
        """
        if not self.trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Convert to dataframe
        df = pd.DataFrame([features])

        # Ensure all features present
        for feat in self.feature_names:
            if feat not in df.columns:
                raise ValueError(f"Missing required feature: {feat}")

        # Predict
        prediction = self.model.predict(df[self.feature_names])[0]

        return {
            "predicted_fulfillment_hours": float(prediction),
            "model_name": self.model_name,
            "model_version": self.version,
            "model_type": "RandomForest",
            "timestamp": datetime.utcnow().isoformat(),
            "mlflow_run_id": self.mlflow_run_id,
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.trained or self.model is None:
            return {}

        return dict(
            zip(
                self.feature_names,
                [float(x) for x in self.model.feature_importances_],
                strict=True,
            )
        )

    def save_local(self, path: str = "/app/models/rf_model.joblib"):
        """Save model locally using joblib"""
        if not self.trained or self.model is None:
            raise ValueError("Model not trained")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"💾 Model saved to {path}")

    def load_local(self, path: str = "/app/models/rf_model.joblib"):
        """Load model from local path"""
        if os.path.exists(path):
            self.model = joblib.load(path)
            self.trained = True
            print(f"📂 Model loaded from {path}")
        else:
            print(f"⚠️  Model file not found: {path}")

    @classmethod
    def load_from_mlflow(cls, model_uri: str) -> "SupplyChainRFModel":
        """Load model from MLflow"""
        instance = cls()
        instance.model = mlflow.sklearn.load_model(model_uri)
        instance.trained = True
        instance.mlflow_model_uri = model_uri
        print(f"📦 Model loaded from MLflow: {model_uri}")
        return instance

    def get_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "model_type": "RandomForest",
            "trained": self.trained,
            "feature_names": self.feature_names,
            "feature_importance": self.get_feature_importance() if self.trained else {},
            "mlflow_run_id": self.mlflow_run_id,
            "mlflow_model_uri": self.mlflow_model_uri,
        }


# Training script for auto-startup
if __name__ == "__main__":
    print("🚀 Starting Random Forest model training...")

    model = SupplyChainRFModel()
    model.train(n_estimators=100, max_depth=10, log_to_mlflow=True)

    # Save locally as backup
    model.save_local("/app/models/rf_model.joblib")

    # Test prediction
    test_features = {
        "product_category": 2,
        "order_quantity": 500,
        "warehouse_distance": 150.0,
        "day_of_week": 3,
        "season": 1,
        "supplier_reliability": 85.0,
        "weather_condition": 0,
    }

    result = model.predict(test_features)
    print(f"\n📊 Test Prediction: {result['predicted_fulfillment_hours']:.1f} hours")
    print("✅ Model ready for inference!")
