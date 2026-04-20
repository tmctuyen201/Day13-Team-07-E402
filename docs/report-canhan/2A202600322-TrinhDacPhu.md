# Báo cáo cá nhân - Trịnh Đắc Phú

## Thông tin thành viên
- **Họ tên:** Trịnh Đắc Phú
- **MSSV:** 2A202600322
- **Vai trò:** Member B — Backend Developer (Tracing & Enrichment)
- **Ngày:** 20/04/2026

---

## 1. Thông Tin Nhóm

**Tên nhóm:** VinAI Observability Team  
**Repository:** d:\project\vinai\Lab13-Observability  
**Thành viên:**
- **Member A: Trịnh Minh Công Tuyền (2A202600324)** — Logging & PII Scrubbing
- **Member B: Trịnh Đắc Phú (2A202600322) — Tôi** — Tracing & Enrichment
- **Member C: Trần Hữu Gia Huy (2A202600426)** — SLO & Alerts Configuration
- **Member D: Nguyễn Thị Cẩm Nhung (2A202600208)** — Load Test & Dashboard Development
- **Member E: Nguyễn Thị Cẩm Nhung (2A202600208)** — Demo & Report Documentation

---

## 2. Tổng Quan Dự Án

Dự án xây dựng hệ thống Observability hoàn chỉnh cho FastAPI application với các tính năng:
- Structured logging với JSON schema
- Correlation ID propagation
- PII scrubbing (6 patterns)
- Distributed tracing với Langfuse
- Real-time metrics dashboard
- SLO tracking và compliance monitoring
- Alert rules với runbook documentation

**Kết quả đạt được:**
- ✅ Validation Score: 100/100
- ✅ 75+ traces trên Langfuse
- ✅ 0 PII leaks
- ✅ Dashboard 6 panels hoạt động tốt
- ✅ Load testing thành công với 63 requests

---

## 3. Phần Việc Của Tôi — Member B: Tracing & Enrichment

### 3.1. Correlation ID Middleware (app/middleware.py)

**Mô tả công việc:**  
Triển khai `CorrelationIdMiddleware` để gắn và truyền correlation ID xuyên suốt vòng đời của mỗi request, đảm bảo khả năng trace từ đầu đến cuối.

**Chi tiết triển khai:**

```python
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear contextvars để tránh rò rỉ giữa các request
        clear_contextvars()

        # Lấy x-request-id từ header hoặc tự sinh mới
        correlation_id = request.headers.get("x-request-id") or f"req-{secrets.token_hex(4)}"

        # Bind correlation_id vào structlog contextvars
        bind_contextvars(correlation_id=correlation_id)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000)

        # Inject vào response headers
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        return response
```

**Chức năng chính:**
- Clear contextvars trước mỗi request để tránh data leakage giữa các request
- Lấy `x-request-id` từ header nếu có, hoặc tự sinh theo format `req-<8-char-hex>`
- Bind `correlation_id` vào structlog contextvars để tất cả log trong request đều có trường này
- Ghi lại `x-request-id` và `x-response-time-ms` vào response headers

**Kết quả:**
- ✅ 100% log records có correlation_id
- ✅ 75+ unique correlation IDs được tạo ra
- ✅ Response headers đầy đủ cho client tracking

**Evidence:** `app/middleware.py` (lines 1–30)

---

### 3.2. Log Enrichment (app/main.py)

**Mô tả công việc:**  
Bổ sung các trường context vào mỗi request log để tăng khả năng phân tích và debug.

**Chi tiết triển khai:**

```python
# Trong request handler
bind_contextvars(
    user_id_hash=hash_user_id(payload.user_id),
    session_id=payload.session_id,
    feature=payload.feature,
    model=settings.model,
    env=settings.env,
)
```

**Các trường enrichment:**
| Trường | Mô tả | Ví dụ |
|---|---|---|
| `user_id_hash` | SHA256 12-char hash của user_id | `a3f9c12b8e01` |
| `session_id` | Session identifier | `sess-abc123` |
| `feature` | Feature name của request | `chat`, `search` |
| `model` | LLM model đang dùng | `gpt-4o-mini` |
| `env` | Môi trường chạy | `dev`, `prod` |

**Kết quả:**
- ✅ Tất cả log records có đầy đủ enrichment fields
- ✅ 0 records thiếu context (validated bởi validate_logs.py)

**Evidence:** `app/main.py` (lines 40–60)

---

### 3.3. Langfuse Tracing (app/agent.py)

**Mô tả công việc:**  
Tích hợp distributed tracing với Langfuse để theo dõi toàn bộ pipeline xử lý request, từ RAG retrieval đến LLM generation.

