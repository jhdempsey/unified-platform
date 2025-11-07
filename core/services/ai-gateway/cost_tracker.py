"""Cost tracking for AI Gateway."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional


class CostTracker:
    """Tracks costs per team/project."""

    def __init__(self):
        # In-memory storage (use Redis/database in production)
        self.costs: Dict[str, list] = defaultdict(list)

    def track_request(
        self,
        team_id: str,
        provider: str,
        model: str,
        tokens: Dict[str, int],
        cost: float,
    ):
        """Track a single request."""
        self.costs[team_id].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider,
                "model": model,
                "tokens": tokens,
                "cost": cost,
            }
        )

    def get_team_summary(self, team_id: str) -> Dict[str, Any]:
        """Get cost summary for a team."""
        if team_id not in self.costs:
            return {
                "team_id": team_id,
                "total_requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "by_provider": {},
            }

        requests = self.costs[team_id]

        # Aggregate by provider
        by_provider = defaultdict(lambda: {"requests": 0, "cost": 0.0, "tokens": 0})

        total_cost = 0.0
        total_tokens = 0

        for req in requests:
            provider = req["provider"]
            by_provider[provider]["requests"] += 1
            by_provider[provider]["cost"] += req["cost"]
            by_provider[provider]["tokens"] += req["tokens"]["total"]

            total_cost += req["cost"]
            total_tokens += req["tokens"]["total"]

        return {
            "team_id": team_id,
            "total_requests": len(requests),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_provider": dict(by_provider),
            "last_updated": requests[-1]["timestamp"] if requests else None,
        }

    def get_all_summaries(self) -> Dict[str, Any]:
        """Get cost summary for all teams."""
        summaries = {}
        total_cost = 0.0
        total_requests = 0

        for team_id in self.costs.keys():
            summary = self.get_team_summary(team_id)
            summaries[team_id] = summary
            total_cost += summary["total_cost"]
            total_requests += summary["total_requests"]

        return {
            "teams": summaries,
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reset_team(self, team_id: str):
        """Reset costs for a team."""
        if team_id in self.costs:
            del self.costs[team_id]

    def export_costs(self, team_id: Optional[str] = None) -> str:
        """Export costs as JSON."""
        if team_id:
            return json.dumps(self.get_team_summary(team_id), indent=2)
        return json.dumps(self.get_all_summaries(), indent=2)
