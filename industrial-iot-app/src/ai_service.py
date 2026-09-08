"""
工业互联网应用 - AI 故障诊断服务
调用本地 LLM 模型(qwen2.5-coder:7b)进行设备故障诊断和预测性维护
"""
import requests
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

LITELLM_URL = "http://litellm.ai-platform.svc.cluster.local:4000/v1"
API_KEY = "sk-ai-platform-master"
CHAT_MODEL = "qwen2.5-coder:7b"

# 故障诊断提示词模板
DIAGNOSIS_PROMPT = """你是一位工业设备故障诊断专家。请根据以下设备数据分析可能的故障原因和维护建议。

设备信息:
- 设备ID: {device_id}
- 设备名称: {device_name}
- 设备类型: {device_type}
- 所在车间: {workshop}
- 当前状态: {status}
- 运行时长: {uptime} 小时
- 效率: {efficiency}%

传感器数据:
- 温度: {temperature}°C
- 压力: {pressure} MPa
- 振动: {vibration} mm/s
- 电流: {current} A
- 功率: {power} kW

告警类型: {alarm_types}

请分析:
1. 故障可能的原因（按可能性排序）
2. 紧急处理建议
3. 预防措施
4. 预计维修时间

请用简洁专业的中文回答。"""

PREDICTION_PROMPT = """你是一位工业设备预测性维护专家。基于以下历史数据趋势，预测设备未来7天的健康状态。

设备: {device_name} ({device_type})
当前温度趋势: {temp_trend}
当前振动趋势: {vibration_trend}
当前效率趋势: {efficiency_trend}
设备运行时长: {uptime} 小时

请输出:
1. 健康度评分(0-100)
2. 预测风险等级(低/中/高)
3. 建议维护时间窗口
4. 重点关注的指标

请用简洁的中文回答。"""


class AIService:
    """AI 故障诊断服务"""

    def __init__(self):
        self.url = LITELLM_URL
        self.api_key = API_KEY
        self.model = CHAT_MODEL

    def _call_llm(self, messages: List[dict], max_tokens: int = 500) -> str:
        """调用 LLM 模型"""
        try:
            resp = requests.post(
                f"{self.url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            else:
                logger.error(f"LLM API error: {resp.status_code} {resp.text[:200]}")
                return f"AI分析暂时不可用 (HTTP {resp.status_code})"
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"AI分析暂时不可用: {str(e)[:100]}"

    def diagnose(self, device_data: dict, alarm_types: List[str]) -> dict:
        """设备故障诊断"""
        prompt = DIAGNOSIS_PROMPT.format(
            device_id=device_data.get("device_id", ""),
            device_name=device_data.get("device_name", ""),
            device_type=device_data.get("device_type", ""),
            workshop=device_data.get("workshop", ""),
            status=device_data.get("status", ""),
            uptime=device_data.get("uptime_hours", 0),
            efficiency=device_data.get("efficiency", 0),
            temperature=device_data.get("temperature", 0),
            pressure=device_data.get("pressure", 0),
            vibration=device_data.get("vibration", 0),
            current=device_data.get("current", 0),
            power=device_data.get("power", 0),
            alarm_types=", ".join(alarm_types) if alarm_types else "无",
        )

        result = self._call_llm([
            {"role": "system", "content": "你是工业设备故障诊断专家，请用专业简洁的中文分析。"},
            {"role": "user", "content": prompt},
        ])

        return {
            "device_id": device_data.get("device_id", ""),
            "device_name": device_data.get("device_name", ""),
            "diagnosis": result,
            "timestamp": device_data.get("timestamp", ""),
        }

    def predict(self, device_data: dict, temp_trend: str, vibration_trend: str, efficiency_trend: str) -> dict:
        """预测性维护分析"""
        prompt = PREDICTION_PROMPT.format(
            device_name=device_data.get("device_name", ""),
            device_type=device_data.get("device_type", ""),
            temp_trend=temp_trend,
            vibration_trend=vibration_trend,
            efficiency_trend=efficiency_trend,
            uptime=device_data.get("uptime_hours", 0),
        )

        result = self._call_llm([
            {"role": "system", "content": "你是工业设备预测性维护专家，请用专业简洁的中文分析。"},
            {"role": "user", "content": prompt},
        ])

        return {
            "device_id": device_data.get("device_id", ""),
            "device_name": device_data.get("device_name", ""),
            "prediction": result,
            "timestamp": device_data.get("timestamp", ""),
        }

    def generate_report(self, statistics: dict, alarms: list) -> str:
        """生成工厂运营日报"""
        alarm_summary = "\n".join([
            f"- {a['device_name']}({a['workshop']}): {', '.join(a['alarm_type'])} [{a['severity']}]"
            for a in alarms[:10]
        ]) if alarms else "无告警"

        prompt = f"""请生成一份工业工厂运营日报。

工厂概况:
- 设备总数: {statistics.get('total_devices', 0)}
- 运行中: {statistics.get('running', 0)}
- 空闲: {statistics.get('idle', 0)}
- 告警: {statistics.get('warning', 0)}
- 故障: {statistics.get('fault', 0)}
- 在线率: {statistics.get('online_rate', 0)}%
- 故障率: {statistics.get('fault_rate', 0)}%
- 总功率: {statistics.get('total_power_kw', 0)} kW
- 平均效率: {statistics.get('avg_efficiency', 0)}%
- 平均温度: {statistics.get('avg_temperature', 0)}°C

当前告警:
{alarm_summary}

请输出:
1. 运营概况总结
2. 关键风险提示
3. 建议措施
4. 资源优化建议

请用专业的中文输出，格式清晰。"""

        return self._call_llm([
            {"role": "system", "content": "你是工厂运营管理专家，请生成专业的运营日报。"},
            {"role": "user", "content": prompt},
        ], max_tokens=800)


# 全局 AI 服务实例
ai_service = AIService()


if __name__ == "__main__":
    # 测试 AI 服务
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_simulator import IndustrialDataSimulator

    sim = IndustrialDataSimulator(num_devices=10)
    sim.start_background(interval=5)
    import time; time.sleep(6)  # 等待数据采集

    data = sim.get_current_data()
    if data:
        device = data[0]
        print(f"测试设备: {device['device_name']}")
        print(f"状态: {device['status']}")
        print(f"温度: {device['temperature']}°C\n")

        print("=== 故障诊断 ===")
        result = ai_service.diagnose(device, ["状态异常"])
        print(result["diagnosis"])

        print("\n=== 运营日报 ===")
        stats = sim.get_statistics()
        alarms = sim.get_alarms()
        report = ai_service.generate_report(stats, alarms)
        print(report)
