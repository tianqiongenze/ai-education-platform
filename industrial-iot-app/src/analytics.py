"""
工业互联网应用 - 数据分析引擎
使用 Pandas/NumPy 进行工业数据分析
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

class DataAnalysisEngine:
    """工业数据分析引擎"""

    def __init__(self, simulator):
        self.sim = simulator

    def analyze_temperature_trend(self, device_id: str) -> dict:
        """分析温度趋势"""
        history = self.sim.get_device_history(device_id, limit=100)
        if len(history) < 2:
            return {"device_id": device_id, "analysis": "数据不足"}

        temps = np.array([h["temperature"] for h in history])
        result = {
            "device_id": device_id,
            "current": float(temps[-1]),
            "avg": round(float(np.mean(temps)), 1),
            "max": float(np.max(temps)),
            "min": float(np.min(temps)),
            "std": round(float(np.std(temps)), 2),
            "trend": "上升" if temps[-1] > np.mean(temps) else "下降",
            "prediction_next": round(float(np.polyfit(range(len(temps)), temps, 1)[-1] if len(temps) > 2 else temps[-1]), 1),
        }
        result["risk_level"] = "高" if result["current"] > 85 else ("中" if result["current"] > 70 else "低")
        return result

    def analyze_efficiency(self) -> dict:
        """分析全厂效率"""
        all_data = self.sim.get_current_data()
        df = pd.DataFrame(all_data)

        result = {
            "total_devices": len(df),
            "avg_efficiency": round(float(df["efficiency"].mean()), 1),
            "max_efficiency": float(df["efficiency"].max()),
            "min_efficiency": float(df["efficiency"].min()),
            "below_threshold": int((df["efficiency"] < 80).sum()),
            "by_type": {},
            "by_workshop": {},
        }

        # 按设备类型分析
        for dtype, group in df.groupby("device_type"):
            result["by_type"][dtype] = {
                "count": len(group),
                "avg_eff": round(float(group["efficiency"].mean()), 1),
                "avg_temp": round(float(group["temperature"].mean()), 1),
                "total_power": round(float(group["power"].sum()), 2),
            }

        # 按车间分析
        for ws, group in df.groupby("workshop"):
            result["by_workshop"][ws] = {
                "count": len(group),
                "avg_eff": round(float(group["efficiency"].mean()), 1),
                "total_power": round(float(group["power"].sum()), 2),
                "running": int((group["status"] == "running").sum()),
            }

        return result

    def detect_anomalies(self) -> List[dict]:
        """异常检测 - 使用统计方法"""
        all_data = self.sim.get_current_data()
        df = pd.DataFrame(all_data)

        anomalies = []

        # 温度异常检测 (超过2个标准差)
        temp_mean = df["temperature"].mean()
        temp_std = df["temperature"].std()
        for _, row in df.iterrows():
            if abs(row["temperature"] - temp_mean) > 2 * temp_std:
                anomalies.append({
                    "device_id": row["device_id"],
                    "device_name": row["device_name"],
                    "type": "温度异常",
                    "value": float(row["temperature"]),
                    "mean": round(temp_mean, 1),
                    "deviation": round(abs(row["temperature"] - temp_mean), 1),
                })

        # 振动异常检测
        vib_mean = df["vibration"].mean()
        vib_std = df["vibration"].std()
        for _, row in df.iterrows():
            if abs(row["vibration"] - vib_mean) > 2 * vib_std:
                anomalies.append({
                    "device_id": row["device_id"],
                    "device_name": row["device_name"],
                    "type": "振动异常",
                    "value": float(row["vibration"]),
                    "mean": round(vib_mean, 3),
                    "deviation": round(abs(row["vibration"] - vib_mean), 3),
                })

        return anomalies

    def generate_kpi_report(self) -> dict:
        """生成 KPI 报告"""
        all_data = self.sim.get_current_data()
        df = pd.DataFrame(all_data)

        total_power = float(df["power"].sum())
        running_count = int((df["status"] == "running").sum())
        total = len(df)

        kpis = {
            "OEE": round(running_count / total * 100, 1),  # 设备综合效率 (简化)
            "availability": round(running_count / total * 100, 1),  # 可用率
            "performance": round(float(df["efficiency"].mean()), 1),  # 性能率
            "quality": 95.0,  # 质量率 (模拟)
            "MTBF": round(float(df["uptime_hours"].mean()), 1),  # 平均故障间隔
            "energy_consumption": total_power,
            "energy_efficiency": round(total_power / (running_count + 0.01), 2),  # 单位设备能耗
            "carbon_footprint": round(total_power * 0.5, 2),  # 碳足迹估算 (kgCO2/h)
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        kpis["OEE"] = round(kpis["availability"] * kpis["performance"] * kpis["quality"] / 10000, 1)
        return kpis


if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_simulator import IndustrialDataSimulator
    sim = IndustrialDataSimulator(num_devices=50)
    sim.start_background(interval=5)
    import time; time.sleep(6)

    engine = DataAnalysisEngine(sim)
    print("=== 效率分析 ===")
    print(json.dumps(engine.analyze_efficiency(), indent=2, ensure_ascii=False))
    print("\n=== KPI 报告 ===")
    print(json.dumps(engine.generate_kpi_report(), indent=2, ensure_ascii=False))
    print("\n=== 异常检测 ===")
    anomalies = engine.detect_anomalies()
    print(f"检测到 {len(anomalies)} 个异常")
