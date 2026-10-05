"""
AJAX AI - System Telemetry & Monitor
Provides real-time system metrics, process tracking, and disk analytics.
"""

import psutil
from typing import Dict, Any, List

class SystemMonitor:
    @staticmethod
    def get_full_diagnostics() -> Dict[str, Any]:
        cpu_pct = psutil.cpu_percent(interval=0.2)
        cpu_count = psutil.cpu_count(logical=True)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()

        # Top 5 CPU-consuming processes
        top_procs = []
        for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']), 
                        key=lambda x: x.info.get('cpu_percent') or 0, reverse=True)[:5]:
            top_procs.append({
                "name": p.info['name'],
                "pid": p.info['pid'],
                "cpu": p.info.get('cpu_percent', 0),
                "ram_mb": round((p.info.get('memory_percent', 0) / 100) * (ram.total / (1024**2)), 1)
            })

        return {
            "cpu": {
                "usage_percent": cpu_pct,
                "cores": cpu_count
            },
            "ram": {
                "used_mb": ram.used // (1024**2),
                "total_mb": ram.total // (1024**2),
                "percent": ram.percent
            },
            "disk": {
                "free_gb": round(disk.free / (1024**3), 1),
                "total_gb": round(disk.total / (1024**3), 1),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent_mb": round(net.bytes_sent / (1024**2), 1),
                "bytes_recv_mb": round(net.bytes_recv / (1024**2), 1)
            },
            "battery": {
                "percent": battery.percent if battery else None,
                "plugged": battery.power_plugged if battery else True
            },
            "top_processes": top_procs
        }

system_monitor = SystemMonitor()
