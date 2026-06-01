"""Industry-style LLM telemetry — tokens, latency, cost (Lab 3 bonus)."""

from __future__ import annotations

from typing import Any

from src.telemetry.logger import logger

# USD per 1M tokens (approximate; update per provider billing)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek-v4-flash": (0.10, 0.20),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "mock": (0.0, 0.0),
}


class PerformanceTracker:
    def __init__(self) -> None:
        self.session_metrics: list[dict[str, Any]] = []

    def track_request(
        self,
        provider: str,
        model: str,
        usage: dict[str, int],
        latency_ms: int,
    ) -> None:
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        ratio = (
            round(completion_tokens / prompt_tokens, 3)
            if prompt_tokens > 0
            else None
        )

        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "completion_to_prompt_ratio": ratio,
            "latency_ms": latency_ms,
            "cost_estimate_usd": cost,
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        key = model.lower()
        for name, (in_price, out_price) in _MODEL_PRICING.items():
            if name in key or key in name:
                return (prompt_tokens / 1_000_000) * in_price + (
                    completion_tokens / 1_000_000
                ) * out_price
        return (prompt_tokens + completion_tokens) / 1000 * 0.001

    def session_summary(self) -> dict[str, Any]:
        if not self.session_metrics:
            return {"request_count": 0}

        latencies = [m["latency_ms"] for m in self.session_metrics]
        totals = [m["total_tokens"] for m in self.session_metrics]
        costs = [m["cost_estimate_usd"] for m in self.session_metrics]
        sorted_lat = sorted(latencies)

        def percentile(values: list[int], p: float) -> int:
            if not values:
                return 0
            idx = int(len(values) * p)
            return values[min(idx, len(values) - 1)]

        return {
            "request_count": len(self.session_metrics),
            "total_tokens": sum(totals),
            "total_cost_usd": round(sum(costs), 6),
            "latency_ms": {
                "p50": percentile(sorted_lat, 0.5),
                "p99": percentile(sorted_lat, 0.99),
                "max": max(latencies),
            },
            "avg_tokens_per_request": round(sum(totals) / len(totals), 1),
        }

    def reset(self) -> None:
        self.session_metrics.clear()


tracker = PerformanceTracker()
