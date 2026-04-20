# Metrics Persistence

## Tổng quan

Metrics giờ được **tự động lưu vào file** `data/metrics.json` sau mỗi request/error. Khi restart app, metrics sẽ được **tự động load lại**.

## Cách hoạt động

### 1. Auto-save
```python
# Mỗi khi có request mới
record_request(...) → save_metrics() → Ghi vào data/metrics.json

# Mỗi khi có error
record_error(...) → save_metrics() → Ghi vào data/metrics.json
```

### 2. Auto-load
```python
# Khi app startup
@app.on_event("startup")
async def startup():
    load_metrics()  # ← Load từ data/metrics.json
```

## File format

`data/metrics.json`:
```json
{
  "traffic": 42,
  "latencies": [150, 200, 180, ...],
  "costs": [0.0001, 0.0002, ...],
  "tokens_in": [50, 60, 55, ...],
  "tokens_out": [120, 150, 130, ...],
  "errors": {
    "RuntimeError": 2,
    "ValueError": 1
  },
  "quality_scores": [0.7, 0.8, 0.75, ...]
}
```

## API Endpoints

### Reset metrics
```bash
# Xóa tất cả metrics về 0
curl -X POST http://127.0.0.1:8000/metrics/reset

# Response:
{
  "ok": true,
  "message": "Metrics reset successfully"
}
```

### View current metrics
```bash
curl http://127.0.0.1:8000/metrics

# Response:
{
  "traffic": 42,
  "latency_p50": 180.0,
  "latency_p95": 245.0,
  "latency_p99": 280.0,
  "avg_cost_usd": 0.0002,
  "total_cost_usd": 0.0084,
  ...
}
```

## Configuration

Thay đổi đường dẫn file trong `.env`:
```bash
METRICS_PATH=data/metrics.json  # Default
```

## Testing

```bash
# 1. Gửi một số requests
python scripts/load_test.py

# 2. Kiểm tra metrics
curl http://127.0.0.1:8000/metrics

# 3. Restart app
# Ctrl+C → uvicorn app.main:app --reload

# 4. Kiểm tra lại metrics (vẫn còn!)
curl http://127.0.0.1:8000/metrics

# 5. Reset nếu cần
curl -X POST http://127.0.0.1:8000/metrics/reset
```

## Lợi ích

✅ **Persistence**: Metrics không mất khi restart  
✅ **Auto-save**: Không cần thao tác thủ công  
✅ **Simple**: Chỉ dùng JSON file, không cần database  
✅ **Testable**: Có endpoint để reset metrics  

## Lưu ý

⚠️ File `data/metrics.json` đã được thêm vào `.gitignore`  
⚠️ Với production, nên dùng database hoặc time-series DB (Prometheus, InfluxDB)  
⚠️ File size sẽ tăng theo số lượng requests (có thể implement rotation nếu cần)
