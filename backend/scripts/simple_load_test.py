#!/usr/bin/env python3
"""
Simple load test for API endpoints without authentication.
"""

import asyncio
import aiohttp
import time
import statistics
import logging
from typing import List, Dict, Any
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleLoadTester:
    """Simple load tester for public API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str, 
                           method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """Test a single endpoint."""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    content = await response.text()
                    end_time = time.time()
                    
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status,
                        "response_time": end_time - start_time,
                        "content_length": len(content),
                        "success": 200 <= response.status < 400
                    }
            else:
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    content = await response.text()
                    end_time = time.time()
                    
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status,
                        "response_time": end_time - start_time,
                        "content_length": len(content),
                        "success": 200 <= response.status < 400
                    }
                    
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": end_time - start_time,
                "content_length": 0,
                "success": False,
                "error": str(e)
            }
    
    async def run_concurrent_tests(self, endpoints: List[Dict[str, Any]], 
                                  concurrent_requests: int = 10, 
                                  total_requests: int = 100) -> List[Dict[str, Any]]:
        """Run concurrent tests on multiple endpoints."""
        logger.info(f"Starting load test with {concurrent_requests} concurrent requests")
        logger.info(f"Total requests: {total_requests}")
        
        results = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=concurrent_requests * 2)
        ) as session:
            
            # Create tasks for all requests
            tasks = []
            for i in range(total_requests):
                endpoint_config = endpoints[i % len(endpoints)]
                task = asyncio.create_task(
                    self.test_endpoint(
                        session, 
                        endpoint_config["endpoint"],
                        endpoint_config.get("method", "GET"),
                        endpoint_config.get("data")
                    )
                )
                tasks.append(task)
                
                # Control concurrency
                if len(tasks) >= concurrent_requests:
                    completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in completed_tasks:
                        if isinstance(result, dict):
                            results.append(result)
                        else:
                            logger.error(f"Task failed: {result}")
                    tasks = []
                    
                    # Small delay to prevent overwhelming the server
                    await asyncio.sleep(0.01)
            
            # Process remaining tasks
            if tasks:
                completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
                for result in completed_tasks:
                    if isinstance(result, dict):
                        results.append(result)
                    else:
                        logger.error(f"Task failed: {result}")
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze load test results."""
        if not results:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        # Response time statistics
        response_times = [r["response_time"] for r in results if r["success"]]
        
        response_time_stats = {}
        if response_times:
            response_time_stats = {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
            }
        
        # Status code distribution
        status_codes = {}
        for result in results:
            status = result["status_code"]
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # Endpoint performance
        endpoint_stats = {}
        for result in results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "response_times": []
                }
            
            endpoint_stats[endpoint]["total_requests"] += 1
            if result["success"]:
                endpoint_stats[endpoint]["successful_requests"] += 1
                endpoint_stats[endpoint]["response_times"].append(result["response_time"])
        
        # Calculate endpoint averages
        for endpoint, stats in endpoint_stats.items():
            if stats["response_times"]:
                stats["avg_response_time"] = statistics.mean(stats["response_times"])
                stats["success_rate"] = (stats["successful_requests"] / stats["total_requests"]) * 100
            else:
                stats["avg_response_time"] = 0
                stats["success_rate"] = 0
            del stats["response_times"]  # Remove raw data to save space
        
        # Error analysis
        errors = {}
        for result in results:
            if not result["success"] and "error" in result:
                error = result["error"]
                errors[error] = errors.get(error, 0) + 1
        
        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate
            },
            "response_time_stats": response_time_stats,
            "status_code_distribution": status_codes,
            "endpoint_performance": endpoint_stats,
            "errors": errors
        }
    
    def print_results(self, analysis: Dict[str, Any]):
        """Print load test results."""
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        
        summary = analysis["summary"]
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful Requests: {summary['successful_requests']}")
        print(f"Failed Requests: {summary['failed_requests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        response_stats = analysis.get("response_time_stats", {})
        if response_stats:
            print(f"\nResponse Time Statistics:")
            print(f"  Min: {response_stats['min']:.3f}s")
            print(f"  Max: {response_stats['max']:.3f}s")
            print(f"  Mean: {response_stats['mean']:.3f}s")
            print(f"  Median: {response_stats['median']:.3f}s")
            print(f"  95th Percentile: {response_stats['p95']:.3f}s")
            print(f"  99th Percentile: {response_stats['p99']:.3f}s")
        
        status_codes = analysis.get("status_code_distribution", {})
        if status_codes:
            print(f"\nStatus Code Distribution:")
            for status, count in sorted(status_codes.items()):
                print(f"  {status}: {count} requests")
        
        endpoint_perf = analysis.get("endpoint_performance", {})
        if endpoint_perf:
            print(f"\nEndpoint Performance:")
            for endpoint, stats in endpoint_perf.items():
                print(f"  {endpoint}:")
                print(f"    Requests: {stats['total_requests']}")
                print(f"    Success Rate: {stats['success_rate']:.1f}%")
                print(f"    Avg Response Time: {stats['avg_response_time']:.3f}s")
        
        errors = analysis.get("errors", {})
        if errors:
            print(f"\nErrors:")
            for error, count in errors.items():
                print(f"  {error}: {count} occurrences")
    
    def save_results(self, analysis: Dict[str, Any], filename: str = None):
        """Save results to JSON file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"load_test_results_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath


async def main():
    """Main function to run load test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Load Test for Ponder API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--total", type=int, default=100, help="Total requests")
    parser.add_argument("--save", help="Save results to specific file")
    
    args = parser.parse_args()
    
    # Define endpoints to test (public endpoints only)
    endpoints = [
        {"endpoint": "/", "method": "GET"},
        {"endpoint": "/test", "method": "GET"},
        {"endpoint": "/api/v1/health", "method": "GET"},
        {"endpoint": "/health", "method": "GET"},
    ]
    
    tester = SimpleLoadTester(args.url)
    
    try:
        start_time = time.time()
        results = await tester.run_concurrent_tests(
            endpoints, 
            concurrent_requests=args.concurrent,
            total_requests=args.total
        )
        end_time = time.time()
        
        analysis = tester.analyze_results(results)
        analysis["test_duration"] = end_time - start_time
        analysis["throughput"] = len(results) / (end_time - start_time) if end_time > start_time else 0
        
        tester.print_results(analysis)
        
        print(f"\nTest Duration: {analysis['test_duration']:.2f} seconds")
        print(f"Throughput: {analysis['throughput']:.2f} requests/second")
        
        if args.save:
            tester.save_results(analysis, args.save)
        else:
            tester.save_results(analysis)
        
    except KeyboardInterrupt:
        logger.info("Load test interrupted by user")
    except Exception as e:
        logger.error(f"Load test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())