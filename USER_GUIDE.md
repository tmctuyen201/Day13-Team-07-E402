# 📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG OBSERVABILITY LAB

## 📋 Mục lục
1. [Giới thiệu](#giới-thiệu)
2. [Cài đặt](#cài-đặt)
3. [Khởi động hệ thống](#khởi-động-hệ-thống)
4. [API Documentation](#api-documentation)
5. [Dashboard](#dashboard)
6. [Scripts & Tools](#scripts--tools)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Giới thiệu

Hệ thống Observability Lab là một ứng dụng FastAPI được thiết kế để demo các khái niệm về:
- **Structured Logging**: Ghi log có cấu trúc JSON
- **Distributed Tracing**: Theo dõi request qua Langfuse
- **Metrics**: Thu thập và hiển thị metrics
- **PII Scrubbing**: Che giấu thông tin cá nhân
- **SLO Tracking**: Theo dõi Service Level Objectives
- **Incident Simulation**: Mô phỏng các sự cố

---

## 🔧 Cài đặt

### Yêu cầu hệ thống
- Python 3.10+
- pip hoặc uv package manager

### Bước 1: Clone repository
```bash
cd d:\project\vinai\Lab13-Observability
```

### Bước 2: Tạo virtual environment
```bash
python -m venv .venv
```

### Bước 3: Kích hoạt virtual environment
**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### Bước 4: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 5: Cấu hình environment variables
```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:
```env
# App Configuration
APP_ENV=dev
APP_NAME=day13-observability-lab
LOG_LEVEL=INFO
LOG_PATH=data/logs.jsonl
AUDIT_LOG_PATH=data/audit.jsonl

# Langfuse (Optional - for tracing)
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key
LANGFUSE_HOST=https://cloud.langfuse.com

# OpenAI (Optional - for real AI)
OPENAI_API_KEY=sk-your-openai-key
USE_OPENAI=false
```

---

## 🚀 Khởi động hệ thống

### Khởi động server
```bash
uvicorn app.main:app --reload
```

Server sẽ chạy tại: **http://localhost:8000**

### Kiểm tra server đang chạy
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "ok": true,
  "tracing_enabled": true,
  "incidents": {
    "rag_slow": false,
    "tool_fail": false,
    "cost_spike": false
  }
}
```

---

## 📡 API Documentation

### 1. Health Check

**Endpoint:** `GET /health`

**Mô tả:** Kiểm tra trạng thái hệ thống

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "ok": true,
  "tracing_enabled": true,
  "incidents": {
    "rag_slow": false,
    "tool_fail": false,
    "cost_spike": false
  }
}
```

**Response Fields:**
- `ok` (boolean): Trạng thái hệ thống
- `tracing_enabled` (boolean): Langfuse tracing có được bật không
- `incidents` (object): Trạng thái các incident đang được inject

---

### 2. Chat API

**Endpoint:** `POST /chat`

**Mô tả:** Gửi câu hỏi và nhận câu trả lời từ AI agent

**Request Body:**
```json
{
  "user_id": "u_team_01",
  "session_id": "s_demo_01",
  "feature": "qa",
  "message": "What is your refund policy?"
}
```

**Request Fields:**
- `user_id` (string, required): ID người dùng
- `session_id` (string, required): ID phiên làm việc
- `feature` (string, optional): Loại feature ("qa" hoặc "summary"), mặc định "qa"
- `message` (string, required): Câu hỏi của người dùng (tối thiểu 1 ký tự)

**cURL Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "session_id": "session_456",
    "feature": "qa",
    "message": "What is your refund policy?"
  }'
```

**Response:**
```json
{
  "answer": "Refunds are available within 7 days with proof of purchase...",
  "correlation_id": "req-a1b2c3d4",
  "latency_ms": 152,
  "tokens_in": 37,
  "tokens_out": 140,
  "cost_usd": 0.002211,
  "quality_score": 0.7
}
```

**Response Fields:**
- `answer` (string): Câu trả lời từ AI
- `correlation_id` (string): ID để trace request (format: req-XXXXXXXX)
- `latency_ms` (integer): Thời gian xử lý (milliseconds)
- `tokens_in` (integer): Số token input
- `tokens_out` (integer): Số token output
- `cost_usd` (float): Chi phí ước tính (USD)
- `quality_score` (float): Điểm chất lượng (0.0 - 1.0)

**Response Headers:**
- `x-request-id`: Correlation ID
- `x-response-time-ms`: Thời gian xử lý

**Error Response (500):**
```json
{
  "detail": "RuntimeError"
}
```

---

### 3. Metrics

**Endpoint:** `GET /metrics`

**Mô tả:** Lấy metrics tổng hợp của hệ thống

**Request:**
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "traffic": 42,
  "latency_p50": 152.0,
  "latency_p95": 165.0,
  "latency_p99": 180.0,
  "avg_cost_usd": 0.0021,
  "total_cost_usd": 0.0882,
  "tokens_in_total": 1554,
  "tokens_out_total": 5880,
  "error_breakdown": {
    "RuntimeError": 2
  },
  "quality_avg": 0.75
}
```

**Response Fields:**
- `traffic` (integer): Tổng số request
- `latency_p50` (float): Latency percentile 50 (median)
- `latency_p95` (float): Latency percentile 95
- `latency_p99` (float): Latency percentile 99
- `avg_cost_usd` (float): Chi phí trung bình mỗi request
- `total_cost_usd` (float): Tổng chi phí
- `tokens_in_total` (integer): Tổng token input
- `tokens_out_total` (integer): Tổng token output
- `error_breakdown` (object): Phân loại lỗi theo type
- `quality_avg` (float): Điểm chất lượng trung bình

**Lưu ý:** Metrics được lưu trong memory, sẽ reset khi restart server.

---

### 4. Dashboard

**Endpoint:** `GET /dashboard`

**Mô tả:** Hiển thị dashboard với 6 panels và SLO table

**Request:**
```bash
# Mở trong browser
http://localhost:8000/dashboard
```

**Features:**
- 6 metric panels với Chart.js visualizations
- SLO compliance table
- Auto-refresh (15 giây)
- Status indicators (Good/Warning/Critical)
- Real-time updates

---

### 5. Dashboard API - Metrics

**Endpoint:** `GET /api/metrics`

**Mô tả:** API endpoint cho dashboard (giống /metrics)

**Request:**
```bash
curl http://localhost:8000/api/metrics
```

**Response:** Giống endpoint `/metrics`

---

### 6. Dashboard API - SLO

**Endpoint:** `GET /api/slo`

**Mô tả:** Lấy cấu hình SLO từ config/slo.yaml

**Request:**
```bash
curl http://localhost:8000/api/slo
```

**Response:**
```json
{
  "service": "day13-observability-lab",
  "window": "28d",
  "slis": {
    "latency_p95_ms": {
      "objective": 3000,
      "target": 99.5,
      "note": "Replace with your group's target"
    },
    "error_rate_pct": {
      "objective": 2,
      "target": 99.0
    },
    "daily_cost_usd": {
      "objective": 2.5,
      "target": 100.0
    },
    "quality_score_avg": {
      "objective": 0.75,
      "target": 95.0
    }
  }
}
```

**Response Fields:**
- `service` (string): Tên service
- `window` (string): Thời gian tracking (28d = 28 ngày)
- `slis` (object): Service Level Indicators
  - `objective` (number): Ngưỡng mục tiêu
  - `target` (number): % compliance mục tiêu
  - `note` (string, optional): Ghi chú

---

### 7. Dashboard API - Logs

**Endpoint:** `GET /api/logs`

**Mô tả:** Lấy logs từ file data/logs.jsonl

**Query Parameters:**
- `limit` (integer, optional): Số lượng logs (10-1000), mặc định 100
- `level` (string, optional): Filter theo level (info, warning, error, critical)

**Request:**
```bash
# Lấy 50 logs mới nhất
curl http://localhost:8000/api/logs?limit=50

# Lấy chỉ error logs
curl http://localhost:8000/api/logs?level=error

# Lấy 20 warning logs
curl http://localhost:8000/api/logs?level=warning&limit=20
```

**Response:**
```json
{
  "logs": [
    {
      "ts": "2026-04-20T07:20:03.899367Z",
      "level": "info",
      "service": "api",
      "event": "request_received",
      "correlation_id": "req-3676f6e7",
      "user_id_hash": "64f6ec689229",
      "session_id": "s05",
      "feature": "qa",
      "model": "gpt-4o-mini",
      "env": "dev",
      "payload": {
        "message_preview": "Here is my phone [REDACTED_PHONE_VN], what should be logged?"
      }
    }
  ],
  "stats": {
    "total": 50,
    "info": 45,
    "warning": 3,
    "error": 2,
    "critical": 0
  }
}
```

---

### 8. Enable Incident

**Endpoint:** `POST /incidents/{name}/enable`

**Mô tả:** Bật một incident để test error handling

**Path Parameters:**
- `name` (string): Tên incident (rag_slow, tool_fail, cost_spike)

**Request:**
```bash
curl -X POST http://localhost:8000/incidents/rag_slow/enable
```

**Response:**
```json
{
  "ok": true,
  "incidents": {
    "rag_slow": true,
    "tool_fail": false,
    "cost_spike": false
  }
}
```

**Available Incidents:**
- `rag_slow`: RAG retrieval chậm 2.5 giây
- `tool_fail`: Vector store timeout
- `cost_spike`: Sử dụng model đắt hơn (GPT-4o thay vì GPT-4o-mini)

**Error Response (404):**
```json
{
  "detail": "Unknown incident: invalid_name"
}
```

---

### 9. Disable Incident

**Endpoint:** `POST /incidents/{name}/disable`

**Mô tả:** Tắt một incident

**Path Parameters:**
- `name` (string): Tên incident

**Request:**
```bash
curl -X POST http://localhost:8000/incidents/rag_slow/disable
```

**Response:**
```json
{
  "ok": true,
  "incidents": {
    "rag_slow": false,
    "tool_fail": false,
    "cost_spike": false
  }
}
```

---

### 10. API Documentation (Swagger)

**Endpoint:** `GET /docs`

**Mô tả:** Interactive API documentation (Swagger UI)

**Request:**
```bash
# Mở trong browser
http://localhost:8000/docs
```

**Features:**
- Interactive API testing
- Request/Response schemas
- Try it out functionality

---

### 11. Alternative API Documentation (ReDoc)

**Endpoint:** `GET /redoc`

**Mô tả:** Alternative API documentation (ReDoc)

**Request:**
```bash
# Mở trong browser
http://localhost:8000/redoc
```

---

## 📊 Dashboard

### Truy cập Dashboard
```
http://localhost:8000/dashboard
```

### 6 Metric Panels

#### 1. Latency Percentiles
- **Hiển thị:** P50, P95, P99 latency
- **Đơn vị:** milliseconds (ms)
- **Chart:** Line chart
- **SLO Line:** 3000ms threshold
- **Status:** Good (< 2400ms), Warning (2400-3000ms), Critical (> 3000ms)

#### 2. Traffic (Requests)
- **Hiển thị:** Tổng số request
- **Đơn vị:** total requests
- **Chart:** Bar chart
- **Status:** Always Good (informational)

#### 3. Error Rate
- **Hiển thị:** % lỗi
- **Đơn vị:** % error rate
- **Chart:** Doughnut chart (Success vs Errors)
- **SLO Line:** 2% threshold
- **Status:** Good (< 1%), Warning (1-2%), Critical (> 2%)

#### 4. Cost Over Time
- **Hiển thị:** Tổng chi phí
- **Đơn vị:** USD (total)
- **Chart:** Line chart
- **SLO Line:** $2.50/day threshold
- **Status:** Good (< $2.00), Warning ($2.00-$2.50), Critical (> $2.50)

#### 5. Token Usage
- **Hiển thị:** Tokens input và output
- **Đơn vị:** total tokens
- **Chart:** Bar chart (Input vs Output)
- **Status:** Always Good (informational)

#### 6. Quality Score
- **Hiển thị:** Điểm chất lượng trung bình
- **Đơn vị:** average score (0-1)
- **Chart:** Line chart
- **SLO Line:** 0.75 threshold
- **Status:** Good (≥ 0.75), Warning (0.68-0.75), Critical (< 0.68)

### SLO Table

Hiển thị 4 metrics với:
- **Metric Name:** Tên metric
- **Current Value:** Giá trị hiện tại
- **Objective:** Ngưỡng mục tiêu
- **Target:** % compliance mục tiêu
- **Status:** Good/Warning/Critical badge
- **Compliance:** % với progress bar

### Dashboard Controls

- **Auto-refresh checkbox:** Bật/tắt auto-refresh (15 giây)
- **Refresh button:** Refresh thủ công
- **Responsive:** Tự động điều chỉnh theo màn hình

---

## 🛠️ Scripts & Tools

### 1. Load Test

**File:** `scripts/load_test.py`

**Mô tả:** Generate traffic để test hệ thống

**Usage:**
```bash
# Basic load test
python scripts/load_test.py

# With concurrency
python scripts/load_test.py --concurrency 5
```

**Options:**
- `--concurrency N`: Số request đồng thời (mặc định: 1)

**Output:**
```
[200] req-abc123 | qa | 152.3ms
[200] req-def456 | summary | 165.7ms
...
```

---

### 2. Validate Logs

**File:** `scripts/validate_logs.py`

**Mô tả:** Kiểm tra logs có đúng schema không

**Usage:**
```bash
python scripts/validate_logs.py
```

**Output:**
```
--- Lab Verification Results ---
Total log records analyzed: 235
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 75
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```

**Checks:**
- Required fields: ts, level, service, event, correlation_id
- Enrichment fields: user_id_hash, session_id, feature, model
- PII leaks: @ symbol, credit card numbers
- Correlation ID uniqueness

---

### 3. Inject Incident

**File:** `scripts/inject_incident.py`

**Mô tả:** Inject incidents để test error handling

**Usage:**
```bash
# Enable incident
python scripts/inject_incident.py --scenario rag_slow

# Disable incident
python scripts/inject_incident.py --scenario rag_slow --disable
```

**Available Scenarios:**
- `rag_slow`: RAG retrieval chậm
- `tool_fail`: Vector store timeout
- `cost_spike`: Sử dụng model đắt hơn

---

### 4. Analyze Logs

**File:** `scripts/analyze_logs.py`

**Mô tả:** Phân tích logs và extract metrics

**Usage:**
```bash
python scripts/analyze_logs.py
```

**Output:**
```
Total requests: 63
Latency P50: 161ms
Latency P95: 2685ms
Latency P99: 12748ms
Avg latency: 1068.5ms
Total cost: $0.1170
Avg cost: $0.001856
Total tokens in: 2610
Total tokens out: 7275
Total errors: 10
Error rate: 15.87%
Unique correlation IDs: 75
```

---

### 5. Test Features

**File:** `scripts/test_features.py`

**Mô tả:** Automated testing cho tất cả features

**Usage:**
```bash
python scripts/test_features.py
```

**Tests:**
- Health check
- Chat API
- Dashboard API
- Dashboard UI
- Metrics endpoint

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# App Configuration
APP_ENV=dev                              # Environment: dev, staging, prod
APP_NAME=day13-observability-lab        # Service name
LOG_LEVEL=INFO                           # Log level: DEBUG, INFO, WARNING, ERROR
LOG_PATH=data/logs.jsonl                 # Log file path
AUDIT_LOG_PATH=data/audit.jsonl         # Audit log path

# Langfuse Tracing (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx           # Langfuse public key
LANGFUSE_SECRET_KEY=sk-lf-xxx           # Langfuse secret key
LANGFUSE_HOST=https://cloud.langfuse.com # Langfuse host

# OpenAI Integration (Optional)
OPENAI_API_KEY=sk-xxx                    # OpenAI API key
USE_OPENAI=false                         # Use real OpenAI (true) or mock (false)
```

### SLO Configuration (config/slo.yaml)

```yaml
service: day13-observability-lab
window: 28d
slis:
  latency_p95_ms:
    objective: 3000      # < 3000ms
    target: 99.5         # 99.5% compliance
    note: Replace with your group's target
  error_rate_pct:
    objective: 2         # < 2%
    target: 99.0         # 99.0% compliance
  daily_cost_usd:
    objective: 2.5       # < $2.50/day
    target: 100.0        # 100% compliance
  quality_score_avg:
    objective: 0.75      # > 0.75
    target: 95.0         # 95% compliance
```

### Alert Rules (config/alert_rules.yaml)

```yaml
alerts:
  - name: high_latency_p95
    condition: latency_p95 > 3000
    severity: warning
    runbook: docs/alerts.md#1-high-latency-p95
    
  - name: error_rate_spike
    condition: error_rate > 2%
    severity: critical
    runbook: docs/alerts.md#2-error-rate-spike
    
  - name: cost_budget_exceeded
    condition: daily_cost > 2.5
    severity: warning
    runbook: docs/alerts.md#3-cost-budget-exceeded
```

---

## 🔍 Troubleshooting

### Server không khởi động được

**Lỗi:** `ModuleNotFoundError: No module named 'fastapi'`

**Giải pháp:**
```bash
pip install -r requirements.txt
```

---

### Dashboard không hiển thị data

**Nguyên nhân:** Chưa có traffic

**Giải pháp:**
```bash
python scripts/load_test.py
```

---

### Metrics bị reset về 0

**Nguyên nhân:** Metrics lưu trong memory, reset khi restart server

**Giải pháp:** Metrics sẽ tích lũy khi server đang chạy. Để persistent metrics, cần implement database storage.

---

### PII vẫn bị leak

**Kiểm tra:**
```bash
python scripts/validate_logs.py
```

**Nếu phát hiện leak:** Check patterns trong `app/pii.py`

---

### Langfuse không nhận traces

**Kiểm tra:**
1. Verify API keys trong `.env`
2. Check network connection
3. Xem logs: `tail -f data/logs.jsonl | grep langfuse`

**Test connection:**
```bash
python check_langfuse.py
```

---

### OpenAI API errors

**Lỗi:** `AuthenticationError`

**Giải pháp:**
1. Check `OPENAI_API_KEY` trong `.env`
2. Verify API key còn valid
3. Check API credits

**Fallback to mock:**
```env
USE_OPENAI=false
```

---

## 📞 Support & Resources

### Documentation
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Dashboard:** http://localhost:8000/dashboard

### Files
- **README.md:** Project overview
- **docs/blueprint-template.md:** Team report template
- **docs/alerts.md:** Runbook documentation
- **config/slo.yaml:** SLO configuration

### Logs
- **Application logs:** `data/logs.jsonl`
- **Audit logs:** `data/audit.jsonl`

### Scripts
- **Load test:** `scripts/load_test.py`
- **Validate:** `scripts/validate_logs.py`
- **Analyze:** `scripts/analyze_logs.py`
- **Test:** `scripts/test_features.py`

---

## 🎯 Quick Reference

### Start Server
```bash
uvicorn app.main:app --reload
```

### Test API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","session_id":"test","message":"hello"}'
```

### View Dashboard
```
http://localhost:8000/dashboard
```

### Generate Traffic
```bash
python scripts/load_test.py
```

### Validate
```bash
python scripts/validate_logs.py
```

### Check Metrics
```bash
curl http://localhost:8000/metrics
```

---

**Last Updated:** 2026-04-20  
**Version:** 1.0  
**Author:** VinAI Observability Team
