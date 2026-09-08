# 工业互联网应用项目

本项目是一个面向 1000 人同时在线使用的大型工业互联网应用系统，包含：

1. **设备监控仪表盘** - 实时展示传感器数据、设备状态
2. **MQTT 数据采集** - 模拟工业设备数据采集
3. **设备管理系统** - 设备注册、状态管理、告警
4. **数据分析引擎** - 基于 Pandas/NumPy 的工业数据分析
5. **API 网关** - RESTful API 供前端和第三方调用
6. **AI 助手** - 集成本地 AI 模型进行故障诊断和预测

## 架构
```
[模拟设备] → [MQTT Broker] → [数据采集服务] → [时序数据库]
                                          ↓
[Web 仪表盘] ← [API 网关 (FastAPI)] ← [数据分析引擎]
                              ↓
                      [AI 故障诊断 (LiteLLM)]
```

## 运行
```bash
# 启动数据采集模拟器
python3 src/data_simulator.py

# 启动 API 服务
python3 src/app.py

# 访问 Web 仪表盘
# http://10.167.2.175:30087/vscode/proxy/8080/
```

## 技术栈
- Python 3.13 + FastAPI + Flask
- Pandas + NumPy (数据分析)
- paho-mqtt (MQTT 通信)
- matplotlib (数据可视化)
- requests (AI 模型调用)
