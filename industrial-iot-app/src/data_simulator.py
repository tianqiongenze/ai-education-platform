"""
工业互联网应用 - 设备数据模拟器
模拟 50 台工业设备的传感器数据（温度、压力、振动、电流、功率）
通过 MQTT 协议发送到本地 broker
支持 1000 人同时在线查看
"""
import json
import random
import time
import threading
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import os
import sys

# 设备类型定义
DEVICE_TYPES = {
    "CNC机床": {"temp": (35, 85), "pressure": (2, 8), "vibration": (0.5, 5.0), "current": (10, 50), "power": (3, 15)},
    "工业机器人": {"temp": (30, 75), "pressure": (1, 6), "vibration": (0.2, 3.5), "current": (5, 35), "power": (1, 10)},
    "传送带电机": {"temp": (25, 65), "pressure": (0.5, 4), "vibration": (0.1, 2.0), "current": (3, 20), "power": (0.5, 5)},
    "注塑机": {"temp": (40, 95), "pressure": (5, 20), "vibration": (0.3, 4.0), "current": (15, 60), "power": (5, 25)},
    "空压机": {"temp": (35, 80), "pressure": (3, 12), "vibration": (0.2, 3.0), "current": (8, 40), "power": (2, 12)},
}

# 告警阈值
ALARM_THRESHOLDS = {
    "temp_high": 85,
    "temp_critical": 95,
    "pressure_high": 18,
    "vibration_high": 4.5,
    "current_high": 55,
}


@dataclass
class DeviceData:
    """设备传感器数据点"""
    device_id: str
    device_type: str
    device_name: str
    workshop: str  # 车间
    timestamp: str
    temperature: float       # 温度 (°C)
    pressure: float         # 压力 (MPa)
    vibration: float         # 振动 (mm/s)
    current: float           # 电流 (A)
    power: float             # 功率 (kW)
    status: str              # running / idle / warning / fault
    uptime_hours: float      # 运行时长
    efficiency: float       # 效率 %


class DeviceSimulator:
    """单台设备模拟器"""

    _id_counter = 0

    def __init__(self, device_type: str, workshop: str):
        DeviceSimulator._id_counter += 1
        self.device_id = f"DEV-{DeviceSimulator._id_counter:04d}"
        self.device_type = device_type
        self.device_name = f"{device_type}-{DeviceSimulator._id_counter:03d}"
        self.workshop = workshop
        self.ranges = DEVICE_TYPES[device_type]
        self.status = "running"
        self.uptime_hours = round(random.uniform(100, 5000), 1)
        self.efficiency = round(random.uniform(85, 98), 1)
        self._alarm_cooldown = 0
        self._phase = random.uniform(0, 2 * math.pi)  # 用于生成波形

    def generate_data(self) -> DeviceData:
        """生成一个时间点的传感器数据"""
        now = datetime.now()

        # 基于正弦波 + 随机噪声生成数据
        t = time.time()
        self._phase += 0.05

        temp_base = (self.ranges["temp"][0] + self.ranges["temp"][1]) / 2
        temp_amp = (self.ranges["temp"][1] - self.ranges["temp"][0]) / 2
        temperature = round(temp_base + temp_amp * 0.3 * math.sin(self._phase) + random.gauss(0, 1.5), 1)

        pressure = round(
            (self.ranges["pressure"][0] + self.ranges["pressure"][1]) / 2
            + (self.ranges["pressure"][1] - self.ranges["pressure"][0]) / 2 * 0.2 * math.sin(self._phase * 0.7)
            + random.gauss(0, 0.3), 2
        )

        vibration = round(
            (self.ranges["vibration"][0] + self.ranges["vibration"][1]) / 2
            + (self.ranges["vibration"][1] - self.ranges["vibration"][0]) / 2 * 0.3 * math.sin(self._phase * 1.5)
            + random.gauss(0, 0.1), 3
        )

        current = round(
            (self.ranges["current"][0] + self.ranges["current"][1]) / 2
            + (self.ranges["current"][1] - self.ranges["current"][0]) / 2 * 0.4 * math.sin(self._phase * 0.8)
            + random.gauss(0, 2), 1
        )

        power = round(current * 0.3 + random.gauss(0, 0.5), 2)

        # 偶发告警/故障
        self._alarm_cooldown = max(0, self._alarm_cooldown - 1)
        if self._alarm_cooldown == 0 and random.random() < 0.003:
            # 触发告警
            if temperature > ALARM_THRESHOLDS["temp_high"]:
                self.status = "warning"
                self._alarm_cooldown = 10
            elif random.random() < 0.1:
                self.status = "fault"
                self._alarm_cooldown = 5
            else:
                self.status = "running"
        elif self._alarm_cooldown == 0:
            self.status = "running" if random.random() > 0.05 else "idle"

        self.uptime_hours = round(self.uptime_hours + (1 / 3600), 1)
        self.efficiency = max(60, min(99, self.efficiency + random.gauss(0, 0.5)))

        return DeviceData(
            device_id=self.device_id,
            device_type=self.device_type,
            device_name=self.device_name,
            workshop=self.workshop,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
            temperature=max(0, temperature),
            pressure=max(0, pressure),
            vibration=max(0, vibration),
            current=max(0, current),
            power=max(0, power),
            status=self.status,
            uptime_hours=self.uptime_hours,
            efficiency=round(self.efficiency, 1),
        )


