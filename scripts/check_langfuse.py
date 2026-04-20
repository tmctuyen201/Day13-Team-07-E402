#!/usr/bin/env python
"""
CLI tool to check if traces were sent to Langfuse successfully.
Usage: python check_langfuse.py [options]
"""
import argparse
import os
import sys
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()


def check_connection():
    """Test if we can connect to Langfuse API"""
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not pk or not sk:
        print("[ERROR] LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in .env")
        return False
    
    try:
        print(f"[INFO] Connecting to {host}...")
        response = httpx.get(
            f"{host}/api/public/traces",
            auth=(pk, sk),
            params={"page": 1, "limit": 1},
            timeout=10.0
        )
        
        if response.status_code == 200:
            print("[OK] Connected to Langfuse API successfully!")
            return True
        else:
            print(f"[ERROR] API returned status code: {response.status_code}")
            print(response.text[:200])
            return False
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False


def get_traces(limit=10, user_id=None):
    """Get recent traces from Langfuse"""
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    try:
        params = {"page": 1, "limit": limit}
        if user_id:
            params["userId"] = user_id
        
        response = httpx.get(
            f"{host}/api/public/traces",
            auth=(pk, sk),
            params=params,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"[ERROR] API Error: {response.status_code}")
            print(response.text[:200])
            return []
    except Exception as e:
        print(f"[ERROR] Error fetching traces: {e}")
        return []


def format_timestamp(ts):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return f"{int(diff.total_seconds())}s ago"
        elif diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() / 60)}m ago"
        elif diff < timedelta(days=1):
            return f"{int(diff.total_seconds() / 3600)}h ago"
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts


def display_trace(trace, index=None):
    """Display trace information"""
    trace_id = trace.get("id", "unknown")
    name = trace.get("name", "unnamed")
    timestamp = trace.get("timestamp", "")
    user_id = trace.get("userId", "N/A")
    session_id = trace.get("sessionId", "N/A")
    tags = trace.get("tags", [])
    
    prefix = f"[{index}] " if index is not None else ""
    
    print(f"\n{prefix}{'='*65}")
    print(f"Trace: {name}")
    print(f"{'='*65}")
    print(f"  ID:         {trace_id}")
    print(f"  Time:       {format_timestamp(timestamp)}")
    print(f"  User:       {user_id}")
    print(f"  Session:    {session_id}")
    if tags:
        print(f"  Tags:       {', '.join(tags)}")


def main():
    parser = argparse.ArgumentParser(
        description="Check if traces were sent to Langfuse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check connection
  python check_langfuse.py --check

  # List recent traces
  python check_langfuse.py --list

  # List traces for specific user
  python check_langfuse.py --list --user-id test_user

  # List more traces
  python check_langfuse.py --list --limit 20
        """
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check connection to Langfuse API"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List recent traces"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of traces to fetch (default: 10)"
    )
    
    parser.add_argument(
        "--user-id",
        type=str,
        help="Filter traces by user ID (hashed)"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print("=" * 70)
    print("Langfuse Trace Checker")
    print("=" * 70)
    print(f"Host: {host}")
    print(f"Public Key: {pk[:20] if pk else 'NOT SET'}...")
    print("=" * 70)
    
    # Check connection
    if args.check:
        check_connection()
    
    # List traces
    elif args.list:
        print(f"\n[INFO] Fetching {args.limit} most recent traces...")
        if args.user_id:
            print(f"   Filtering by user_id: {args.user_id}")
        
        if not check_connection():
            sys.exit(1)
        
        traces = get_traces(limit=args.limit, user_id=args.user_id)
        
        if traces:
            print(f"\n[OK] Found {len(traces)} trace(s):")
            for i, trace in enumerate(traces, 1):
                display_trace(trace, index=i)
            
            print("\n" + "=" * 70)
            print(f"[OK] Total: {len(traces)} trace(s)")
            print("=" * 70)
            print(f"\nView in dashboard: {host}")
        else:
            print("\n[WARNING] No traces found")
            print("\nPossible reasons:")
            print("  1. No traces have been sent yet")
            print("  2. Traces are still being processed (wait a few seconds)")
            print("  3. User ID filter doesn't match any traces")
            print("\nTry:")
            print("  1. Run: python test_flush_logs.py")
            print("  2. Wait 5 seconds")
            print("  3. Check: python check_langfuse.py --list")


if __name__ == "__main__":
    main()
