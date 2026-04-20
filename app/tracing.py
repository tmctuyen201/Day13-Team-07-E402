from __future__ import annotations

import os
from typing import Any

# Load environment variables early
from dotenv import load_dotenv
load_dotenv()

try:
    from langfuse import observe, get_client
    
    # Get the global Langfuse client instance with faster flush settings
    langfuse_client = get_client()
    
    # Configure for immediate/faster flushing
    # The client batches events and flushes every few seconds by default
    # Calling flush() manually ensures immediate sending
        
except Exception as e:  # pragma: no cover
    print(f"Warning: Langfuse initialization failed: {e}")
    
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None
        
        def score_current_trace(self, **kwargs: Any) -> None:
            return None
        
        def flush(self) -> None:
            return None

    langfuse_client = _DummyClient()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
