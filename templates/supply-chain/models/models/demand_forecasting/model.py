"""
Demand Forecasting Model - Simple time series forecasting
"""

from datetime import datetime
from typing import Any, Dict, Sequence, Union

import numpy as np


class DemandForecastingModel:
    def __init__(self):
        self.model_name = "demand_forecasting_v1"
        self.version = "1.0.0"
        self.trained = False

    def train(
        self, historical_data: Sequence[Union[int, float]]
    ) -> "DemandForecastingModel":
        """Train model with historical data"""
        self.baseline = float(np.mean(historical_data))
        self.trained = True
        return self

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make demand forecast

        Args:
            features: {
                'historical_sales': Sequence[Union[int, float]],
                'forecast_horizon': int (default: 7)
            }
        """
        historical_sales = features.get("historical_sales", [])
        forecast_horizon = features.get("forecast_horizon", 7)

        if not historical_sales:
            raise ValueError("historical_sales is required")

        # Simple moving average
        recent_avg = float(np.mean(historical_sales[-7:]))
        trend = self._calculate_trend(historical_sales)

        # Generate forecast
        predictions = []
        for i in range(forecast_horizon):
            pred = recent_avg + (trend * i)
            predictions.append(max(0, float(pred)))

        # Confidence intervals
        std_dev = float(np.std(historical_sales))
        confidence_intervals = [
            {"lower": max(0, pred - 1.96 * std_dev), "upper": pred + 1.96 * std_dev}
            for pred in predictions
        ]

        return {
            "predictions": predictions,
            "confidence_intervals": confidence_intervals,
            "baseline": float(recent_avg),
            "trend": float(trend),
            "model_version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _calculate_trend(self, data: Sequence[Union[int, float]]) -> float:
        """Calculate linear trend"""
        if len(data) < 2:
            return 0.0
        x = np.arange(len(data))
        y = np.array(data, dtype=float)
        slope = float(np.polyfit(x, y, 1)[0])
        return slope


# Example usage
if __name__ == "__main__":
    # Create and test model
    model = DemandForecastingModel()

    # Sample historical sales data
    historical_sales = [100, 105, 98, 110, 115, 120, 118, 125, 130, 128]

    # Train
    model.train(historical_sales)

    # Predict
    result = model.predict(
        {"historical_sales": historical_sales, "forecast_horizon": 7}
    )

    print("📊 Demand Forecast Results:")
    print(f"Predictions: {result['predictions']}")
    print(f"Baseline: {result['baseline']}")
    print(f"Trend: {result['trend']}")
