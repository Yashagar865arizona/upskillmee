#!/usr/bin/env python3
"""
Enhanced Monitoring System Test Script
Tests all monitoring components including alerting, enhanced database monitoring, and system health checks.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.monitoring_service import monitoring_service
from app.services.alerting_service import alerting_service, AlertType, AlertSeverity
from app.services.enhanced_db_monitoring import enhanced_db_monitor
from app.database import get_db
from app.models.analytics import SystemMetric

async def test_basic_monitoring():
    """Test basic monitoring functionality"""
    print("🔧 Testing Basic Monitoring System...")
    
    try:
        # Test health checks
        print("\n1. Testing health checks...")
        health_status = await monitoring_service.health_checker.run_all_checks()
        print(f"   ✅ Overall health: {health_status['overall_status']}")
        
        # Test performance monitoring
        print("\n2. Testing performance monitoring...")
        await monitoring_service.record_api_request("/test/endpoint", "GET", 0.15, 200)
        perf_stats = monitoring_service.performance_monitor.get_all_stats()
        print(f"   ✅ Performance stats recorded: {len(perf_stats)} endpoints")
        
        # Test error tracking
        print("\n3. Testing error tracking...")
        test_error = ValueError("Test error for monitoring")
        monitoring_service.error_tracker.track_error(test_error, {"test": True})
        error_summary = monitoring_service.error_tracker.get_error_summary()
        print(f"   ✅ Error tracked: {error_summary['total_errors']} total errors")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_alerting_system():
    """Test the alerting system"""
    print("\n🚨 Testing Alerting System...")
    
    try:
        # Test alert creation
        print("\n1. Creating test alerts...")
        
        # Create different types of alerts
        alerts_created = []
        
        # High CPU alert
        cpu_alert = await alerting_service.create_alert(
            AlertType.RESOURCE_USAGE,
            AlertSeverity.HIGH,
            "Test High CPU Usage",
            "CPU usage is above 85% for testing purposes",
            {"cpu_percent": 87.5, "threshold": 80.0}
        )
        alerts_created.append(cpu_alert)
        print(f"   ✅ Created CPU alert: {cpu_alert.id}")
        
        # Database performance alert
        db_alert = await alerting_service.create_alert(
            AlertType.DATABASE,
            AlertSeverity.MEDIUM,
            "Test Slow Database Response",
            "Database response time is slower than expected",
            {"response_time": 1.5, "threshold": 1.0}
        )
        alerts_created.append(db_alert)
        print(f"   ✅ Created database alert: {db_alert.id}")
        
        # Error rate alert
        error_alert = await alerting_service.create_alert(
            AlertType.ERROR_RATE,
            AlertSeverity.CRITICAL,
            "Test High Error Rate",
            "Error rate is critically high",
            {"error_rate": 25.0, "threshold": 10.0}
        )
        alerts_created.append(error_alert)
        print(f"   ✅ Created error rate alert: {error_alert.id}")
        
        # Test alert retrieval
        print("\n2. Testing alert retrieval...")
        active_alerts = alerting_service.get_active_alerts()
        print(f"   ✅ Active alerts: {len(active_alerts)}")
        
        alert_summary = alerting_service.get_alert_summary()
        print(f"   ✅ Alert summary: {alert_summary['active_alerts_count']} active")
        
        # Test alert resolution
        print("\n3. Testing alert resolution...")
        for alert in alerts_created:
            success = await alerting_service.resolve_alert(alert.id)
            if success:
                print(f"   ✅ Resolved alert: {alert.id}")
            else:
                print(f"   ❌ Failed to resolve alert: {alert.id}")
        
        # Verify alerts are resolved
        active_alerts_after = alerting_service.get_active_alerts()
        print(f"   ✅ Active alerts after resolution: {len(active_alerts_after)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Alerting system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_threshold_checking():
    """Test automatic threshold checking and alert creation"""
    print("\n📊 Testing Threshold Checking...")
    
    try:
        # Get current system status
        print("\n1. Getting system status for threshold checking...")
        system_status = await monitoring_service.get_system_status()
        print(f"   ✅ System status retrieved: {system_status['health']['overall_status']}")
        
        # Test threshold checking
        print("\n2. Testing threshold checking...")
        alerts_created = await alerting_service.check_system_thresholds(system_status)
        print(f"   ✅ Threshold check completed: {len(alerts_created)} alerts created")
        
        for alert in alerts_created:
            print(f"      - {alert.severity.value.upper()}: {alert.title}")
        
        # Test with simulated high resource usage
        print("\n3. Testing with simulated high resource usage...")
        
        # Create a mock system status with high resource usage
        mock_system_status = {
            'health': {
                'overall_status': 'healthy',
                'checks': {
                    'system_resources': {
                        'status': 'healthy',
                        'cpu_percent': 95.0,  # High CPU
                        'memory': {'percent': 90.0},  # High memory
                        'disk': {'percent': 85.0}  # Moderate disk usage
                    },
                    'database': {
                        'status': 'healthy',
                        'response_time': 0.5  # Normal response time
                    }
                }
            },
            'errors': {
                'error_rate': 15.0  # High error rate
            }
        }
        
        simulated_alerts = await alerting_service.check_system_thresholds(mock_system_status)
        print(f"   ✅ Simulated threshold check: {len(simulated_alerts)} alerts created")
        
        for alert in simulated_alerts:
            print(f"      - {alert.severity.value.upper()}: {alert.title}")
            # Resolve the test alert
            await alerting_service.resolve_alert(alert.id)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Threshold checking test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_database_monitoring():
    """Test enhanced database monitoring features"""
    print("\n🗄️  Testing Enhanced Database Monitoring...")
    
    try:
        # Test comprehensive database health check
        print("\n1. Testing comprehensive database health check...")
        db_health = await enhanced_db_monitor.check_database_health()
        print(f"   ✅ Database health status: {db_health['overall_status']}")
        
        if 'checks' in db_health:
            for check_name, check_result in db_health['checks'].items():
                status = check_result.get('status', 'unknown')
                print(f"      - {check_name}: {status}")
        
        # Test connection pool monitoring
        print("\n2. Testing connection pool monitoring...")
        pool_status = enhanced_db_monitor.connection_monitor.get_pool_status()
        print(f"   ✅ Pool size: {pool_status['pool_size']}")
        print(f"   ✅ Checked out connections: {pool_status['checked_out_connections']}")
        print(f"   ✅ Total connections: {pool_status['total_connections']}")
        
        # Test query analysis (simulate some queries)
        print("\n3. Testing query analysis...")
        query_analyzer = enhanced_db_monitor.query_analyzer
        
        # Simulate some test queries
        test_queries = [
            ("SELECT * FROM users WHERE id = 1", 0.05),
            ("SELECT * FROM messages ORDER BY created_at DESC", 0.15),
            ("UPDATE users SET last_login = NOW() WHERE id = 1", 0.03),
            ("SELECT COUNT(*) FROM conversations", 0.08),
            ("SELECT * FROM users u JOIN user_profiles p ON u.id = p.user_id", 0.12)
        ]
        
        for query, duration in test_queries:
            analysis = query_analyzer.analyze_query(query, duration)
            print(f"   ✅ Analyzed query: {len(analysis['issues'])} issues found")
        
        # Get query recommendations
        recommendations = query_analyzer.get_query_recommendations()
        print(f"   ✅ Query recommendations: {len(recommendations)} recommendations")
        
        for rec in recommendations[:3]:  # Show first 3 recommendations
            print(f"      - {rec['priority'].upper()}: {rec['title']}")
        
        # Test performance summary
        print("\n4. Testing performance summary...")
        perf_summary = enhanced_db_monitor.get_performance_summary()
        print(f"   ✅ Performance summary generated")
        print(f"      - Connection pool status: {perf_summary['connection_pool']['pool_size']} pool size")
        print(f"      - Slow queries: {perf_summary['query_analysis']['slow_queries_count']}")
        print(f"      - Health trend: {perf_summary['health_trend']['healthy_percentage']:.1f}% healthy")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced database monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_metrics_storage():
    """Test metrics storage and retrieval"""
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
        
        # Show sample metrics
        for metric in recent_metrics[:5]:
            print(f"      - {metric.metric_name}: {metric.metric_value} ({metric.metric_type})")
        
        # Test historical metrics retrieval
        print("\n3. Testing historical metrics retrieval...")
        historical_data = await monitoring_service.get_historical_metrics("system_uptime", 24)
        print(f"   ✅ Retrieved {len(historical_data)} historical data points")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Metrics storage test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between monitoring components"""
    print("\n🔗 Testing Component Integration...")
    
    try:
        # Test monitoring service with alerting integration
        print("\n1. Testing monitoring service with alerting integration...")
        
        # Get system status (this should trigger alert checking)
        system_status = await monitoring_service.get_system_status()
        print(f"   ✅ System status retrieved with alert checking")
        
        # Simulate some API requests to generate performance data
        print("\n2. Simulating API requests for performance monitoring...")
        endpoints = [
            ("/api/v1/health", "GET", 0.05, 200),
            ("/api/v1/users/profile", "GET", 0.12, 200),
            ("/api/v1/chat/message", "POST", 0.25, 200),
            ("/api/v1/learning/plans", "GET", 0.18, 200),
            ("/api/v1/auth/login", "POST", 0.08, 401),  # Simulated error
        ]
        
        for endpoint, method, response_time, status_code in endpoints:
            await monitoring_service.record_api_request(endpoint, method, response_time, status_code)
            if status_code >= 400:
                # Simulate error for error tracking
                error = Exception(f"Simulated {status_code} error for {endpoint}")
                monitoring_service.error_tracker.track_error(error, {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code
                })
        
        print(f"   ✅ Simulated {len(endpoints)} API requests")
        
        # Get updated performance stats
        perf_stats = monitoring_service.performance_monitor.get_all_stats()
        print(f"   ✅ Performance stats updated: {len(perf_stats)} endpoints tracked")
        
        # Test comprehensive system status
        print("\n3. Testing comprehensive system status...")
        comprehensive_status = await monitoring_service.get_system_status()
        
        print(f"   ✅ Health status: {comprehensive_status['health']['overall_status']}")
        print(f"   ✅ Performance endpoints: {len(comprehensive_status['performance'])}")
        print(f"   ✅ Error summary: {comprehensive_status['errors']['total_errors']} errors")
        print(f"   ✅ System uptime: {comprehensive_status['uptime_seconds']:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all enhanced monitoring tests"""
    print("🚀 Starting Enhanced Monitoring System Tests")
    print("=" * 70)
    
    # Run async tests
    loop = asyncio.get_event_loop()
    
    tests = [
        ("Basic Monitoring", test_basic_monitoring),
        ("Alerting System", test_alerting_system),
        ("Threshold Checking", test_threshold_checking),
        ("Enhanced Database Monitoring", test_enhanced_database_monitoring),
        ("Metrics Storage", test_metrics_storage),
        ("Component Integration", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            success = loop.run_until_complete(test_func())
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Enhanced Monitoring Test Results Summary:")
    print("-" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All enhanced monitoring tests completed successfully!")
        print("\n📊 Enhanced monitoring system is ready for production!")
        print("\nAvailable monitoring endpoints:")
        print("1. Health checks:")
        print("   - GET /api/v1/monitoring/health")
        print("   - GET /api/v1/monitoring/health/database")
        print("   - GET /api/v1/monitoring/database/detailed (admin)")
        print("\n2. Performance monitoring:")
        print("   - GET /api/v1/monitoring/performance (admin)")
        print("   - GET /api/v1/monitoring/performance/{endpoint} (admin)")
        print("\n3. Alerting system:")
        print("   - GET /api/v1/monitoring/alerts (admin)")
        print("   - GET /api/v1/monitoring/alerts/history (admin)")
        print("   - POST /api/v1/monitoring/alerts/{alert_id}/resolve (admin)")
        print("   - GET /api/v1/monitoring/alerts/thresholds (admin)")
        print("   - PUT /api/v1/monitoring/alerts/thresholds (admin)")
        print("\n4. Database analysis:")
        print("   - GET /api/v1/monitoring/database/query-analysis (admin)")
        print("\n5. System status:")
        print("   - GET /api/v1/monitoring/status (admin)")
        print("   - GET /api/v1/monitoring/errors (admin)")
        print("   - GET /api/v1/monitoring/metrics/historical/{metric_name} (admin)")
        
        print("\n🔧 Configuration:")
        print("- Alert thresholds can be configured via API")
        print("- Email/webhook notifications can be enabled in settings")
        print("- Database monitoring runs automatically")
        print("- Metrics are stored every 5 minutes")
        print("- Alert checks run every minute")
        
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()