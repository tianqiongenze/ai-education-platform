"""
工业互联网应用 - FastAPI 主应用
提供 RESTful API 和 Web 仪表盘
支持 1000 人同时在线访问
"""
import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_simulator import IndustrialDataSimulator
from ai_service import ai_service

# ============ 初始化 ============
app = FastAPI(title="工业互联网应用平台", version="2.0.0", description="支持1000人在线的工业互联网监控系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化设备模拟器 (50台设备, 5个车间, 5种设备类型)
simulator = IndustrialDataSimulator(num_devices=50)
simulator.start_background(interval=5)

# ============ API 路由 ============

@app.get("/api/v1/devices")
async def get_all_devices():
    """获取所有设备的最新状态"""
    data = simulator.get_current_data()
    return {"total": len(data), "devices": data, "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/devices/{device_id}")
async def get_device_detail(device_id: str):
    """获取单台设备详情和历史数据"""
    all_data = simulator.get_current_data()
    device = next((d for d in all_data if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    history = simulator.get_device_history(device_id, limit=50)
    return {"device": device, "history": history}

@app.get("/api/v1/statistics")
async def get_statistics():
    """获取全局统计数据"""
    stats = simulator.get_statistics()
    alarms = simulator.get_alarms()
    stats["active_alarms"] = len(alarms)
    return stats

@app.get("/api/v1/alarms")
async def get_alarms():
    """获取当前告警列表"""
    alarms = simulator.get_alarms()
    return {"total": len(alarms), "alarms": alarms, "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/workshops")
async def get_workshops():
    """按车间分组统计"""
    all_data = simulator.get_current_data()
    workshops = {}
    for d in all_data:
        ws = d["workshop"]
        if ws not in workshops:
            workshops[ws] = {"total": 0, "running": 0, "warning": 0, "fault": 0, "power": 0}
        workshops[ws]["total"] += 1
        if d["status"] == "running":
            workshops[ws]["running"] += 1
        elif d["status"] == "warning":
            workshops[ws]["warning"] += 1
        elif d["status"] == "fault":
            workshops[ws]["fault"] += 1
        workshops[ws]["power"] += d["power"]
    return workshops

@app.get("/api/v1/device-types")
async def get_device_types():
    """按设备类型分组统计"""
    all_data = simulator.get_current_data()
    types = {}
    for d in all_data:
        dt = d["device_type"]
        if dt not in types:
            types[dt] = {"total": 0, "running": 0, "avg_temp": 0, "avg_power": 0, "temps": [], "powers": []}
        types[dt]["total"] += 1
        if d["status"] == "running":
            types[dt]["running"] += 1
        types[dt]["temps"].append(d["temperature"])
        types[dt]["powers"].append(d["power"])
    for dt in types:
        temps = types[dt]["temps"]
        powers = types[dt]["powers"]
        types[dt]["avg_temp"] = round(sum(temps) / len(temps), 1) if temps else 0
        types[dt]["avg_power"] = round(sum(powers) / len(powers), 2) if powers else 0
        del types[dt]["temps"]
        del types[dt]["powers"]
    return types

@app.post("/api/v1/ai/diagnose/{device_id}")
async def ai_diagnose(device_id: str):
    """AI 故障诊断"""
    all_data = simulator.get_current_data()
    device = next((d for d in all_data if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    
    alarms = simulator.get_alarms()
    device_alarm = next((a for a in alarms if a["device_id"] == device_id), None)
    alarm_types = device_alarm["alarm_type"] if device_alarm else ["状态检查"]
    
    result = ai_service.diagnose(device, alarm_types)
    return result

@app.post("/api/v1/ai/predict/{device_id}")
async def ai_predict(device_id: str):
    """AI 预测性维护分析"""
    all_data = simulator.get_current_data()
    device = next((d for d in all_data if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    
    history = simulator.get_device_history(device_id, limit=20)
    temps = [h["temperature"] for h in history]
    vibrations = [h["vibration"] for h in history]
    effs = [h["efficiency"] for h in history]
    
    def trend(arr):
        if len(arr) < 2: return "数据不足"
        diff = arr[-1] - arr[0]
        if diff > 1: return f"上升 (+{round(diff,1)})"
        elif diff < -1: return f"下降 ({round(diff,1)})"
        else: return "平稳"
    
    result = ai_service.predict(
        device,
        trend(temps),
        trend(vibrations),
        trend(effs),
    )
    return result

@app.get("/api/v1/ai/report")
async def ai_daily_report():
    """AI 生成工厂运营日报"""
    stats = simulator.get_statistics()
    alarms = simulator.get_alarms()
    report = ai_service.generate_report(stats, alarms)
    return {"report": report, "statistics": stats, "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/charts/temperature")
async def get_temperature_chart():
    """获取温度趋势图表数据"""
    all_data = simulator.get_current_data()
    return {
        "labels": [d["device_name"] for d in all_data],
        "values": [d["temperature"] for d in all_data],
        "threshold": 85,
    }

@app.get("/api/v1/charts/power")
async def get_power_chart():
    """获取功率分布图表数据"""
    all_data = simulator.get_current_data()
    return {
        "labels": [d["device_name"] for d in all_data],
        "values": [d["power"] for d in all_data],
    }

@app.get("/api/v1/charts/status")
async def get_status_chart():
    """获取设备状态分布"""
    all_data = simulator.get_current_data()
    status_count = {"running": 0, "idle": 0, "warning": 0, "fault": 0}
    for d in all_data:
        status_count[d["status"]] = status_count.get(d["status"], 0) + 1
    return status_count

# ============ Web 仪表盘 ============

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Web 仪表盘主页"""
    return DASHBOARD_HTML

@app.get("/health")
async def health():
    return {"status": "ok", "service": "industrial-iot", "version": "2.0.0"}


# ============ Web 仪表盘 HTML ============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工业互联网应用平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a1929; color: #e0e0e0; }
        .header { background: linear-gradient(135deg, #0d2847, #1a3a5c); padding: 20px; text-align: center; border-bottom: 2px solid #2563eb; }
        .header h1 { color: #fff; font-size: 24px; }
        .header .subtitle { color: #60a5fa; font-size: 14px; margin-top: 5px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #0d2847; border: 1px solid #1e3a5f; border-radius: 8px; padding: 20px; text-align: center; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #00c896; }
        .stat-card .label { font-size: 14px; color: #8b95a5; margin-top: 5px; }
        .stat-card.warning .number { color: #ffb300; }
        .stat-card.danger .number { color: #ef4444; }
        .stat-card.info .number { color: #2563eb; }
        .section { background: #0d2847; border: 1px solid #1e3a5f; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #60a5fa; font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #1e3a5f; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #1e3a5f; }
        th { color: #60a5fa; font-size: 13px; }
        td { font-size: 13px; }
        .status-running { color: #00c896; }
        .status-idle { color: #8b95a5; }
        .status-warning { color: #ffb300; }
        .status-fault { color: #ef4444; font-weight: bold; }
        .chart-bar { height: 200px; display: flex; align-items: flex-end; gap: 3px; overflow-x: auto; }
        .bar { flex: 1; min-width: 20px; background: #2563eb; border-radius: 3px 3px 0 0; position: relative; transition: height 0.5s; }
        .bar.warn { background: #ffb300; }
        .bar.danger { background: #ef4444; }
        .bar .val { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); font-size: 10px; color: #8b95a5; }
        .alarm-item { background: #1a1f2e; border-left: 3px solid #ef4444; padding: 10px; margin-bottom: 8px; border-radius: 4px; }
        .alarm-item.warn { border-left-color: #ffb300; }
        .refresh-btn { background: #2563eb; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; float: right; }
        .refresh-btn:hover { background: #1d4ed8; }
        .ai-btn { background: #00c896; color: #fff; border: none; padding: 5px 15px; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .ai-btn:hover { background: #00a878; }
        #ai-result { background: #1a1f2e; padding: 15px; border-radius: 4px; margin-top: 10px; white-space: pre-wrap; font-size: 13px; line-height: 1.6; display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏭 工业互联网应用平台</h1>
        <div class="subtitle">设备监控 · 数据分析 · AI 故障诊断 · 支持 1000 人在线</div>
    </div>
    <div class="container">
        <div class="stats-grid" id="stats"></div>
        
        <div class="section">
            <h2>📊 设备温度监控 <button class="refresh-btn" onclick="refresh()">刷新</button></h2>
            <div class="chart-bar" id="temp-chart"></div>
        </div>

        <div class="section">
            <h2>📋 设备列表</h2>
            <table>
                <thead>
                    <tr><th>设备ID</th><th>名称</th><th>类型</th><th>车间</th><th>温度</th><th>压力</th><th>振动</th><th>电流</th><th>功率</th><th>效率</th><th>状态</th><th>AI诊断</th></tr>
                </thead>
                <tbody id="device-table"></tbody>
            </table>
        </div>

        <div class="section">
            <h2>⚠️ 告警信息</h2>
            <div id="alarms"></div>
        </div>

        <div class="section">
            <h2>🤖 AI 运营日报 <button class="ai-btn" onclick="getReport()">生成日报</button></h2>
            <div id="ai-result"></div>
        </div>
    </div>

    <script>
        async function fetchJSON(url) {
            const resp = await fetch(url);
            return resp.json();
        }

        async function refresh() {
            // 统计数据
            const stats = await fetchJSON('/api/v1/statistics');
            const statsEl = document.getElementById('stats');
            statsEl.innerHTML = `
                <div class="stat-card"><div class="number">${stats.total_devices}</div><div class="label">设备总数</div></div>
                <div class="stat-card"><div class="number">${stats.running}</div><div class="label">运行中</div></div>
                <div class="stat-card warning"><div class="number">${stats.warning}</div><div class="label">告警</div></div>
                <div class="stat-card danger"><div class="number">${stats.fault}</div><div class="label">故障</div></div>
                <div class="stat-card info"><div class="number">${stats.total_power_kw}</div><div class="label">总功率(kW)</div></div>
                <div class="stat-card"><div class="number">${stats.avg_efficiency}%</div><div class="label">平均效率</div></div>
                <div class="stat-card"><div class="number">${stats.online_rate}%</div><div class="label">在线率</div></div>
                <div class="stat-card warning"><div class="number">${stats.avg_temperature}°C</div><div class="label">平均温度</div></div>
            `;

            // 设备表格
            const data = await fetchJSON('/api/v1/devices');
            const tbody = document.getElementById('device-table');
            tbody.innerHTML = data.devices.map(d => `
                <tr>
                    <td>${d.device_id}</td>
                    <td>${d.device_name}</td>
                    <td>${d.device_type}</td>
                    <td>${d.workshop}</td>
                    <td>${d.temperature}°C</td>
                    <td>${d.pressure}</td>
                    <td>${d.vibration}</td>
                    <td>${d.current}A</td>
                    <td>${d.power}kW</td>
                    <td>${d.efficiency}%</td>
                    <td class="status-${d.status}">${d.status}</td>
                    <td><button class="ai-btn" onclick="diagnose('${d.device_id}')">诊断</button></td>
                </tr>
            `).join('');

            // 温度图表
            const chart = document.getElementById('temp-chart');
            chart.innerHTML = data.devices.map(d => {
                const h = Math.min(100, d.temperature);
                const cls = d.temperature > 85 ? 'danger' : (d.temperature > 70 ? 'warn' : '');
                return `<div class="bar ${cls}" style="height: ${h * 1.8}px"><div class="val">${d.temperature}</div></div>`;
            }).join('');

            // 告警
            const alarms = await fetchJSON('/api/v1/alarms');
            const alarmsEl = document.getElementById('alarms');
            if (alarms.alarms.length === 0) {
                alarmsEl.innerHTML = '<p style="color:#00c896">✅ 无告警，所有设备运行正常</p>';
            } else {
                alarmsEl.innerHTML = alarms.alarms.map(a => `
                    <div class="alarm-item ${a.severity === '警告' ? 'warn' : ''}">
                        <strong>${a.device_name}</strong> (${a.workshop}) - ${a.severity}
                        <br>告警类型: ${a.alarm_type.join(', ')}
                        <br>温度: ${a.temperature}°C, 振动: ${a.vibration}mm/s
                        <br>时间: ${a.timestamp}
                        <button class="ai-btn" onclick="diagnose('${a.device_id}')" style="float:right;margin-top:5px">AI诊断</button>
                    </div>
                `).join('');
            }
        }

        async function diagnose(deviceId) {
            const result = document.getElementById('ai-result');
            result.style.display = 'block';
            result.textContent = '⏳ AI 正在分析中...';
            try {
                const resp = await fetch(`/api/v1/ai/diagnose/${deviceId}`, {method: 'POST'});
                const data = await resp.json();
                result.textContent = `📋 ${data.device_name} 故障诊断报告\n\n${data.diagnosis}`;
            } catch(e) {
                result.textContent = '❌ AI 分析失败: ' + e;
            }
        }

        async function getReport() {
            const result = document.getElementById('ai-result');
            result.style.display = 'block';
            result.textContent = '⏳ AI 正在生成运营日报...';
            try {
                const resp = await fetch('/api/v1/ai/report');
                const data = await resp.json();
                result.textContent = data.report;
            } catch(e) {
                result.textContent = '❌ AI 分析失败: ' + e;
            }
        }

        // 初始加载
        refresh();
        // 每10秒自动刷新
        setInterval(refresh, 10000);
    </script>
</body>
</html>
"""

# ============ 启动 ============

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  工业互联网应用平台 v2.0")
    print("  50 台设备 · 5 个车间 · 5 种设备类型")
    print("  AI 故障诊断 · 预测性维护 · 实时监控")
    print("=" * 60)
    print(f"  访问地址: http://localhost:8080")
    print(f"  API 文档: http://localhost:8080/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8080)
