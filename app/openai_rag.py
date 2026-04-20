from __future__ import annotations

import os
import time

import openai
from openai import OpenAI

from .incidents import STATE

# Enhanced corpus with more detailed information
CORPUS = {
    "refund": [
        "Refunds are available within 7 days with proof of purchase.",
        "To request a refund, contact customer support with your order number and reason for return.",
        "Refund processing typically takes 5-7 business days after approval."
    ],
    "monitoring": [
        "Metrics detect incidents, traces localize them, logs explain root cause.",
        "Use structured logging with correlation IDs to trace requests across services.",
        "Set up alerts based on SLOs to catch issues before they impact users.",
        "Distributed tracing helps identify bottlenecks in microservices architectures."
    ],
    "policy": [
        "Do not expose PII in logs. Use sanitized summaries only.",
        "All sensitive data must be encrypted at rest and in transit.",
        "Access to production logs requires approval and is audited.",
        "PII includes email addresses, phone numbers, credit cards, and government IDs."
    ],
    "observability": [
        "Observability consists of three pillars: metrics, logs, and traces.",
        "Metrics provide aggregate statistics about system behavior over time.",
        "Logs capture discrete events with detailed context.",
        "Traces show the path of requests through distributed systems."
    ],
    "latency": [
        "Tail latency (p95, p99) is often more important than average latency.",
        "Use distributed tracing to identify slow components in request paths.",
        "Cache frequently accessed data to reduce latency.",
        "Consider using CDNs for static content delivery."
    ],
    "alert": [
        "Alerts should be actionable and tied to user impact.",
        "Use multi-window, multi-burn-rate alerts for SLO violations.",
        "Avoid alert fatigue by tuning thresholds appropriately.",
        "Include runbooks in alert notifications for faster resolution."
    ]
}


class OpenAIRAG:
    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self._embeddings_cache: dict[str, list[float]] = {}

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI API with caching."""
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            self._embeddings_cache[text] = embedding
            return embedding
        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)

    def retrieve(self, message: str, top_k: int = 3) -> list[str]:
        """Retrieve relevant documents using semantic search."""
        # Simulate incidents
        if STATE["tool_fail"]:
            raise RuntimeError("Vector store timeout")
        if STATE["rag_slow"]:
            time.sleep(2.5)
        
        # Simple keyword matching fallback for common queries
        lowered = message.lower()
        matched_docs = []
        
        for key, docs in CORPUS.items():
            if key in lowered:
                matched_docs.extend(docs)
        
        if matched_docs:
            return matched_docs[:top_k]
        
        # Use semantic search with embeddings
        try:
            query_embedding = self._get_embedding(message)
            
            # Get all documents with their embeddings
            all_docs = []
            for docs in CORPUS.values():
                all_docs.extend(docs)
            
            # Calculate similarity scores
            doc_scores = []
            for doc in all_docs:
                doc_embedding = self._get_embedding(doc)
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                doc_scores.append((doc, similarity))
            
            # Sort by similarity and return top_k
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            if doc_scores and doc_scores[0][1] > 0.5:  # Threshold for relevance
                return [doc for doc, _ in doc_scores[:top_k]]
            
        except Exception:
            # Fall back to keyword matching if embedding fails
            pass
        
        return ["No domain document matched. Use general fallback answer."]


# Global instance for easy import
_rag_instance: OpenAIRAG | None = None


def get_rag() -> OpenAIRAG:
    """Get or create the global RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = OpenAIRAG()
    return _rag_instance


def retrieve(message: str) -> list[str]:
    """Convenience function for backward compatibility."""
    return get_rag().retrieve(message)
