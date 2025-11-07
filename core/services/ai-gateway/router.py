"""Smart routing logic for LLM providers."""

from enum import Enum
from typing import List, Optional

from providers import ProviderManager, ProviderType


class RoutingStrategy(str, Enum):
    """Routing strategies."""

    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    ROUND_ROBIN = "round_robin"


class SmartRouter:
    """Routes requests to optimal LLM provider."""

    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
        self._round_robin_index = 0

        # Provider characteristics (based on benchmarks/pricing)
        self.provider_profiles = {
            ProviderType.GEMINI: {
                "cost_score": 10,  # Cheapest (free tier available)
                "latency_score": 9,  # Very fast
                "quality_score": 8,  # Good quality
            },
            ProviderType.GPT4: {
                "cost_score": 7,  # Moderate cost
                "latency_score": 7,  # Good latency
                "quality_score": 9,  # Excellent quality
            },
            ProviderType.CLAUDE: {
                "cost_score": 5,  # Higher cost
                "latency_score": 8,  # Fast
                "quality_score": 10,  # Best quality
            },
        }

    def route(
        self,
        strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED,
        preferred_provider: Optional[ProviderType] = None,
    ) -> Optional[ProviderType]:
        """Route request to best provider based on strategy."""

        available = self.provider_manager.get_available_providers()
        if not available:
            return None

        # If preferred provider specified and available, use it
        if preferred_provider and preferred_provider in available:
            return preferred_provider

        # Route based on strategy
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._route_by_cost(available)
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            return self._route_by_latency(available)
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return self._route_by_quality(available)
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            return self._route_round_robin(available)

        # Default: cost optimized
        return self._route_by_cost(available)

    def get_fallback_chain(self, primary: ProviderType) -> List[ProviderType]:
        """Get fallback chain starting with primary provider."""
        available = self.provider_manager.get_available_providers()

        # Primary first, then sorted by reliability/availability
        fallback_order = [primary]

        # Add others in order of preference
        for provider in [ProviderType.GEMINI, ProviderType.GPT4, ProviderType.CLAUDE]:
            if provider != primary and provider in available:
                fallback_order.append(provider)

        return fallback_order

    def _route_by_cost(self, available: List[ProviderType]) -> ProviderType:
        """Route to cheapest provider."""
        return max(available, key=lambda p: self.provider_profiles[p]["cost_score"])

    def _route_by_latency(self, available: List[ProviderType]) -> ProviderType:
        """Route to fastest provider."""
        return max(available, key=lambda p: self.provider_profiles[p]["latency_score"])

    def _route_by_quality(self, available: List[ProviderType]) -> ProviderType:
        """Route to highest quality provider."""
        return max(available, key=lambda p: self.provider_profiles[p]["quality_score"])

    def _route_round_robin(self, available: List[ProviderType]) -> ProviderType:
        """Round-robin routing."""
        provider = available[self._round_robin_index % len(available)]
        self._round_robin_index += 1
        return provider
