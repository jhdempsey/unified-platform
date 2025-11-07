"""Supplier Reliability Scorer - Predicts supplier performance."""

from typing import Any, Dict


class SupplierReliabilityModel:
    """ML model for scoring supplier reliability."""

    def __init__(self):
        self.model_name = "supplier_reliability_v1"
        self.version = "1.0.0"

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score supplier reliability based on multiple factors.

        Args:
            features: Dict containing:
                - supplier_id: str
                - historical_reliability: float (0-1)
                - delivery_history: list of delivery times
                - region: str
                - distance_miles: int

        Returns:
            Dict with reliability score and factors
        """
        base_reliability = features.get("historical_reliability", 0.85)
        region = features.get("region", "Unknown")
        distance = features.get("distance_miles", 1000)

        # Adjust based on distance (longer distance = more risk)
        distance_factor = 1.0
        if distance > 2000:
            distance_factor = 0.95
        elif distance > 1000:
            distance_factor = 0.98

        # Regional reliability adjustments
        region_adjustments = {
            "California": 1.02,
            "Alaska": 0.95,
            "Wisconsin": 1.0,
            "Oregon": 0.98,
            "International": 0.92,
        }
        region_factor = region_adjustments.get(region, 1.0)

        # Calculate final score
        reliability_score = base_reliability * distance_factor * region_factor
        reliability_score = min(max(reliability_score, 0.0), 1.0)

        # Categorize
        if reliability_score >= 0.9:
            category = "excellent"
        elif reliability_score >= 0.8:
            category = "good"
        elif reliability_score >= 0.7:
            category = "fair"
        else:
            category = "poor"

        return {
            "model": self.model_name,
            "version": self.version,
            "reliability_score": round(reliability_score, 3),
            "category": category,
            "factors": {
                "base_reliability": round(base_reliability, 3),
                "distance_impact": round(distance_factor, 3),
                "region_impact": round(region_factor, 3),
            },
            "confidence": 0.87,
        }
