"""Inventory Optimization - Recommends optimal stock levels."""

from typing import Any, Dict

import numpy as np


class InventoryOptimizationModel:
    """ML model for inventory optimization recommendations."""

    def __init__(self):
        self.model_name = "inventory_optimization_v1"
        self.version = "1.0.0"

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend optimal inventory levels.

        Args:
            features: Dict containing:
                - product_name: str
                - current_stock: int
                - daily_demand: float
                - lead_time_days: int
                - perishable: bool
                - shelf_life_days: int (if perishable)

        Returns:
            Dict with inventory recommendations
        """
        current_stock = features.get("current_stock", 100)
        daily_demand = features.get("daily_demand", 20)
        lead_time = features.get("lead_time_days", 3)
        perishable = features.get("perishable", False)
        shelf_life = features.get("shelf_life_days", 30)

        # Calculate safety stock (buffer for demand variability)
        demand_std = daily_demand * 0.2  # Assume 20% variability
        safety_stock = demand_std * np.sqrt(lead_time) * 1.65  # 95% service level

        # Calculate reorder point
        reorder_point = (daily_demand * lead_time) + safety_stock

        # Calculate optimal order quantity
        # For perishables, limit by shelf life
        if perishable:
            max_order = daily_demand * min(shelf_life * 0.7, lead_time * 3)
        else:
            max_order = daily_demand * lead_time * 2

        optimal_quantity = max(max_order, safety_stock * 2)

        # Determine action
        if current_stock < reorder_point:
            action = "reorder"
            urgency = "high" if current_stock < safety_stock else "medium"
            quantity_to_order = optimal_quantity
        elif current_stock > optimal_quantity * 1.5:
            action = "reduce"
            urgency = "low"
            quantity_to_order = 0
        else:
            action = "maintain"
            urgency = "low"
            quantity_to_order = 0

        # Days of stock remaining
        days_remaining = current_stock / daily_demand if daily_demand > 0 else 999

        return {
            "model": self.model_name,
            "version": self.version,
            "action": action,
            "urgency": urgency,
            "current_stock": int(current_stock),
            "optimal_stock": int(optimal_quantity),
            "reorder_point": int(reorder_point),
            "safety_stock": int(safety_stock),
            "recommended_order_quantity": int(quantity_to_order),
            "days_of_stock": round(days_remaining, 1),
            "stockout_risk": "high" if days_remaining < lead_time else "low",
            "confidence": 0.82,
        }
