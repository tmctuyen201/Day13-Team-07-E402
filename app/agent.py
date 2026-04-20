from __future__ import annotations

import time
from dataclasses import dataclass

import os

from . import metrics
from .logging_config import get_logger
from .pii import hash_user_id, summarize_text
from .tracing import langfuse_client, observe

# Import based on environment variable
USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"

if USE_OPENAI:
    from .openai_llm import OpenAILLM as LLM
    from .openai_rag import retrieve
else:
    from .mock_llm import FakeLLM as LLM
    from .mock_rag import retrieve

log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.llm = LLM(model=model)

    @observe()
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        
        # Log to Langfuse - request received (v3 pattern)
        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
        )
        
        # Log RAG retrieval
        docs = retrieve(message)
        langfuse_client.update_current_span(
            metadata={"doc_count": len(docs), "query_preview": summarize_text(message)},
        )
        
        # Log LLM generation
        prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"
        response = self.llm.generate(prompt)
        
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        # Update span with LLM usage (use metadata for usage info)
        langfuse_client.update_current_span(
            metadata={
                "tokens_in": response.usage.input_tokens,
                "tokens_out": response.usage.output_tokens,
                "model": self.model
            },
        )
        
        # Add scores to trace
        langfuse_client.score_current_trace(
            name="latency_ms",
            value=latency_ms,
        )
        langfuse_client.score_current_trace(
            name="quality_score",
            value=quality_score,
        )
        langfuse_client.score_current_trace(
            name="cost_usd",
            value=cost_usd,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        result = AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )
        
        # Manually flush to send traces immediately
        log.info("sending_log_start", service="langfuse", payload={"action": "flush_traces"})
        langfuse_client.flush()
        log.info("sending_log_end", service="langfuse", payload={"action": "flush_traces"})
        
        return result

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
