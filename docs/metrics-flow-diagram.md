# Metrics Persistence Flow Diagram

## 🔄 COMPLETE FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    APP STARTUP                                  │
│                                                                 │
│  uvicorn app.main:app --reload                                 │
│         ↓                                                       │
│  @app.on_event("startup")                                      │
│         ↓                                                       │
│  load_metrics()                                                │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ data/metrics.json exists?        │                         │
│  └──────────────────────────────────┘                         │
│         ↓                    ↓                                 │
│       YES                   NO                                 │
│         ↓                    ↓                                 │
│  Load from file        Start with 0                           │
│  TRAFFIC = 42          TRAFFIC = 0                            │
│  LATENCIES = [...]     LATENCIES = []                         │
│         ↓                    ↓                                 │
│         └────────────────────┘                                 │
│                  ↓                                             │
│         App ready with metrics!                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  REQUEST HANDLING                               │
│                                                                 │
│  Client → POST /chat                                           │
│         ↓                                                       │
│  CorrelationIdMiddleware                                       │
│         ↓                                                       │
│  /chat endpoint                                                │
│         ↓                                                       │
│  agent.run()                                                   │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ record_request()                 │                         │
│  │  - TRAFFIC += 1                  │                         │
│  │  - LATENCIES.append(150)         │                         │
│  │  - COSTS.append(0.0001)          │                         │
│  │  - TOKENS_IN.append(50)          │                         │
│  │  - TOKENS_OUT.append(120)        │                         │
│  │  - QUALITY_SCORES.append(0.7)    │                         │
│  │         ↓                         │                         │
│  │  save_metrics() ← AUTO-SAVE!     │                         │
│  └──────────────────────────────────┘                         │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ Write to data/metrics.json       │                         │
│  │ {                                │                         │
│  │   "traffic": 43,                 │                         │
│  │   "latencies": [..., 150],       │                         │
│  │   "costs": [..., 0.0001],        │                         │
│  │   ...                            │                         │
│  │ }                                │                         │
│  └──────────────────────────────────┘                         │
│         ↓                                                       │
│  Response to client                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  ERROR HANDLING                                 │
│                                                                 │
│  Exception occurs                                              │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ record_error("RuntimeError")     │                         │
│  │  - ERRORS["RuntimeError"] += 1   │                         │
│  │         ↓                         │                         │
│  │  save_metrics() ← AUTO-SAVE!     │                         │
│  └──────────────────────────────────┘                         │
│         ↓                                                       │
│  Write to data/metrics.json                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD VIEW                                 │
│                                                                 │
│  Browser → GET /dashboard                                      │
│         ↓                                                       │
│  JavaScript → fetch('/api/metrics')                            │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ snapshot()                       │                         │
│  │  - Read from memory (fast!)      │                         │
│  │  - Calculate percentiles         │                         │
│  │  - Return JSON                   │                         │
│  └──────────────────────────────────┘                         │
│         ↓                                                       │
│  {                                                             │
│    "traffic": 43,                                              │
│    "latency_p95": 180.0,                                       │
│    "total_cost_usd": 0.0043,                                   │
│    ...                                                         │
│  }                                                             │
│         ↓                                                       │
│  Render charts & tables                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  RESET METRICS                                  │
│                                                                 │
│  curl -X POST /metrics/reset                                   │
│         ↓                                                       │
│  ┌──────────────────────────────────┐                         │
│  │ Clear all metrics:               │                         │
│  │  - TRAFFIC = 0                   │                         │
│  │  - LATENCIES.clear()             │                         │
│  │  - COSTS.clear()                 │                         │
│  │  - TOKENS_IN.clear()             │                         │
│  │  - TOKENS_OUT.clear()            │                         │
│  │  - ERRORS.clear()                │                         │
│  │  - QUALITY_SCORES.clear()        │                         │
│  │         ↓                         │                         │
│  │  save_metrics() ← Save empty!    │                         │
│  └──────────────────────────────────┘                         │
│         ↓                                                       │
│  Write empty metrics to file                                   │
│  {"traffic": 0, "latencies": [], ...}                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 DATA FLOW

```
Memory (RAM)                    Disk (File)
─────────────                   ───────────

TRAFFIC = 42                    data/metrics.json
LATENCIES = [...]               {
COSTS = [...]        ──save──>    "traffic": 42,
TOKENS_IN = [...]               "latencies": [...],
TOKENS_OUT = [...]              "costs": [...],
ERRORS = {...}                  ...
QUALITY_SCORES = [...]        }
     ↑
     │
     └──load── (on startup)
```

## 🔄 LIFECYCLE

```
┌──────────────┐
│ App Start    │
│ load_metrics │
└──────┬───────┘
       │
       ↓
┌──────────────┐     ┌──────────────┐
│ Handle       │────>│ save_metrics │
│ Requests     │     │ (auto)       │
└──────┬───────┘     └──────────────┘
       │                     │
       │                     ↓
       │              ┌──────────────┐
       │              │ File Updated │
       │              └──────────────┘
       │
       ↓
┌──────────────┐
│ App Restart  │
│ load_metrics │ ← Metrics preserved!
└──────────────┘
```

## 🎯 KEY POINTS

1. **Auto-save**: Mỗi request/error → Tự động ghi file
2. **Auto-load**: Startup → Tự động đọc file
3. **Fast reads**: Dashboard đọc từ memory (không đọc file)
4. **Persistent**: Restart không mất data
5. **Resetable**: Có endpoint để xóa metrics

## 🚀 PERFORMANCE

```
Operation          Time        Impact
─────────────────────────────────────
load_metrics()     ~5ms        Once on startup
save_metrics()     ~1ms        Per request
snapshot()         ~0.1ms      Per dashboard refresh
```

**Overhead:** ~1ms per request (negligible)
