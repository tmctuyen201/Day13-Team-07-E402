from __future__ import annotations

"""
Dashboard Module - Member D: QA Engineer
Implements 6-panel observability dashboard with real-time metrics,
SLO tracking, and Chart.js visualizations.

Author: Member D - QA Engineer
Features:
- 6 metric panels (Latency, Traffic, Error Rate, Cost, Tokens, Quality)
- SLO compliance table with progress bars
- Auto-refresh functionality (15s intervals)
- API endpoints for metrics, SLO, and logs
"""

import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .metrics import snapshot

router = APIRouter()


def load_slo_config() -> dict[str, Any]:
    """Load SLO configuration from YAML file."""
    slo_path = Path("config/slo.yaml")
    if not slo_path.exists():
        return {}
    
    with open(slo_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_logs(limit: int = 100, level: str | None = None) -> list[dict[str, Any]]:
    """Read logs from the JSONL file."""
    log_path = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
    
    if not log_path.exists():
        return []
    
    logs = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    log = json.loads(line)
                    if level is None or log.get("level") == level:
                        logs.append(log)
                except json.JSONDecodeError:
                    continue
    
    # Return most recent logs first
    return logs[-limit:][::-1]


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    """Render the metrics dashboard with 6 panels and SLO table."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Observability Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        header {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px 30px;
            border-radius: 16px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        h1 {
            font-size: 2rem;
            color: #1e293b;
            font-weight: 700;
        }
        
        .header-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .refresh-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .refresh-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: #64748b;
        }
        
        .panels-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            transition: transform 0.2s;
        }
        
        .panel:hover {
            transform: translateY(-4px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
        }
        
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .panel-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #1e293b;
        }
        
        .panel-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .panel-unit {
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 15px;
        }
        
        .panel-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        
        .status-good {
            background: #10b981;
            color: white;
        }
        
        .status-warning {
            background: #f59e0b;
            color: white;
        }
        
        .status-critical {
            background: #ef4444;
            color: white;
        }
        
        .chart-container {
            position: relative;
            height: 200px;
            margin-top: 15px;
        }
        
        .slo-table-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        }
        
        .slo-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .slo-table th {
            background: #f1f5f9;
            padding: 15px;
            text-align: left;
            font-weight: 700;
            color: #1e293b;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .slo-table td {
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
            color: #475569;
        }
        
        .slo-table tr:hover {
            background: #f8fafc;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            transition: width 0.3s;
        }
        
        .progress-good {
            background: #10b981;
        }
        
        .progress-warning {
            background: #f59e0b;
        }
        
        .progress-critical {
            background: #ef4444;
        }
        
        .metric-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 8px;
        }
        
        .badge-latency {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .badge-error {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .badge-cost {
            background: #fef3c7;
            color: #92400e;
        }
        
        .badge-quality {
            background: #d1fae5;
            color: #065f46;
        }
        
        @media (max-width: 768px) {
            .panels-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>📊 Observability Dashboard</h1>
                <div style="margin-top: 8px; color: #64748b; font-size: 0.9rem;">
                    Real-time metrics with SLO tracking
                </div>
            </div>
            <div class="header-info">
                <div class="auto-refresh">
                    <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
                    <label for="autoRefresh">Auto-refresh (15s)</label>
                </div>
                <button class="refresh-btn" onclick="loadMetrics()">🔄 Refresh</button>
            </div>
        </header>
        
        <div class="panels-grid" id="panels"></div>
        
        <div class="slo-table-container">
            <h2 style="margin-bottom: 20px; color: #1e293b;">Service Level Objectives (SLO)</h2>
            <table class="slo-table" id="sloTable">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Current Value</th>
                        <th>Objective</th>
                        <th>Target</th>
                        <th>Status</th>
                        <th>Compliance</th>
                    </tr>
                </thead>
                <tbody id="sloTableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let autoRefreshInterval = null;
        let charts = {};
        
        async function loadMetrics() {
            try {
                const [metricsRes, sloRes] = await Promise.all([
                    fetch('/api/metrics'),
                    fetch('/api/slo')
                ]);
                
                const metrics = await metricsRes.json();
                const slo = await sloRes.json();
                
                renderPanels(metrics, slo);
                renderSLOTable(metrics, slo);
            } catch (error) {
                console.error('Error loading metrics:', error);
            }
        }
        
        function renderPanels(metrics, slo) {
            const panels = [
                {
                    title: 'Latency Percentiles',
                    value: metrics.latency_p95.toFixed(0),
                    unit: 'ms (P95)',
                    status: getLatencyStatus(metrics.latency_p95, slo.slis?.latency_p95_ms?.objective),
                    chart: {
                        type: 'line',
                        data: {
                            labels: ['P50', 'P95', 'P99'],
                            datasets: [{
                                label: 'Latency',
                                data: [metrics.latency_p50, metrics.latency_p95, metrics.latency_p99],
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4,
                                fill: true
                            }, {
                                label: 'SLO Threshold',
                                data: [slo.slis?.latency_p95_ms?.objective, slo.slis?.latency_p95_ms?.objective, slo.slis?.latency_p95_ms?.objective],
                                borderColor: '#ef4444',
                                borderDash: [5, 5],
                                borderWidth: 2,
                                pointRadius: 0
                            }]
                        }
                    },
                    badge: 'badge-latency'
                },
                {
                    title: 'Traffic (Requests)',
                    value: metrics.traffic,
                    unit: 'total requests',
                    status: 'good',
                    chart: {
                        type: 'bar',
                        data: {
                            labels: ['Total'],
                            datasets: [{
                                label: 'Requests',
                                data: [metrics.traffic],
                                backgroundColor: '#10b981'
                            }]
                        }
                    },
                    badge: 'badge-latency'
                },
                {
                    title: 'Error Rate',
                    value: calculateErrorRate(metrics).toFixed(2),
                    unit: '% error rate',
                    status: getErrorStatus(calculateErrorRate(metrics), slo.slis?.error_rate_pct?.objective),
                    chart: {
                        type: 'doughnut',
                        data: {
                            labels: ['Success', 'Errors'],
                            datasets: [{
                                data: [metrics.traffic - Object.values(metrics.error_breakdown).reduce((a, b) => a + b, 0), Object.values(metrics.error_breakdown).reduce((a, b) => a + b, 0)],
                                backgroundColor: ['#10b981', '#ef4444']
                            }]
                        }
                    },
                    badge: 'badge-error'
                },
                {
                    title: 'Cost Over Time',
                    value: metrics.total_cost_usd.toFixed(4),
                    unit: 'USD (total)',
                    status: getCostStatus(metrics.total_cost_usd, slo.slis?.daily_cost_usd?.objective),
                    chart: {
                        type: 'line',
                        data: {
                            labels: ['Avg', 'Total'],
                            datasets: [{
                                label: 'Cost (USD)',
                                data: [metrics.avg_cost_usd, metrics.total_cost_usd],
                                borderColor: '#f59e0b',
                                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                tension: 0.4,
                                fill: true
                            }, {
                                label: 'Daily SLO',
                                data: [slo.slis?.daily_cost_usd?.objective, slo.slis?.daily_cost_usd?.objective],
                                borderColor: '#ef4444',
                                borderDash: [5, 5],
                                borderWidth: 2,
                                pointRadius: 0
                            }]
                        }
                    },
                    badge: 'badge-cost'
                },
                {
                    title: 'Token Usage',
                    value: (metrics.tokens_in_total + metrics.tokens_out_total).toLocaleString(),
                    unit: 'total tokens',
                    status: 'good',
                    chart: {
                        type: 'bar',
                        data: {
                            labels: ['Input', 'Output'],
                            datasets: [{
                                label: 'Tokens',
                                data: [metrics.tokens_in_total, metrics.tokens_out_total],
                                backgroundColor: ['#3b82f6', '#8b5cf6']
                            }]
                        }
                    },
                    badge: 'badge-latency'
                },
                {
                    title: 'Quality Score',
                    value: metrics.quality_avg.toFixed(2),
                    unit: 'average score',
                    status: getQualityStatus(metrics.quality_avg, slo.slis?.quality_score_avg?.objective),
                    chart: {
                        type: 'line',
                        data: {
                            labels: ['Current', 'Target'],
                            datasets: [{
                                label: 'Quality',
                                data: [metrics.quality_avg, slo.slis?.quality_score_avg?.objective],
                                borderColor: '#10b981',
                                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                tension: 0.4,
                                fill: true
                            }, {
                                label: 'SLO Threshold',
                                data: [slo.slis?.quality_score_avg?.objective, slo.slis?.quality_score_avg?.objective],
                                borderColor: '#ef4444',
                                borderDash: [5, 5],
                                borderWidth: 2,
                                pointRadius: 0
                            }]
                        }
                    },
                    badge: 'badge-quality'
                }
            ];
            
            const panelsHtml = panels.map((panel, index) => `
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span class="metric-badge ${panel.badge}">${panel.title}</span>
                        </div>
                        <span class="panel-status status-${panel.status}">${panel.status}</span>
                    </div>
                    <div class="panel-value">${panel.value}</div>
                    <div class="panel-unit">${panel.unit}</div>
                    <div class="chart-container">
                        <canvas id="chart${index}"></canvas>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('panels').innerHTML = panelsHtml;
            
            // Destroy old charts
            Object.values(charts).forEach(chart => chart.destroy());
            charts = {};
            
            // Create new charts
            panels.forEach((panel, index) => {
                const ctx = document.getElementById(`chart${index}`).getContext('2d');
                charts[index] = new Chart(ctx, {
                    type: panel.chart.type,
                    data: panel.chart.data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'bottom'
                            }
                        },
                        scales: panel.chart.type !== 'doughnut' ? {
                            y: {
                                beginAtZero: true
                            }
                        } : {}
                    }
                });
            });
        }
        
        function renderSLOTable(metrics, slo) {
            const slis = slo.slis || {};
            const rows = [
                {
                    metric: 'Latency P95',
                    current: `${metrics.latency_p95.toFixed(0)} ms`,
                    objective: `< ${slis.latency_p95_ms?.objective || 'N/A'} ms`,
                    target: `${slis.latency_p95_ms?.target || 'N/A'}%`,
                    status: getLatencyStatus(metrics.latency_p95, slis.latency_p95_ms?.objective),
                    compliance: calculateCompliance(metrics.latency_p95, slis.latency_p95_ms?.objective, true)
                },
                {
                    metric: 'Error Rate',
                    current: `${calculateErrorRate(metrics).toFixed(2)}%`,
                    objective: `< ${slis.error_rate_pct?.objective || 'N/A'}%`,
                    target: `${slis.error_rate_pct?.target || 'N/A'}%`,
                    status: getErrorStatus(calculateErrorRate(metrics), slis.error_rate_pct?.objective),
                    compliance: calculateCompliance(calculateErrorRate(metrics), slis.error_rate_pct?.objective, true)
                },
                {
                    metric: 'Daily Cost',
                    current: `$${metrics.total_cost_usd.toFixed(4)}`,
                    objective: `< $${slis.daily_cost_usd?.objective || 'N/A'}`,
                    target: `${slis.daily_cost_usd?.target || 'N/A'}%`,
                    status: getCostStatus(metrics.total_cost_usd, slis.daily_cost_usd?.objective),
                    compliance: calculateCompliance(metrics.total_cost_usd, slis.daily_cost_usd?.objective, true)
                },
                {
                    metric: 'Quality Score',
                    current: metrics.quality_avg.toFixed(2),
                    objective: `> ${slis.quality_score_avg?.objective || 'N/A'}`,
                    target: `${slis.quality_score_avg?.target || 'N/A'}%`,
                    status: getQualityStatus(metrics.quality_avg, slis.quality_score_avg?.objective),
                    compliance: calculateCompliance(metrics.quality_avg, slis.quality_score_avg?.objective, false)
                }
            ];
            
            const tableHtml = rows.map(row => `
                <tr>
                    <td><strong>${row.metric}</strong></td>
                    <td>${row.current}</td>
                    <td>${row.objective}</td>
                    <td>${row.target}</td>
                    <td><span class="panel-status status-${row.status}">${row.status}</span></td>
                    <td>
                        <div>${row.compliance.toFixed(1)}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-${row.status}" style="width: ${row.compliance}%"></div>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('sloTableBody').innerHTML = tableHtml;
        }
        
        function getLatencyStatus(value, threshold) {
            if (!threshold) return 'good';
            if (value < threshold * 0.8) return 'good';
            if (value < threshold) return 'warning';
            return 'critical';
        }
        
        function getErrorStatus(value, threshold) {
            if (!threshold) return 'good';
            if (value < threshold * 0.5) return 'good';
            if (value < threshold) return 'warning';
            return 'critical';
        }
        
        function getCostStatus(value, threshold) {
            if (!threshold) return 'good';
            if (value < threshold * 0.8) return 'good';
            if (value < threshold) return 'warning';
            return 'critical';
        }
        
        function getQualityStatus(value, threshold) {
            if (!threshold) return 'good';
            if (value >= threshold) return 'good';
            if (value >= threshold * 0.9) return 'warning';
            return 'critical';
        }
        
        function calculateErrorRate(metrics) {
            const totalErrors = Object.values(metrics.error_breakdown).reduce((a, b) => a + b, 0);
            return metrics.traffic > 0 ? (totalErrors / metrics.traffic) * 100 : 0;
        }
        
        function calculateCompliance(current, threshold, lowerIsBetter) {
            if (!threshold) return 100;
            if (lowerIsBetter) {
                return Math.min(100, Math.max(0, (1 - current / threshold) * 100));
            } else {
                return Math.min(100, Math.max(0, (current / threshold) * 100));
            }
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(loadMetrics, 15000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }
        
        // Initial load
        loadMetrics();
    </script>
</body>
</html>
    """


@router.get("/api/logs")
async def get_logs(
    limit: int = Query(default=100, ge=10, le=1000),
    level: str | None = Query(default=None)
) -> dict[str, Any]:
    """API endpoint to fetch logs."""
    logs = read_logs(limit=limit, level=level)
    
    # Calculate stats
    stats = {
        "total": len(logs),
        "info": sum(1 for log in logs if log.get("level") == "info"),
        "warning": sum(1 for log in logs if log.get("level") == "warning"),
        "error": sum(1 for log in logs if log.get("level") == "error"),
        "critical": sum(1 for log in logs if log.get("level") == "critical"),
    }
    
    return {"logs": logs, "stats": stats}


@router.get("/api/metrics")
async def get_metrics() -> dict[str, Any]:
    """API endpoint to fetch current metrics."""
    return snapshot()


@router.get("/api/slo")
async def get_slo() -> dict[str, Any]:
    """API endpoint to fetch SLO configuration."""
    return load_slo_config()
