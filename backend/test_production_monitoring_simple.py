#!/usr/bin/env python3
"""
Simple test script for production monitoring system.
Tests core functionality without external dependencies.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_basic_functionality():
    """Test basic production monitoring functionality"""
    print("Testing basic production monitoring functionality...")
    
    try:
        from app.services.production_monitoring import production_monitoring, IncidentStatus
        from app.services.backup_monitoring_service import backup_monitoring
        from app.services.alerting_service import alerting_service, AlertType, AlertSeverity
        
        print("✓ All modules imported successfully")
        
        # Test incident manager
        incident = await production_monitoring.incident_manager.create_incident(
            title="Test Incident",
            description="Test incident for validation",
            severity=AlertSeverity.LOW,
            affected_services=["test"]
        )
        print(f"✓ Test incident created: {incident.id}")
        
        # Test incident status update
        success = await production_monitoring.incident_manager.update_incident_status(
            incident.id,
            IncidentStatus.RESOLVED,
            "Test resolved"
        )
        print(f"✓ Incident status updated: {success}")
        
        # Test backup monitoring
        backup_jobs = backup_monitoring.get_backup_jobs()
        print(f"✓ Backup jobs retrieved: {len(backup_jobs)} jobs")
        
        # Test backup health check
        health_status = await backup_monitoring.check_backup_health()
        print(f"✓ Backup health check completed: {health_status.get('overall_status')}")
        
        # Test alerting
        alert = await alerting_service.create_alert(
            AlertType.CUSTOM,
            AlertSeverity.LOW,
            "Test Alert",
            "Test alert message",
            {"test": True}
        )
        print(f"✓ Test alert created: {alert.id}")
        
        # Resolve alert
        resolved = await alerting_service.resolve_alert(alert.id)
        print(f"✓ Alert resolved: {resolved}")
        
        # Test log aggregation (basic)
        log_analysis = await production_monitoring.log_aggregator.collect_logs()
        print(f"✓ Log analysis completed: {log_analysis.get('total_logs', 0)} logs")
        
        # Test service health
        service_health = await production_monitoring._get_service_health()
        print(f"✓ Service health check: {len(service_health)} services")
        
        # Test performance metrics
        performance_metrics = await production_monitoring._get_performance_metrics()
        print(f"✓ Performance metrics collected")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dashboard_data():
    """Test dashboard data collection"""
    print("\nTesting dashboard data collection...")
    
    try:
        from app.services.production_monitoring import production_monitoring
        
        dashboard_data = await production_monitoring.get_production_dashboard()
        
        print(f"✓ Dashboard data retrieved")
        print(f"  - Timestamp: {dashboard_data.get('timestamp')}")
        print(f"  - Has system status: {'system_status' in dashboard_data}")
        print(f"  - Has service health: {'service_health' in dashboard_data}")
        print(f"  - Has performance metrics: {'performance_metrics' in dashboard_data}")
        print(f"  - Has log analysis: {'log_analysis' in dashboard_data}")
        print(f"  - Active incidents: {len(dashboard_data.get('active_incidents', []))}")
        print(f"  - Active alerts: {len(dashboard_data.get('active_alerts', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        return False

async def test_runbooks():
    """Test incident runbooks"""
    print("\nTesting incident runbooks...")
    
    try:
        from app.services.production_monitoring import production_monitoring
        
        # Test available runbooks
        runbook_types = ["database_down", "high_error_rate", "system_overload"]
        
        for runbook_type in runbook_types:
            runbook = production_monitoring.incident_manager.get_runbook(runbook_type)
            if runbook:
                print(f"✓ Runbook '{runbook_type}': {runbook['title']}")
                print(f"  - Steps: {len(runbook['steps'])}")
                print(f"  - Escalation time: {runbook['escalation_time']} minutes")
            else:
                print(f"✗ Runbook '{runbook_type}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Runbook test failed: {e}")
        return False

async def run_simple_tests():
    """Run simple production monitoring tests"""
    print("=" * 50)
    print("PRODUCTION MONITORING SIMPLE TEST")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Dashboard Data", test_dashboard_data),
        ("Runbooks", test_runbooks),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} test encountered an exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All production monitoring tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_simple_tests())
    sys.exit(0 if success else 1)