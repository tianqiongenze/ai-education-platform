"""
工业互联网应用 - 配置文件
支持 1000 人同时在线的配置参数
"""

# ============ 系统配置 ============
SYSTEM = {
    "name": "工业互联网应用平台",
    "version": "2.0.0",
    "environment": "production",
    "max_concurrent_users": 1000,
}

# ============ 数据采集配置 ============
DATA_SIMULATOR = {
    "num_devices": 50,              # 模拟设备数量
    "collection_interval": 5,       # 数据采集间隔(秒)
    "history_size": 100,            # 每台设备历史数据保留量
    "workshops": ["A1车间", "A2车间", "B1车间", "B2车间", "C1车间"],
    "device_types": ["CNC机床", "工业机器人", "传送带电机", "注塑机", "空压机"],
}

# ============ 告警阈值 ============
ALARM_THRESHOLDS = {
    "temp_high": 85,         # 温度告警阈值(°C)
    "temp_critical": 95,     # 温度危险阈值(°C)
    "pressure_high": 18,    # 压力告警阈值(MPa)
    "vibration_high": 4.5,  # 振动告警阈值(mm/s)
    "current_high": 55,     # 电流告警阈值(A)
    "efficiency_low": 80,   # 效率低告警(%)
}

# ============ AI 模型配置 ============
AI_CONFIG = {
    "litellm_url": "http://litellm.ai-platform.svc.cluster.local:4000/v1",
    "api_key": "sk-ai-platform-master",
    "chat_model": "qwen2.5-coder:7b",           # 聊天/诊断模型
    "fast_model": "qwen3:4b",                    # 快速响应模型
    "embedding_model": "bge-m3",                 # 嵌入模型
    "temperature": 0.3,                           # 采样温度
    "max_tokens": 500,                            # 最大token数
    "timeout": 60,                                # 超时(秒)
}

# ============ API 配置 ============
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8888,
    "workers": 4,                # uvicorn worker 数量
    "cors": True,
    "docs_url": "/docs",
}

# ============ 数据分析配置 ============
ANALYTICS = {
    "anomaly_threshold_std": 2,   # 异常检测标准差倍数
    "trend_window": 20,           # 趋势分析窗口
    "prediction_horizon": 7,     # 预测天数
}

# ============ 1000人并发支持 ============
SCALING = {
    # Dify API HPA: 3-20 副本
    "dify_api_min": 3,
    "dify_api_max": 20,
    # Code-Server HPA: 3-20 副本
    "code_server_min": 3,
    "code_server_max": 20,
    # LiteLLM: 1-10 副本
    "litellm_min": 1,
    "litellm_max": 10,
    # uvicorn workers per pod
    "uvicorn_workers": 4,
    # 每 pod 最大并发连接
    "max_connections_per_pod": 250,
    # 估算: 5 pods × 4 workers × 250 = 5000 并发(支持1000人在线)
}
