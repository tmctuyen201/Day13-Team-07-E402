from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean

METRICS_FILE = Path(os.getenv("METRICS_PATH", "data/metrics.json"))

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)
    
    # Auto-save after each request
    save_metrics()



def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1
    
    # Auto-save after error
    save_metrics()



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def save_metrics() -> None:
    """Save current metrics to file for persistence across restarts."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "traffic": TRAFFIC,
        "latencies": REQUEST_LATENCIES,
        "costs": REQUEST_COSTS,
        "tokens_in": REQUEST_TOKENS_IN,
        "tokens_out": REQUEST_TOKENS_OUT,
        "errors": dict(ERRORS),
        "quality_scores": QUALITY_SCORES,
    }
    with METRICS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_metrics() -> None:
    """Load metrics from file on startup."""
    global TRAFFIC, REQUEST_LATENCIES, REQUEST_COSTS, REQUEST_TOKENS_IN
    global REQUEST_TOKENS_OUT, ERRORS, QUALITY_SCORES
    
    if not METRICS_FILE.exists():
        return
    
    try:
        with METRICS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        TRAFFIC = data.get("traffic", 0)
        REQUEST_LATENCIES = data.get("latencies", [])
        REQUEST_COSTS = data.get("costs", [])
        REQUEST_TOKENS_IN = data.get("tokens_in", [])
        REQUEST_TOKENS_OUT = data.get("tokens_out", [])
        ERRORS = Counter(data.get("errors", {}))
        QUALITY_SCORES = data.get("quality_scores", [])
    except Exception as e:
        print(f"Warning: Failed to load metrics from {METRICS_FILE}: {e}")


def snapshot() -> dict:
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }
