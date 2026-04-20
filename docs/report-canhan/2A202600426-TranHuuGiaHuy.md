# Báo Cáo Cá Nhân - Day 13 Observability Lab

**Họ và tên:** Trần Hữu Gia Huy  
**MSSV:** 2A202600426  
**Vai trò:** Member C — DevOps Engineer (SLO & Alerts Configuration)  
**Ngày:** 20/04/2026

---

## 1. Thông Tin Nhóm

**Tên nhóm:** VinAI Observability Team  
**Repository:** d:\project\vinai\Lab13-Observability  
**Thành viên:**
- **Member A: Trịnh Minh Công Tuyền (2A202600324)** — Logging & PII Scrubbing
- **Member B: Trịnh Đắc Phú (2A202600322)** — Tracing & Enrichment
- **Member C: Trần Hữu Gia Huy (2A202600426) — Tôi** — SLO & Alerts Configuration
- **Member D: Nguyễn Thị Cẩm Nhung (2A202600208)** — Load Test & Dashboard Development
- **Member E: Nguyễn Thị Cẩm Nhung (2A202600208)** — Demo & Report Documentation

---

## 2. Tổng Quan Dự Án

Dự án xây dựng hệ thống Observability hoàn chỉnh cho FastAPI application với các tính năng:
- Structured logging với JSON schema và PII scrubbing
- Correlation ID propagation
- Distributed tracing với Langfuse
- Real-time metrics dashboard (6 panels)
- SLO tracking và compliance monitoring
- Alert rules với runbook documentation

**Kết quả đạt được:**
- ✅ Validation Score: 100/100
- ✅ 75+ traces trên Langfuse
- ✅ 0 PII leaks
- ✅ Dashboard 6 panels hoạt động tốt
- ✅ SLO configuration đầy đủ với 4 SLIs
- ✅ Alert rules với runbook documentation

---

## 3. Phần Việc Của Tôi — Member C: SLO & Alerts Configuration

### 3.1. SLO Configuration (config/slo.yaml)

**Mô tả công việc:**  
Định nghĩa Service Level Objectives (SLOs) cho hệ thống, bao gồm 4 SLIs với các ngưỡng mục tiêu cụ thể, phục vụ cho việc tracking compliance trên dashboard và kích hoạt alerts.

**Chi tiết triển khai:**

```yaml
service: day13-observability-lab
window: 28d
slis:
  latency_p95_ms:
    objective: 3000
    target: 99.5
    note: Replace with your group's target
  error_rate_pct:
    objective: 2
    target: 99.0
  daily_cost_usd:
    objective: 2.5
    target: 100.0
  quality_score_avg:
    objective: 0.75
    target: 95.0
```

**4 SLIs được định nghĩa:**

| SLI | Objective (Ngưỡng) | Target (%) | Cửa sổ | Ý nghĩa |
|---|---:|---:|---|---|
| `latency_p95_ms` | < 3000 ms | 99.5% | 28 ngày | P95 latency không vượt 3 giây |
| `error_rate_pct` | < 2% | 99.0% | 28 ngày | Tỷ lệ lỗi dưới 2% |
| `daily_cost_usd` | < $2.50/ngày | 100.0% | 28 ngày | Chi phí API không vượt ngân sách |
| `quality_score_avg` | > 0.75 | 95.0% | 28 ngày | Điểm chất lượng trung bình đạt yêu cầu |

**Lý do chọn các ngưỡng này:**
- **Latency P95 < 3000ms**: Đây là ngưỡng trải nghiệm người dùng chấp nhận được cho chatbot AI. P95 thay vì P50 để đảm bảo cả tail latency được kiểm soát.
- **Error Rate < 2%**: Tiêu chuẩn phổ biến cho production API. Trên 2% ảnh hưởng đáng kể đến UX.
- **Daily Cost < $2.50**: Ngân sách hợp lý cho lab environment với GPT-4o-mini.
- **Quality Score > 0.75**: Ngưỡng tối thiểu để câu trả lời được coi là có ích (heuristic score từ 0–1).

**Kết quả SLO hiện tại (từ dashboard):**

| SLI | Giá trị hiện tại | Trạng thái | Compliance |
|---|---:|---|---:|
| Latency P95 | 2685 ms | ✅ Good | 89.5% |
| Error Rate | 15.87% | ❌ Critical | 0% |
| Daily Cost | $0.117 | ✅ Good | 95.3% |
| Quality Score | 0.88 | ✅ Good | 117.3% |

**Evidence:** `config/slo.yaml`

---

### 3.2. Alert Rules Configuration (config/alert_rules.yaml)

**Mô tả công việc:**  
Thiết lập các alert rules để tự động phát hiện và thông báo khi hệ thống vi phạm SLO hoặc có dấu hiệu bất thường.

**Chi tiết triển khai:**

```yaml
alerts:
  - name: high_latency_p95
    severity: P2
    condition: latency_p95_ms > 5000 for 30m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#1-high-latency-p95

  - name: high_error_rate
    severity: P1
    condition: error_rate_pct > 5 for 5m
    type: symptom-based
    owner: team-oncall
    runbook: docs/alerts.md#2-high-error-rate

  - name: cost_budget_spike
    severity: P2
    condition: hourly_cost_usd > 2x_baseline for 15m
    type: symptom-based
    owner: finops-owner
    runbook: docs/alerts.md#3-cost-budget-spike
```

**3 Alert Rules được cấu hình:**

#### Alert 1: High Latency P95
| Thuộc tính | Giá trị |
|---|---|
| Tên | `high_latency_p95` |
| Severity | P2 (Warning) |
| Điều kiện | `latency_p95_ms > 5000` trong 30 phút |
| Loại | Symptom-based |
| Owner | `team-oncall` |
| Runbook | `docs/alerts.md#1-high-latency-p95` |

**Lý do thiết kế:** Ngưỡng 5000ms (cao hơn SLO objective 3000ms) để tránh false positive khi có spike ngắn. Cửa sổ 30 phút đảm bảo đây là vấn đề kéo dài, không phải tạm thời.

#### Alert 2: High Error Rate
| Thuộc tính | Giá trị |
|---|---|
| Tên | `high_error_rate` |
| Severity | P1 (Critical) |
| Điều kiện | `error_rate_pct > 5` trong 5 phút |
| Loại | Symptom-based |
| Owner | `team-oncall` |
| Runbook | `docs/alerts.md#2-high-error-rate` |

**Lý do thiết kế:** P1 vì lỗi ảnh hưởng trực tiếp đến người dùng. Cửa sổ 5 phút ngắn để phản ứng nhanh. Ngưỡng 5% (cao hơn SLO 2%) để phân biệt với noise bình thường.

#### Alert 3: Cost Budget Spike
| Thuộc tính | Giá trị |
|---|---|
| Tên | `cost_budget_spike` |
| Severity | P2 (Warning) |
| Điều kiện | `hourly_cost_usd > 2x_baseline` trong 15 phút |
| Loại | Symptom-based |
| Owner | `finops-owner` |
| Runbook | `docs/alerts.md#3-cost-budget-spike` |

**Lý do thiết kế:** Dùng relative threshold (2x baseline) thay vì absolute để thích nghi với traffic tự nhiên. Owner là `finops-owner` vì đây là vấn đề tài chính, không phải kỹ thuật thuần túy.

**Evidence:** `config/alert_rules.yaml`

---

### 3.3. Runbook Documentation (docs/alerts.md)

**Mô tả công việc:**  
Viết runbook cho từng alert, cung cấp hướng dẫn cụ thể để on-call engineer xử lý sự cố nhanh chóng và đúng cách.

**Cấu trúc mỗi runbook entry:**
1. **Severity** — Mức độ ưu tiên
2. **Trigger** — Điều kiện kích hoạt cụ thể
3. **Impact** — Ảnh hưởng đến người dùng/hệ thống
4. **First checks** — Các bước kiểm tra đầu tiên (có thứ tự ưu tiên)
5. **Mitigation** — Các hành động khắc phục

**Runbook 1 — High Latency P95:**
```markdown
## 1. High latency P95
- Severity: P2
- Trigger: latency_p95_ms > 5000 for 30m
- Impact: tail latency breaches SLO
- First checks:
  1. Open top slow traces in the last 1h
  2. Compare RAG span vs LLM span
  3. Check if incident toggle `rag_slow` is enabled
- Mitigation:
  - truncate long queries
  - fallback retrieval source
  - lower prompt size
```

**Runbook 2 — High Error Rate:**
```markdown
## 2. High error rate
- Severity: P1
- Trigger: error_rate_pct > 5 for 5m
- Impact: users receive failed responses
- First checks:
  1. Group logs by error_type
  2. Inspect failed traces
  3. Determine whether failures are LLM, tool, or schema related
- Mitigation:
  - rollback latest change
  - disable failing tool
  - retry with fallback model
```

**Runbook 3 — Cost Budget Spike:**
```markdown
## 3. Cost budget spike
- Severity: P2
- Trigger: hourly_cost_usd > 2x_baseline for 15m
- Impact: burn rate exceeds budget
- First checks:
  1. Split traces by feature and model
  2. Compare tokens_in/tokens_out
  3. Check if cost_spike incident was enabled
- Mitigation:
  - shorten prompts
  - route easy requests to cheaper model
  - apply prompt cache
```

**Nguyên tắc thiết kế runbook:**
- **Actionable**: Mỗi bước kiểm tra đều có thể thực hiện ngay, không mơ hồ
- **Ordered**: Các bước được sắp xếp từ nhanh/dễ đến phức tạp hơn
- **Linked**: Mỗi alert rule trỏ thẳng đến section runbook tương ứng qua anchor link
- **Contextual**: Mitigation steps phù hợp với kiến trúc RAG + LLM của hệ thống

**Evidence:** `docs/alerts.md`

---

### 3.4. Incident Injection Testing

**Mô tả công việc:**  
Sử dụng hệ thống incident injection có sẵn để kiểm tra xem alert rules và SLO thresholds có hoạt động đúng không.

**Kịch bản test — `rag_slow`:**

```bash
# Kích hoạt incident
POST /incidents/rag_slow/enable

# Quan sát trên dashboard:
# - Latency P95 tăng từ ~150ms lên ~2670ms
# - Tiệm cận ngưỡng SLO 3000ms
# - Alert high_latency_p95 sẽ trigger nếu vượt 5000ms trong 30 phút

# Tắt incident
POST /incidents/rag_slow/disable
```

**Kết quả quan sát:**
- Latency P95 tăng từ ~150ms → ~2670ms khi `rag_slow` được bật
- Dashboard phản ánh thay đổi trong real-time
- Trace trên Langfuse cho thấy RAG span chiếm 2.5s
- Sau khi tắt incident, latency trở về baseline

**Evidence:** Incident system tại `app/incidents.py`, test script tại `scripts/inject_incident.py`

---

## 4. Kỹ Năng Và Công Nghệ Sử Dụng

- **YAML**: Cấu hình SLO và alert rules
- **SLO/SLI/SLA concepts**: Hiểu và áp dụng Google SRE methodology
- **Alert design patterns**: Symptom-based alerting, multi-window strategy
- **Runbook writing**: Technical documentation cho on-call engineers
- **Incident management**: Inject và verify alert thresholds

---

## 5. Thách Thức Và Giải Pháp

### 5.1. Chọn Ngưỡng Alert Phù Hợp

