#!/usr/bin/env python3
"""
Test script to verify metrics persistence across restarts.

Usage:
    python scripts/test_persistence.py
"""

import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
METRICS_FILE = Path("data/metrics.json")


def send_test_requests(count: int = 5) -> None:
    """Send test requests to generate metrics."""
    print(f"\n📤 Sending {count} test requests...")
    
    with httpx.Client(timeout=30.0) as client:
        for i in range(count):
            try:
                payload = {
                    "user_id": f"test_user_{i}",
                    "session_id": "test_session",
                    "feature": "qa",
                    "message": f"Test question {i+1}"
                }
                r = client.post(f"{BASE_URL}/chat", json=payload)
                print(f"  ✓ Request {i+1}: {r.status_code} - {r.json().get('correlation_id')}")
                time.sleep(0.2)
            except Exception as e:
                print(f"  ✗ Request {i+1} failed: {e}")


def get_metrics() -> dict:
    """Fetch current metrics from API."""
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{BASE_URL}/metrics")
            return r.json()
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}


def check_metrics_file() -> dict:
    """Read metrics from file."""
    if not METRICS_FILE.exists():
        return {}
    
    with METRICS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    print("=" * 60)
    print("🧪 METRICS PERSISTENCE TEST")
    print("=" * 60)
    
    # Step 1: Check initial state
    print("\n📊 Step 1: Check initial metrics")
    initial_metrics = get_metrics()
    print(f"  Traffic: {initial_metrics.get('traffic', 0)}")
    print(f"  Total Cost: ${initial_metrics.get('total_cost_usd', 0):.4f}")
    
    # Step 2: Send test requests
    send_test_requests(5)
    
    # Step 3: Check updated metrics
    print("\n📊 Step 2: Check updated metrics")
    updated_metrics = get_metrics()
    print(f"  Traffic: {updated_metrics.get('traffic', 0)}")
    print(f"  Total Cost: ${updated_metrics.get('total_cost_usd', 0):.4f}")
    print(f"  Latency P95: {updated_metrics.get('latency_p95', 0):.0f}ms")
    print(f"  Quality Avg: {updated_metrics.get('quality_avg', 0):.2f}")
    
    # Step 4: Check file persistence
    print("\n💾 Step 3: Check metrics file")
    file_data = check_metrics_file()
    if file_data:
        print(f"  ✓ File exists: {METRICS_FILE}")
        print(f"  ✓ Traffic in file: {file_data.get('traffic', 0)}")
        print(f"  ✓ Latencies count: {len(file_data.get('latencies', []))}")
    else:
        print(f"  ✗ File not found: {METRICS_FILE}")
    
    # Step 5: Instructions
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)
    print("\n📝 Next steps to verify persistence:")
    print("  1. Stop the server (Ctrl+C)")
    print("  2. Restart: uvicorn app.main:app --reload")
    print("  3. Check metrics: curl http://127.0.0.1:8000/metrics")
    print("  4. Verify traffic is still:", updated_metrics.get('traffic', 0))
    print("\n🔄 To reset metrics:")
    print("  curl -X POST http://127.0.0.1:8000/metrics/reset")
    print()


if __name__ == "__main__":
    main()