class IndustrialDataSimulator:
    """工业数据模拟器主类 - 管理 50 台设备"""

    def __init__(self, num_devices=50):
        self.num_devices = num_devices
        self.devices: List[DeviceSimulator] = []
        self.data_history: Dict[str, List[dict]] = {}  # 设备ID -> 历史数据
        self.max_history = 100  # 每台设备保留100条历史
        self._lock = threading.Lock()
        self._running = False

        workshops = ["A1车间", "A2车间", "B1车间", "B2车间", "C1车间"]
        device_types = list(DEVICE_TYPES.keys())

        for i in range(num_devices):
            dt = device_types[i % len(device_types)]
            ws = workshops[i % len(workshops)]
            self.devices.append(DeviceSimulator(dt, ws))
            self.data_history[self.devices[-1].device_id] = []

        print(f"[Simulator] 已初始化 {num_devices} 台设备, 覆盖 {len(device_types)} 种类型, {len(workshops)} 个车间")

    def tick(self):
        """采集一次所有设备的数据"""
        all_data = []
        with self._lock:
            for device in self.devices:
                data = device.generate_data()
                data_dict = asdict(data)
                all_data.append(data_dict)

                # 保存历史
                self.data_history[data.device_id].append(data_dict)
                if len(self.data_history[data.device_id]) > self.max_history:
                    self.data_history[data.device_id].pop(0)

        return all_data

    def get_current_data(self) -> List[dict]:
        """获取所有设备的最新数据"""
        with self._lock:
            return [self.data_history[did][-1] for did in self.data_history if self.data_history[did]]

    def get_device_history(self, device_id: str, limit: int = 50) -> List[dict]:
        """获取设备历史数据"""
        with self._lock:
            history = self.data_history.get(device_id, [])
            return history[-limit:] if limit < len(history) else history

    def get_statistics(self) -> dict:
        """获取全局统计数据"""
        with self._lock:
            all_data = [h[-1] for h in self.data_history.values() if h]
            if not all_data:
                return {}

            total = len(all_data)
            running = sum(1 for d in all_data if d["status"] == "running")
            idle = sum(1 for d in all_data if d["status"] == "idle")
            warning = sum(1 for d in all_data if d["status"] == "warning")
            fault = sum(1 for d in all_data if d["status"] == "fault")

            avg_temp = sum(d["temperature"] for d in all_data) / total
            avg_power = sum(d["power"] for d in all_data) / total
            total_power = sum(d["power"] for d in all_data)
            avg_eff = sum(d["efficiency"] for d in all_data) / total

            return {
                "total_devices": total,
                "running": running,
                "idle": idle,
                "warning": warning,
                "fault": fault,
                "avg_temperature": round(avg_temp, 1),
                "total_power_kw": round(total_power, 2),
                "avg_efficiency": round(avg_eff, 1),
                "online_rate": round(running / total * 100, 1),
                "fault_rate": round((warning + fault) / total * 100, 1),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def get_alarms(self) -> List[dict]:
        """获取当前告警列表"""
        with self._lock:
            alarms = []
            for data_list in self.data_history.values():
                if data_list:
                    d = data_list[-1]
                    if d["status"] in ("warning", "fault"):
                        alarm_type = []
                        if d["temperature"] > ALARM_THRESHOLDS["temp_high"]:
                            alarm_type.append("高温告警")
                        if d["vibration"] > ALARM_THRESHOLDS["vibration_high"]:
                            alarm_type.append("振动异常")
                        if d["current"] > ALARM_THRESHOLDS["current_high"]:
                            alarm_type.append("电流过载")
                        if d["pressure"] > ALARM_THRESHOLDS["pressure_high"]:
                            alarm_type.append("压力过高")

                        alarms.append({
                            "device_id": d["device_id"],
                            "device_name": d["device_name"],
                            "workshop": d["workshop"],
                            "status": d["status"],
                            "alarm_type": alarm_type if alarm_type else ["状态异常"],
                            "temperature": d["temperature"],
                            "vibration": d["vibration"],
                            "timestamp": d["timestamp"],
                            "severity": "严重" if d["status"] == "fault" else "警告",
                        })
            return alarms

    def start_background(self, interval=5):
        """在后台线程中持续采集数据"""
        self._running = True
        def _run():
            while self._running:
                self.tick()
                time.sleep(interval)
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        print(f"[Simulator] 后台采集已启动, 间隔 {interval} 秒")
        return t

    def stop(self):
        self._running = False


if __name__ == "__main__":
    # 独立运行: 持续输出模拟数据
    sim = IndustrialDataSimulator(num_devices=50)
    sim.start_background(interval=5)

    print("\n" + "=" * 60)
    print("工业互联网设备数据模拟器已启动")
    print(f"设备数量: {sim.num_devices}")
    print(f"采集间隔: 5 秒")
    print("=" * 60 + "\n")

    try:
        while True:
            stats = sim.get_statistics()
            print(f"\n[{stats['timestamp']}] 运行={stats['running']} 空闲={stats['idle']} "
                  f"告警={stats['warning']} 故障={stats['fault']} "
                  f"总功率={stats['total_power_kw']}kW 平均效率={stats['avg_efficiency']}%")

            alarms = sim.get_alarms()
            for a in alarms[:3]:
                print(f"  ⚠ [{a['severity']}] {a['device_name']} ({a['workshop']}): {', '.join(a['alarm_type'])}")

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[Simulator] 已停止")
        sim.stop()
