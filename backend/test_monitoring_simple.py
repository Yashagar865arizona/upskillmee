#!/usr/bin/env python3
"""
Simple test script for monitoring and error tracking functionality.
Tests health checks, performance monitoring, and error tracking.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.monitoring_service import monitoring_service, PerformanceMonitor, HealthChecker, ErrorTracker
from app.database import get_db
from app.models.analytics import SystemMetric

async def test_health_checks():
    """Test health check functionality"""
    print("🏥 Testing Health Checks...")
    
    try:
        # Test database health
        print("\n1. Testing database health check...")
        db_health = await monitoring_service.health_checker.check_database_health()
        print(f"   ✅ Database status: {db_health['status']}")
        if db_health['status'] == 'healthy':
            print(f"   ✅ Database response time: {db_health['response_time']:.3f}s")
            print(f"   ✅ Total connections: {db_health.get('total_connections', 'N/A')}")
        
        # Test system resources
        print("\n2. Testing system resource check...")
        system_health = await monitoring_service.health_checker.check_system_resources()
        print(f"   ✅ System status: {system_health['status']}")
        if system_health['status'] == 'healthy':
            print(f"   ✅ CPU usage: {system_health['cpu_percent']:.1f}%")
            print(f"   ✅ Memory usage: {system_health['memory']['percent']:.1f}%")
            print(f"   ✅ Disk usage: {system_health['disk']['percent']:.1f}%")
        
        # Test AI services
        print("\n3. Testing AI services check...")
        ai_health = await monitoring_service.health_checker.check_ai_services()
        print(f"   ✅ AI services status: {ai_health['status']}")
        
        # Test comprehensive health check
        print("\n4. Testing comprehensive health check...")
        overall_health = await monitoring_service.health_checker.run_all_checks()
        print(f"   ✅ Overall system status: {overall_health['overall_status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Health check test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_monitoring():
    """Test performance monitoring functionality"""
    print("\n📊 Testing Performance Monitoring...")
    
    try:
        # Simulate some API requests
        print("\n1. Simulating API requests...")
        endpoints = [
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/chat/message", "POST"),
            ("/api/v1/users/profile", "GET"),
            ("/api/v1/learning/plans", "GET"),
        ]
        
        for endpoint, method in endpoints:
            # Simulate different response times and status codes
            response_time = 0.1 + (hash(endpoint) % 100) / 1000  # 0.1-0.2 seconds
            status_code = 200 if hash(endpoint) % 10 < 9 else 500  # 90% success rate
            
            await monitoring_service.record_api_request(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code
            )
            
            print(f"   ✅ Recorded {method} {endpoint}: {response_time:.3f}s, status {status_code}")
        
        # Get performance statistics
        print("\n2. Getting performance statistics...")
        perf_stats = monitoring_service.performance_monitor.get_all_stats()
        
        for endpoint_key, stats in perf_stats.items():
            print(f"   📈 {endpoint_key}:")
            print(f"      - Avg response time: {stats['avg_response_time']:.3f}s")
            print(f"      - Request count: {stats['request_count']}")
            print(f"      - Error rate: {stats['error_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_tracking():
    """Test error tracking functionality"""
    print("\n🚨 Testing Error Tracking...")
    
    try:
        # Generate some test errors
        print("\n1. Generating test errors...")
        test_errors = [
            ValueError("Test validation error"),
            ConnectionError("Test connection error"),
            RuntimeError("Test runtime error"),
            KeyError("Test key error"),
        ]
        
        for i, error in enumerate(test_errors):
            monitoring_service.error_tracker.track_error(error, {
                "test_id": i,
                "endpoint": f"/test/endpoint/{i}",
                "user_id": f"test_user_{i}"
            })
            print(f"   ✅ Tracked error: {type(error).__name__}")
        
        # Get error summary
        print("\n2. Getting error summary...")
        error_summary = monitoring_service.error_tracker.get_error_summary(24)
        
        print(f"   📊 Total errors (24h): {error_summary['total_errors']}")
        print(f"   📊 Error rate: {error_summary['error_rate']:.1f} errors/hour")
        print(f"   📊 Most common error: {error_summary['most_common_error']}")
        print(f"   📊 Error types: {error_summary['error_types']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error tracking test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_system_status():
    """Test comprehensive system status"""
    print("\n🖥️  Testing System Status...")
    
    try:
        # Get comprehensive system status
        print("\n1. Getting comprehensive system status...")
        system_status = await monitoring_service.get_system_status()
        
        print(f"   ✅ System uptime: {system_status['uptime_seconds']:.1f} seconds")
        print(f"   ✅ Overall health: {system_status['health']['overall_status']}")
        print(f"   ✅ Total errors (24h): {system_status['errors']['total_errors']}")
        print(f"   ✅ Performance endpoints tracked: {len(system_status['performance'])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ System status test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_metrics_storage():
    """Test metrics storage to database"""
    print("\n💾 Testing Metrics Storage...")
    
    try:
        # Store metrics to database
        print("\n1. Storing metrics to database...")
        await monitoring_service.store_metrics_to_database()
        print("   ✅ Metrics stored to database")
        
        # Verify metrics were stored
        print("\n2. Verifying stored metrics...")
        db = next(get_db())
        
        recent_metrics = db.query(SystemMetric).filter(
            SystemMetric.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).all()
        
        print(f"   ✅ Found {len(recent_metrics)} recent metrics in database")
        
        for metric in recent_metrics[:5]:  # Show first 5 metrics
            print(f"      - {metric.metric_name}: {metric.metric_value} ({metric.metric_type})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Metrics storage test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_historical_metrics():
    """Test historical metrics retrieval"""
    print("\n📈 Testing Historical Metrics...")
    
    try:
        # Get historical metrics
        print("\n1. Getting historical metrics...")
        historical_data = await monitoring_service.get_historical_metrics("system_uptime", 24)
        
        print(f"   ✅ Retrieved {len(historical_data)} historical data points")
        
        if historical_data:
            latest = historical_data[-1]
            print(f"   ✅ Latest uptime metric: {latest['value']:.1f}s at {latest['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Historical metrics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all monitoring tests"""
    print("🚀 Starting Monitoring System Tests")
    print("=" * 60)
    
    # Run async tests
    loop = asyncio.get_event_loop()
    
    tests = [
        ("Health Checks", test_health_checks),
        ("Performance Monitoring", test_performance_monitoring),
        ("Error Tracking", test_error_tracking),
        ("System Status", test_system_status),
        ("Metrics Storage", test_metrics_storage),
        ("Historical Metrics", test_historical_metrics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = loop.run_until_complete(test_func())
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("-" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All monitoring tests completed successfully!")
        print("\n📊 Monitoring system is ready for production use!")
        print("\nNext steps:")
        print("1. Start the backend server: uvicorn app.main:app --reload")
        print("2. Check health status: GET /api/v1/monitoring/health")
        print("3. View system status: GET /api/v1/monitoring/status (admin required)")
        print("4. Monitor performance: GET /api/v1/monitoring/performance (admin required)")
        print("5. Check for alerts: GET /api/v1/monitoring/alerts (admin required)")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()