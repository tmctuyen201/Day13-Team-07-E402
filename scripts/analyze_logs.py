#!/usr/bin/env python3
"""
Log Analysis Script - Member E: Technical Writer
Extracts and analyzes metrics from structured logs for reporting.

Author: Member E - Technical Writer
Metrics extracted:
- Request counts and latency percentiles (P50, P95, P99)
- Cost analysis (total and average)
- Token usage (input/output)
- Error rates and correlation IDs
"""

import json
from pathlib import Path

log_path = Path("data/logs.jsonl")

if not log_path.exists():
    print("No logs found")
    exit(0)

logs = []
for line in log_path.read_text(encoding="utf-8").splitlines():
    if line.strip():
        try:
            logs.append(json.loads(line))
        except:
            pass

# Filter API response logs
api_logs = [l for l in logs if l.get("event") == "response_sent"]

if not api_logs:
    print("No API response logs found")
    exit(0)

# Calculate metrics
total_requests = len(api_logs)
latencies = [l.get("latency_ms", 0) for l in api_logs]
costs = [l.get("cost_usd", 0) for l in api_logs]
tokens_in = [l.get("tokens_in", 0) for l in api_logs]
tokens_out = [l.get("tokens_out", 0) for l in api_logs]

# Calculate percentiles
latencies_sorted = sorted(latencies)
p50_idx = int(len(latencies_sorted) * 0.50)
p95_idx = int(len(latencies_sorted) * 0.95)
p99_idx = int(len(latencies_sorted) * 0.99)

print(f"Total requests: {total_requests}")
print(f"Latency P50: {latencies_sorted[p50_idx] if latencies_sorted else 0:.0f}ms")
print(f"Latency P95: {latencies_sorted[p95_idx] if latencies_sorted else 0:.0f}ms")
print(f"Latency P99: {latencies_sorted[p99_idx] if latencies_sorted else 0:.0f}ms")
print(f"Avg latency: {sum(latencies) / len(latencies) if latencies else 0:.1f}ms")
print(f"Total cost: ${sum(costs):.4f}")
print(f"Avg cost: ${sum(costs) / len(costs) if costs else 0:.6f}")
print(f"Total tokens in: {sum(tokens_in)}")
print(f"Total tokens out: {sum(tokens_out)}")

# Count errors
error_logs = [l for l in logs if l.get("level") == "error"]
print(f"Total errors: {len(error_logs)}")
print(f"Error rate: {len(error_logs) / total_requests * 100 if total_requests else 0:.2f}%")

# Count unique correlation IDs
correlation_ids = set(l.get("correlation_id") for l in logs if l.get("correlation_id"))
print(f"Unique correlation IDs: {len(correlation_ids)}")
