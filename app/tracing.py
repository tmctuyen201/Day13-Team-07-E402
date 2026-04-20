from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
load_dotenv()

try:
    # Normal case (Langfuse v4 decorators)
    from langfuse.decorators import observe, langfuse_context

except Exception:
    # Fallback to manual tracing
    from langfuse import get_client

    langfuse = get_client()

    _current_trace = None
    _current_observation = None

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            def wrapper(*f_args, **f_kwargs):
                global _current_trace
                global _current_observation

                with langfuse.start_as_current_observation(
                    as_type="span",
                    name=func.__name__,
                ) as obs:

                    _current_trace = obs
                    _current_observation = obs

                    result = func(*f_args, **f_kwargs)

                try:
                    langfuse.flush()
                except Exception:
                    pass

                return result

            return wrapper

        return decorator

    class _DummyContext:
        """
        Fallback context compatible with Langfuse v4 API.
        """

        def update_current_trace(self, **kwargs: Any) -> None:
            global _current_trace

            try:
                print("Fallback trace update")

                if _current_trace:
                    _current_trace.update(
                        metadata=kwargs
                    )

            except Exception as e:
                print("Trace update error:", e)

        def update_current_observation(self, **kwargs: Any) -> None:
            global _current_observation

            try:
                print("Fallback observation update")

                if _current_observation:
                    _current_observation.update(
                        output=kwargs
                    )

            except Exception as e:
                print("Observation update error:", e)

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    )