**Thách thức:** Nếu ngưỡng alert quá thấp → nhiều false positive, on-call bị alert fatigue. Nếu quá cao → phát hiện vấn đề chậm.

**Giải pháp:** Đặt ngưỡng alert cao hơn SLO objective (ví dụ: SLO latency là 3000ms, alert tại 5000ms) và thêm cửa sổ thời gian (30 phút) để lọc spike ngắn hạn.

### 5.2. Phân Loại Severity

**Thách thức:** Cần phân biệt rõ P1 (cần xử lý ngay) và P2 (cần xử lý trong giờ làm việc).

**Giải pháp:** P1 chỉ dành cho các vấn đề ảnh hưởng trực tiếp đến người dùng (error rate cao). P2 cho các vấn đề performance và cost có thể xử lý trong vài giờ.

### 5.3. Liên Kết Alert Với Runbook

**Thách thức:** On-call engineer cần tìm runbook nhanh khi nhận alert lúc 3 giờ sáng.

**Giải pháp:** Mỗi alert rule có trường `runbook` trỏ thẳng đến anchor link trong `docs/alerts.md`, ví dụ: `docs/alerts.md#1-high-latency-p95`.

---

## 6. Kết Quả Đạt Được

| Hạng mục | Kết quả |
|---|---|
| SLIs được định nghĩa | 4 (latency, error rate, cost, quality) |
| Alert rules được cấu hình | 3 rules với severity P1/P2 |
| Runbook entries | 3 entries với first-checks và mitigation |
| SLO compliance (latency) | 89.5% — Good |
| SLO compliance (cost) | 95.3% — Good |
| SLO compliance (quality) | 117.3% — Exceeds target |
| Incident testing | rag_slow scenario verified |

---

## 7. Kết Luận

Trong lab này, tôi đã hoàn thành vai trò **Member C (SLO & Alerts Configuration)** với các deliverables:

- ✅ `config/slo.yaml` — 4 SLIs với objectives và targets rõ ràng
- ✅ `config/alert_rules.yaml` — 3 alert rules với severity, owner, và runbook links
- ✅ `docs/alerts.md` — Runbook documentation đầy đủ cho 3 alerts

Qua lab này, tôi hiểu sâu hơn về tầm quan trọng của SLO trong production systems: SLO không chỉ là con số mục tiêu mà còn là nền tảng để thiết kế alert, ưu tiên incident response, và đưa ra quyết định kỹ thuật. Việc kết hợp SLO với runbook giúp team phản ứng nhanh và nhất quán khi có sự cố.

---

## 8. Phụ Lục

### 8.1. Files Tạo/Chỉnh Sửa

| File | Mô tả |
|---|---|
| `config/slo.yaml` | SLO configuration với 4 SLIs |
| `config/alert_rules.yaml` | 3 alert rules với severity và runbook links |
| `docs/alerts.md` | Runbook documentation cho 3 alerts |

### 8.2. Commands Tham Khảo

```bash
# Kiểm tra SLO hiện tại
curl http://localhost:8000/api/slo

# Xem metrics để so sánh với SLO
curl http://localhost:8000/api/metrics

# Test alert threshold — kích hoạt rag_slow
curl -X POST http://localhost:8000/incidents/rag_slow/enable

# Quan sát latency tăng trên dashboard
open http://localhost:8000/dashboard

# Tắt incident
curl -X POST http://localhost:8000/incidents/rag_slow/disable
```

### 8.3. Evidence Links

- SLO Config: `config/slo.yaml`
- Alert Rules: `config/alert_rules.yaml`
- Runbook: `docs/alerts.md`
- Dashboard SLO Table: http://localhost:8000/dashboard
- API SLO: http://localhost:8000/api/slo

---

**Ngày hoàn thành:** 20/04/2026  
**Người thực hiện:** Trần Hữu Gia Huy (2A202600426)  
**Vai trò:** Member C — DevOps Engineer (SLO & Alerts Configuration)