**Chi tiết triển khai:**

**A. Trace Setup với @observe decorator:**

```python
@observe(name="agent.run")
def run(self, query: str, user_id: str, session_id: str) -> AgentResponse:
    langfuse_context.update_current_trace(
        user_id=hash_user_id(user_id),
        session_id=session_id,
        tags=["lab", payload.feature, settings.model],
    )
    ...
```

**B. Span Metadata:**

```python
# RAG retrieval span
langfuse_context.update_current_observation(
    metadata={
        "doc_count": len(docs),
        "query_preview": summarize_text(query, max_len=50),
    }
)

# LLM generation span
langfuse_context.update_current_observation(
    metadata={
        "tokens_in": response.usage.prompt_tokens,
        "tokens_out": response.usage.completion_tokens,
        "model": settings.model,
    }
)
```

**C. Trace Scoring:**

```python
langfuse_context.score_current_trace(
    name="latency_ms",
    value=elapsed_ms,
)
langfuse_context.score_current_trace(
    name="quality_score",
    value=quality,
)
langfuse_context.score_current_trace(
    name="cost_usd",
    value=cost,
)

# Manual flush để dữ liệu hiển thị ngay
langfuse.flush()
```

**Cấu trúc trace waterfall:**
```
agent.run()
├── rag.retrieve()   → metadata: doc_count, query_preview
└── llm.generate()  → metadata: tokens_in, tokens_out, model
    └── scores: latency_ms, quality_score, cost_usd
```

**Kết quả:**
- ✅ 75+ traces gửi lên Langfuse với metadata đầy đủ
- ✅ Mỗi trace có user_id_hash, session_id, tags
- ✅ Scores được gắn vào từng trace
- ✅ Manual flush đảm bảo dữ liệu hiển thị ngay lập tức

**Evidence:** `app/agent.py` (lines 35–95)

---

## 4. Kỹ Năng Và Công Nghệ Sử Dụng

- **Python 3.11+**: Core development
- **FastAPI / Starlette**: Middleware implementation
- **structlog**: Context variable binding
- **Langfuse SDK**: Distributed tracing với `@observe` decorator
- **secrets / hashlib**: Secure ID generation và user hashing

---

## 5. Thách Thức Và Giải Pháp

### 5.1. Context Leakage Giữa Các Request

**Thách thức:** Contextvars trong Python có thể bị rò rỉ giữa các request nếu không được clear đúng cách, dẫn đến correlation ID sai.

**Giải pháp:** Gọi `clear_contextvars()` ở đầu mỗi request trong middleware trước khi bind bất kỳ giá trị nào.

### 5.2. Trace Flush Delay

**Thách thức:** Langfuse SDK mặc định flush theo batch, khiến traces không hiển thị ngay trên dashboard.

**Giải pháp:** Gọi `langfuse.flush()` thủ công sau mỗi request để đảm bảo dữ liệu được gửi ngay lập tức.

### 5.3. Privacy Trong Tracing

**Thách thức:** Không được gửi user_id thật lên Langfuse vì lý do privacy.

**Giải pháp:** Dùng `hash_user_id()` (SHA256, 12 ký tự) để tạo định danh ẩn danh nhưng vẫn nhất quán cho cùng một user.

---

## 6. Kết Quả Đạt Được

| Hạng mục | Kết quả |
|---|---|
| Correlation ID coverage | 100% (75+ unique IDs) |
| Log enrichment fields | 5 fields (user_id_hash, session_id, feature, model, env) |
| Traces trên Langfuse | 75+ traces với đầy đủ metadata |
| Validation score | 100/100 |
| PII trong traces | 0 leaks |

---

## 7. Kết Luận

Trong lab này, tôi đã hoàn thành vai trò **Member B (Tracing & Enrichment)** với các deliverables:

- ✅ `app/middleware.py` — Correlation ID middleware hoàn chỉnh
- ✅ `app/main.py` — Log enrichment với 5 context fields
- ✅ `app/agent.py` — Langfuse tracing với span metadata và scoring

Qua lab này, tôi hiểu sâu hơn về tầm quan trọng của distributed tracing trong hệ thống production: correlation ID giúp trace một request qua nhiều service, còn Langfuse cung cấp visibility vào chất lượng và chi phí của LLM pipeline.

---

**Ngày hoàn thành:** 20/04/2026  
**Người thực hiện:** Trịnh Đắc Phú (2A202600322)  
**Vai trò:** Member B — Backend Developer (Tracing & Enrichment)
