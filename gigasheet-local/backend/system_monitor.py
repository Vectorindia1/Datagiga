#!/usr/bin/env python3
"""
🚀 BILLION-ROW System Monitor
Monitors system resources during massive data processing
"""

import psutil
import time
import json
from datetime import datetime
from pathlib import Path

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.peak_memory = 0
        self.peak_cpu = 0
        self.total_disk_read = 0
        self.total_disk_write = 0
        self.log_file = "system_performance.log"
    
    def get_current_stats(self):
        """Get current system resource usage"""
        try:
            # Memory stats
            memory = psutil.virtual_memory()
            memory_gb = memory.used / (1024**3)
            memory_percent = memory.percent
            
            # CPU stats
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Disk I/O stats
            disk_io = psutil.disk_io_counters()
            disk_read_gb = disk_io.read_bytes / (1024**3) if disk_io else 0
            disk_write_gb = disk_io.write_bytes / (1024**3) if disk_io else 0
            
            # Available disk space
            disk_usage = psutil.disk_usage('.')
            disk_free_gb = disk_usage.free / (1024**3)
            
            # Network stats (if needed for distributed processing)
            net_io = psutil.net_io_counters()
            
            # Update peaks
            self.peak_memory = max(self.peak_memory, memory_gb)
            self.peak_cpu = max(self.peak_cpu, cpu_percent)
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "memory": {
                    "used_gb": round(memory_gb, 2),
                    "used_percent": round(memory_percent, 1),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "peak_gb": round(self.peak_memory, 2)
                },
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "core_count": cpu_count,
                    "peak_percent": round(self.peak_cpu, 1)
                },
                "disk": {
                    "read_gb": round(disk_read_gb, 2),
                    "write_gb": round(disk_write_gb, 2),
                    "free_space_gb": round(disk_free_gb, 2)
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                } if net_io else {}
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Failed to get system stats: {str(e)}"}
    
    def log_stats(self, additional_info=None):
        """Log current stats to file"""
        stats = self.get_current_stats()
        if additional_info:
            stats.update(additional_info)
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(stats) + "\n")
    
    def get_performance_warning(self):
        """Check if system is under stress"""
        stats = self.get_current_stats()
        warnings = []
        
        if stats["memory"]["used_percent"] > 85:
            warnings.append(f"⚠️  High memory usage: {stats['memory']['used_percent']}%")
        
        if stats["cpu"]["usage_percent"] > 90:
            warnings.append(f"⚠️  High CPU usage: {stats['cpu']['usage_percent']}%")
        
        if stats["disk"]["free_space_gb"] < 10:
            warnings.append(f"⚠️  Low disk space: {stats['disk']['free_space_gb']:.1f}GB remaining")
        
        return warnings
    
    def estimate_processing_capacity(self, current_rows, target_rows):
        """Estimate if system can handle target scale"""
        stats = self.get_current_stats()
        
        # Rough estimates based on current usage
        memory_ratio = target_rows / current_rows if current_rows > 0 else 1
        estimated_memory_gb = stats["memory"]["used_gb"] * memory_ratio
        
        available_memory = stats["memory"]["available_gb"]
        
        can_handle = estimated_memory_gb < (available_memory * 0.8)  # Leave 20% buffer
        
        return {
            "can_handle_target": can_handle,
            "estimated_memory_needed_gb": round(estimated_memory_gb, 2),
            "available_memory_gb": round(available_memory, 2),
            "recommendation": (
                "✅ System can handle target scale" if can_handle 
                else "⚠️  May need more RAM or enable disk-based processing"
            )
        }
    
    def get_billion_row_readiness(self):
        """Check if system is ready for billion-row processing"""
        stats = self.get_current_stats()
        
        # Minimum requirements for billion-row processing
        min_memory_gb = 16
        min_cpu_cores = 4
        min_disk_space_gb = 100
        
        checks = {
            "memory_ok": stats["memory"]["available_gb"] >= min_memory_gb,
            "cpu_ok": stats["cpu"]["core_count"] >= min_cpu_cores,
            "disk_ok": stats["disk"]["free_space_gb"] >= min_disk_space_gb,
            "current_load_ok": (
                stats["memory"]["used_percent"] < 70 and 
                stats["cpu"]["usage_percent"] < 80
            )
        }
        
        all_good = all(checks.values())
        
        return {
            "ready_for_billion_rows": all_good,
            "checks": checks,
            "recommendations": [
                f"Memory: {stats['memory']['available_gb']:.1f}GB available (need {min_memory_gb}GB+)",
                f"CPU: {stats['cpu']['core_count']} cores (need {min_cpu_cores}+)", 
                f"Disk: {stats['disk']['free_space_gb']:.1f}GB free (need {min_disk_space_gb}GB+)",
                "Current system load is acceptable" if checks["current_load_ok"] else "System is under heavy load"
            ]
        }

# Global monitor instance
monitor = SystemMonitor()

def get_system_status():
    """Quick system status check"""
    return monitor.get_current_stats()

def check_billion_row_readiness():
    """Check if system can handle billion rows"""
    return monitor.get_billion_row_readiness()

if __name__ == "__main__":
    # Test the monitor
    print("🚀 BILLION-ROW System Monitor Test")
    print("=" * 50)
    
    stats = monitor.get_current_stats()
    print(f"Memory: {stats['memory']['used_gb']:.1f}GB used ({stats['memory']['used_percent']:.1f}%)")
    print(f"CPU: {stats['cpu']['usage_percent']:.1f}% ({stats['cpu']['core_count']} cores)")
    print(f"Disk: {stats['disk']['free_space_gb']:.1f}GB free")
    
    print("\n🔍 Billion-Row Readiness Check:")
    readiness = monitor.get_billion_row_readiness()
    print(f"Ready: {'✅ YES' if readiness['ready_for_billion_rows'] else '❌ NO'}")
    for rec in readiness['recommendations']:
        print(f"  • {rec}")