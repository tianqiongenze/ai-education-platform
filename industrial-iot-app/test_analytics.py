import sys, time, json
sys.path.insert(0, "/home/coder/industrial-iot-app/src")
from data_simulator import IndustrialDataSimulator
from analytics import DataAnalysisEngine

sim = IndustrialDataSimulator(num_devices=50)
sim.start_background(interval=5)
time.sleep(6)

engine = DataAnalysisEngine(sim)
stats = engine.generate_kpi_report()
print(f"KPI: OEE={stats['OEE']} 可用率={stats['availability']} 总功率={stats['energy_consumption']}kW")
print(f"碳足迹={stats['carbon_footprint']}kgCO2/h MTBF={stats['MTBF']}h")

eff = engine.analyze_efficiency()
print(f"\n效率: 平均={eff['avg_efficiency']}% 低于阈值={eff['below_threshold']}台")
for dt, v in eff['by_type'].items():
    print(f"  {dt}: {v['count']}台 效率={v['avg_eff']}% 功率={v['total_power']}kW")

anomalies = engine.detect_anomalies()
print(f"\n异常检测: {len(anomalies)} 个异常")
for a in anomalies[:3]:
    print(f"  {a['device_name']}: {a['type']} 值={a['value']} 偏离={a['deviation']}")

sim.stop()
print("\n✅ 数据分析引擎测试通过!")
