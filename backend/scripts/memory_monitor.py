#!/usr/bin/env python3
"""
Memory usage monitoring script for Ponder backend.
Monitors memory consumption under load and identifies memory leaks.
"""

import psutil
import time
import json
import logging
import threading
from typing import Dict, List, Any
import requests
import sys
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitors system and application memory usage."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.monitoring = False
        self.data_points = []
        self.process_data = []
        
    def get_system_memory_info(self) -> Dict[str, Any]:
        """Get current system memory information."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "timestamp": time.time(),
            "system_memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
                "active": getattr(memory, 'active', 0),
                "inactive": getattr(memory, 'inactive', 0),
                "buffers": getattr(memory, 'buffers', 0),
                "cached": getattr(memory, 'cached', 0)
            },
            "swap_memory": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            }
        }
    
    def get_process_memory_info(self) -> List[Dict[str, Any]]:
        """Get memory information for Python processes."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # Check if it's our application
                    is_ponder_process = any(keyword in cmdline.lower() for keyword in 
                                          ['ponder', 'uvicorn', 'fastapi', 'main.py'])
                    
                    memory_info = proc.info['memory_info']
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline,
                        "is_ponder_process": is_ponder_process,
                        "memory": {
                            "rss": memory_info.rss,  # Resident Set Size
                            "vms": memory_info.vms,  # Virtual Memory Size
                            "percent": proc.info['memory_percent']
                        }
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(processes, key=lambda x: x['memory']['rss'], reverse=True)
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific memory metrics from the API."""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/metrics/memory", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not get application metrics: {e}")
        
        return {}
    
    def collect_data_point(self) -> Dict[str, Any]:
        """Collect a single data point."""
        data_point = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "system": self.get_system_memory_info(),
            "processes": self.get_process_memory_info(),
            "application": self.get_application_metrics()
        }
        
        return data_point
    
    def start_monitoring(self, interval: float = 5.0, duration: int = 300):
        """Start continuous memory monitoring."""
        logger.info(f"Starting memory monitoring for {duration} seconds (interval: {interval}s)")
        
        self.monitoring = True
        self.data_points = []
        
        start_time = time.time()
        end_time = start_time + duration
        
        while self.monitoring and time.time() < end_time:
            try:
                data_point = self.collect_data_point()
                self.data_points.append(data_point)
                
                # Log current memory usage
                system_memory = data_point["system"]["system_memory"]
                logger.info(f"Memory usage: {system_memory['percent']:.1f}% "
                           f"({system_memory['used'] / 1024**3:.2f}GB / "
                           f"{system_memory['total'] / 1024**3:.2f}GB)")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                time.sleep(interval)
        
        self.monitoring = False
        logger.info(f"Memory monitoring completed. Collected {len(self.data_points)} data points.")
    
    def analyze_memory_trends(self) -> Dict[str, Any]:
        """Analyze memory usage trends and detect potential leaks."""
        if not self.data_points:
            return {"error": "No data points available"}
        
        # Extract memory usage over time
        timestamps = [dp["timestamp"] for dp in self.data_points]
        memory_percentages = [dp["system"]["system_memory"]["percent"] for dp in self.data_points]
        memory_used = [dp["system"]["system_memory"]["used"] for dp in self.data_points]
        
        # Calculate trends
        start_memory = memory_percentages[0]
        end_memory = memory_percentages[-1]
        memory_change = end_memory - start_memory
        
        # Find peak usage
        peak_memory = max(memory_percentages)
        peak_index = memory_percentages.index(peak_memory)
        peak_time = timestamps[peak_index]
        
        # Calculate average usage
        avg_memory = sum(memory_percentages) / len(memory_percentages)
        
        # Detect potential memory leak (consistent upward trend)
        # Simple linear regression to detect trend
        n = len(memory_percentages)
        sum_x = sum(range(n))
        sum_y = sum(memory_percentages)
        sum_xy = sum(i * memory_percentages[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Analyze process memory trends
        process_trends = {}
        if self.data_points:
            for dp in self.data_points:
                for proc in dp["processes"]:
                    if proc["is_ponder_process"]:
                        pid = proc["pid"]
                        if pid not in process_trends:
                            process_trends[pid] = {
                                "name": proc["name"],
                                "cmdline": proc["cmdline"],
                                "memory_points": []
                            }
                        process_trends[pid]["memory_points"].append({
                            "timestamp": dp["timestamp"],
                            "rss": proc["memory"]["rss"],
                            "vms": proc["memory"]["vms"],
                            "percent": proc["memory"]["percent"]
                        })
        
        return {
            "monitoring_duration": timestamps[-1] - timestamps[0],
            "data_points_collected": len(self.data_points),
            "memory_usage": {
                "start_percent": start_memory,
                "end_percent": end_memory,
                "change_percent": memory_change,
                "peak_percent": peak_memory,
                "peak_time": peak_time,
                "average_percent": avg_memory
            },
            "trend_analysis": {
                "slope": slope,
                "trend": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
                "potential_leak": slope > 0.5,  # Significant upward trend
                "leak_severity": "high" if slope > 1.0 else "medium" if slope > 0.5 else "low"
            },
            "process_trends": process_trends
        }
    
    def generate_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory usage report."""
        analysis = self.analyze_memory_trends()
        
        # Get current system info
        current_info = self.collect_data_point()
        
        # Calculate statistics
        if self.data_points:
            memory_values = [dp["system"]["system_memory"]["percent"] for dp in self.data_points]
            memory_stats = {
                "min": min(memory_values),
                "max": max(memory_values),
                "mean": sum(memory_values) / len(memory_values),
                "median": sorted(memory_values)[len(memory_values) // 2]
            }
        else:
            memory_stats = {}
        
        # Generate recommendations
        recommendations = []
        
        if analysis.get("trend_analysis", {}).get("potential_leak"):
            recommendations.append("Potential memory leak detected. Monitor application for memory growth.")
        
        if current_info["system"]["system_memory"]["percent"] > 80:
            recommendations.append("High memory usage detected. Consider scaling or optimization.")
        
        if current_info["system"]["swap_memory"]["percent"] > 10:
            recommendations.append("Swap usage detected. Consider increasing physical memory.")
        
        # Check for high memory processes
        for proc in current_info["processes"]:
            if proc["is_ponder_process"] and proc["memory"]["percent"] > 10:
                recommendations.append(f"High memory usage in process {proc['pid']}: {proc['memory']['percent']:.1f}%")
        
        return {
            "timestamp": time.time(),
            "current_status": current_info,
            "trend_analysis": analysis,
            "memory_statistics": memory_stats,
            "recommendations": recommendations,
            "raw_data_points": len(self.data_points)
        }
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save memory report to file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"memory_report_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Memory report saved to: {filepath}")
        return filepath
    
    def print_report(self, report: Dict[str, Any]):
        """Print memory report summary."""
        print("\n" + "="*60)
        print("MEMORY USAGE REPORT")
        print("="*60)
        
        current = report["current_status"]["system"]["system_memory"]
        print(f"Current Memory Usage: {current['percent']:.1f}%")
        print(f"  Total: {current['total'] / 1024**3:.2f} GB")
        print(f"  Used: {current['used'] / 1024**3:.2f} GB")
        print(f"  Available: {current['available'] / 1024**3:.2f} GB")
        
        swap = report["current_status"]["system"]["swap_memory"]
        print(f"Swap Usage: {swap['percent']:.1f}%")
        
        # Trend analysis
        trend = report["trend_analysis"]
        if "memory_usage" in trend:
            memory_usage = trend["memory_usage"]
            print(f"\nMemory Trend Analysis:")
            print(f"  Duration: {trend['monitoring_duration']:.0f} seconds")
            print(f"  Start Usage: {memory_usage['start_percent']:.1f}%")
            print(f"  End Usage: {memory_usage['end_percent']:.1f}%")
            print(f"  Change: {memory_usage['change_percent']:+.1f}%")
            print(f"  Peak Usage: {memory_usage['peak_percent']:.1f}%")
            
            trend_analysis = trend["trend_analysis"]
            print(f"  Trend: {trend_analysis['trend']}")
            if trend_analysis["potential_leak"]:
                print(f"  ⚠️  Potential memory leak detected (severity: {trend_analysis['leak_severity']})")
        
        # Process information
        processes = report["current_status"]["processes"]
        ponder_processes = [p for p in processes if p["is_ponder_process"]]
        
        if ponder_processes:
            print(f"\nPonder Processes:")
            for proc in ponder_processes[:5]:  # Show top 5
                print(f"  PID {proc['pid']}: {proc['memory']['percent']:.1f}% "
                      f"({proc['memory']['rss'] / 1024**2:.1f} MB)")
        
        # Recommendations
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")


