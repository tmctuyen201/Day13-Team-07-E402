#!/usr/bin/env python3
"""Test script for new features: Dashboard and OpenAI integration."""

import os
import sys
import time
from pathlib import Path

import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_chat():
    """Test chat endpoint."""
    print("\n💬 Testing chat endpoint...")
    try:
        payload = {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "feature": "qa",
            "message": "What is your refund policy?"
        }
        response = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Chat response received:")
        print(f"   Answer: {data['answer'][:100]}...")
        print(f"   Latency: {data['latency_ms']}ms")
        print(f"   Tokens: {data['tokens_in']} in, {data['tokens_out']} out")
        print(f"   Cost: ${data['cost_usd']}")
        print(f"   Quality: {data['quality_score']}")
        
        use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
        if use_openai:
            print("   🤖 Using OpenAI API")
        else:
            print("   🎭 Using Mock LLM")
        
        return True
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False


def test_dashboard_api():
    """Test dashboard API endpoint."""
    print("\n📊 Testing dashboard API...")
    try:
        # Test metrics endpoint
        response = httpx.get(f"{BASE_URL}/api/metrics", timeout=5.0)
        response.raise_for_status()
        metrics = response.json()
        
        print(f"✅ Metrics API working:")
        print(f"   Traffic: {metrics.get('traffic', 0)}")
        print(f"   Latency P95: {metrics.get('latency_p95', 0):.0f}ms")
        print(f"   Quality: {metrics.get('quality_avg', 0):.2f}")
        
        # Test SLO endpoint
        response = httpx.get(f"{BASE_URL}/api/slo", timeout=5.0)
        response.raise_for_status()
        slo = response.json()
        
        print(f"   SLO Config loaded: {len(slo.get('slis', {}))} SLIs")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard API test failed: {e}")
        return False


def test_dashboard_ui():
    """Test dashboard UI endpoint."""
    print("\n🎨 Testing dashboard UI...")
    try:
        response = httpx.get(f"{BASE_URL}/dashboard", timeout=5.0)
        response.raise_for_status()
        
        if "Observability Dashboard" in response.text and "Service Level Objectives" in response.text:
            print(f"✅ Dashboard UI is accessible at {BASE_URL}/dashboard")
            print("   Features: 6 panels + SLO table with Chart.js visualizations")
            return True
        else:
            print("❌ Dashboard UI loaded but content unexpected")
            return False
    except Exception as e:
        print(f"❌ Dashboard UI test failed: {e}")
        return False


def test_metrics():
    """Test metrics endpoint."""
    print("\n📈 Testing metrics endpoint...")
    try:
        response = httpx.get(f"{BASE_URL}/metrics", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Metrics retrieved:")
        print(f"   Total requests: {data.get('total_requests', 0)}")
        print(f"   Total errors: {data.get('total_errors', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Testing New Features")
    print("=" * 60)
    
    # Check if server is running
    print(f"\n📡 Checking if server is running at {BASE_URL}...")
    try:
        httpx.get(f"{BASE_URL}/health", timeout=2.0)
        print("✅ Server is running")
    except Exception:
        print("❌ Server is not running!")
        print("\nPlease start the server first:")
        print("  uvicorn app.main:app --reload")
        return 1
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Chat API", test_chat()))
    results.append(("Dashboard API", test_dashboard_api()))
    results.append(("Dashboard UI", test_dashboard_ui()))
    results.append(("Metrics", test_metrics()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print(f"\n🌐 Open the dashboard: {BASE_URL}/dashboard")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