def simulate_load_and_monitor(api_url: str, duration: int = 300):
    """Simulate load while monitoring memory usage."""
    monitor = MemoryMonitor(api_url)
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(
        target=monitor.start_monitoring,
        args=(5.0, duration)  # 5 second intervals for specified duration
    )
    monitor_thread.start()
    
    # Simulate some load
    logger.info("Simulating API load...")
    
    def make_requests():
        """Make continuous API requests to simulate load."""
        import requests
        import random
        
        endpoints = [
            "/api/v1/health",
            "/api/v1/metrics/system",
            "/",
        ]
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration - 10:  # Stop 10 seconds before monitoring ends
            try:
                endpoint = random.choice(endpoints)
                response = requests.get(f"{api_url}{endpoint}", timeout=5)
                request_count += 1
                
                if request_count % 50 == 0:
                    logger.info(f"Made {request_count} requests")
                
                time.sleep(0.1)  # 10 requests per second
                
            except Exception as e:
                logger.warning(f"Request failed: {e}")
                time.sleep(1)
    
    # Start load simulation
    load_thread = threading.Thread(target=make_requests)
    load_thread.start()
    
    # Wait for monitoring to complete
    monitor_thread.join()
    
    # Generate and save report
    report = monitor.generate_memory_report()
    report_path = monitor.save_report(report)
    monitor.print_report(report)
    
    return report_path


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Usage Monitor for Ponder")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=float, default=5.0, help="Monitoring interval in seconds")
    parser.add_argument("--load", action="store_true", help="Simulate load during monitoring")
    parser.add_argument("--save", help="Save report to specific file")
    
    args = parser.parse_args()
    
    if args.load:
        report_path = simulate_load_and_monitor(args.url, args.duration)
        print(f"\nMemory report with load simulation saved to: {report_path}")
    else:
        monitor = MemoryMonitor(args.url)
        monitor.start_monitoring(args.interval, args.duration)
        
        report = monitor.generate_memory_report()
        
        if args.save:
            report_path = monitor.save_report(report, args.save)
        else:
            report_path = monitor.save_report(report)
        
        monitor.print_report(report)
        print(f"\nMemory report saved to: {report_path}")


if __name__ == "__main__":
    main()