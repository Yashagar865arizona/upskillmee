#!/usr/bin/env python3
"""
Test script for production monitoring system.
Tests monitoring dashboards, incident management, backup monitoring, and log aggregation.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.production_monitoring import production_monitoring, IncidentStatus
from app.services.backup_monitoring_service import backup_monitoring, BackupStatus
from app.services.alerting_service import alerting_service, AlertType, AlertSeverity

async def test_production_dashboard():
    """Test production monitoring dashboard"""
    print("Testing production monitoring dashboard...")
    
    try:
        dashboard_data = await production_monitoring.get_production_dashboard()
        
        print(f"✓ Dashboard data retrieved successfully")
        print(f"  - Timestamp: {dashboard_data.get('timestamp')}")
        print(f"  - System status: {dashboard_data.get('system_status', {}).get('health', {}).get('overall_status')}")
        print(f"  - Active incidents: {len(dashboard_data.get('active_incidents', []))}")
        print(f"  - Active alerts: {len(dashboard_data.get('active_alerts', []))}")
        print(f"  - Uptime: {dashboard_data.get('uptime', 0):.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        return False

async def test_log_aggregation():
    """Test log aggregation and analysis"""
    print("\nTesting log aggregation...")
    
    try:
        log_analysis = await production_monitoring.log_aggregator.collect_logs()
        
        print(f"✓ Log analysis completed successfully")
        print(f"  - Total logs: {log_analysis.get('total_logs', 0)}")
        print(f"  - Error count: {log_analysis.get('error_count', 0)}")
        print(f"  - Warning count: {log_analysis.get('warning_count', 0)}")
        print(f"  - Log sources: {list(log_analysis.get('log_sources', {}).keys())}")
        print(f"  - Pattern matches: {log_analysis.get('patterns', {})}")
        
        return True
        
    except Exception as e:
        print(f"✗ Log aggregation test failed: {e}")
        return False

async def test_incident_management():
    """Test incident management system"""
    print("\nTesting incident management...")
    
    try:
        # Create a test incident
        incident = await production_monitoring.incident_manager.create_incident(
            title="Test Incident",
            description="This is a test incident for monitoring system validation",
            severity=AlertSeverity.MEDIUM,
            affected_services=["test_service"]
        )
        
        print(f"✓ Test incident created: {incident.id}")
        
        # Update incident status
        success = await production_monitoring.incident_manager.update_incident_status(
            incident.id,
            IncidentStatus.INVESTIGATING,
            "Starting investigation of test incident",
            "test_user"
        )
        
        if success:
            print(f"✓ Incident status updated to investigating")
        else:
            print(f"✗ Failed to update incident status")
            return False
        
        # Get runbook
        runbook = production_monitoring.incident_manager.get_runbook("high_error_rate")
        if runbook:
            print(f"✓ Runbook retrieved: {runbook['title']}")
            print(f"  - Steps: {len(runbook['steps'])}")
            print(f"  - Escalation time: {runbook['escalation_time']} minutes")
        
        # Resolve incident
        success = await production_monitoring.incident_manager.update_incident_status(
            incident.id,
            IncidentStatus.RESOLVED,
            "Test incident resolved successfully",
            "test_user"
        )
        
        if success:
            print(f"✓ Test incident resolved")
        else:
            print(f"✗ Failed to resolve incident")
            return False
        
        # Get incident history
        history = production_monitoring.incident_manager.get_incident_history(1)
        print(f"✓ Incident history retrieved: {len(history)} incidents")
        
        return True
        
    except Exception as e:
        print(f"✗ Incident management test failed: {e}")
        return False

async def test_backup_monitoring():
    """Test backup monitoring system"""
    print("\nTesting backup monitoring...")
    
    try:
        # Check backup health
        health_status = await backup_monitoring.check_backup_health()
        
        print(f"✓ Backup health check completed")
        print(f"  - Overall status: {health_status.get('overall_status')}")
        print(f"  - Overdue jobs: {len(health_status.get('overdue_jobs', []))}")
        print(f"  - Failed jobs: {len(health_status.get('failed_jobs', []))}")
        print(f"  - Recent failures: {health_status.get('recent_failures', 0)}")
        print(f"  - Last successful backup: {health_status.get('last_successful_backup')}")
        
        # Get backup jobs
        backup_jobs = backup_monitoring.get_backup_jobs()
        print(f"✓ Backup jobs retrieved: {len(backup_jobs)} jobs")
        
        for job_id, job_data in backup_jobs.items():
            print(f"  - {job_id}: {job_data['status']} (next: {job_data['next_run']})")
        
        # Get backup history
        history = backup_monitoring.get_backup_history(24)
        print(f"✓ Backup history retrieved: {len(history)} entries")
        
        return True
        
    except Exception as e:
        print(f"✗ Backup monitoring test failed: {e}")
        return False

async def test_alerting_integration():
    """Test alerting system integration"""
    print("\nTesting alerting integration...")
    
    try:
        # Create test alert
        alert = await alerting_service.create_alert(
            AlertType.CUSTOM,
            AlertSeverity.LOW,
            "Test Alert",
            "This is a test alert for monitoring system validation",
            {"test": True, "component": "monitoring_test"}
        )
        
        print(f"✓ Test alert created: {alert.id}")
        
        # Get active alerts
        active_alerts = alerting_service.get_active_alerts()
        print(f"✓ Active alerts retrieved: {len(active_alerts)} alerts")
        
        # Get alert summary
        alert_summary = alerting_service.get_alert_summary()
        print(f"✓ Alert summary retrieved:")
        print(f"  - Active alerts: {alert_summary['active_alerts_count']}")
        print(f"  - Recent alerts: {alert_summary['recent_alerts_count']}")
        print(f"  - Severity breakdown: {alert_summary['severity_breakdown']}")
        
        # Resolve test alert
        success = await alerting_service.resolve_alert(alert.id)
        if success:
            print(f"✓ Test alert resolved")
        else:
            print(f"✗ Failed to resolve test alert")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Alerting integration test failed: {e}")
        return False

async def test_incident_detection():
    """Test automatic incident detection"""
    print("\nTesting incident detection...")
    
    try:
        # Trigger incident check
        await production_monitoring.check_for_incidents()
        print(f"✓ Incident detection check completed")
        
        # Check for any new incidents
        active_incidents = production_monitoring.incident_manager.get_active_incidents()
        print(f"✓ Active incidents after check: {len(active_incidents)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Incident detection test failed: {e}")
        return False

async def test_service_health():
    """Test service health monitoring"""
    print("\nTesting service health monitoring...")
    
    try:
        service_health = await production_monitoring._get_service_health()
        
        print(f"✓ Service health check completed")
        for service, status in service_health.items():
            print(f"  - {service}: {status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Service health test failed: {e}")
        return False

async def test_performance_metrics():
    """Test performance metrics collection"""
    print("\nTesting performance metrics...")
    
    try:
        performance_metrics = await production_monitoring._get_performance_metrics()
        
        print(f"✓ Performance metrics collected")
        if 'system' in performance_metrics:
            system = performance_metrics['system']
            print(f"  - CPU: {system.get('cpu_percent', 0):.1f}%")
            print(f"  - Memory: {system.get('memory_percent', 0):.1f}%")
            print(f"  - Disk: {system.get('disk_percent', 0):.1f}%")
        
        if 'api' in performance_metrics:
            api = performance_metrics['api']
            print(f"  - Avg response time: {api.get('avg_response_time', 0):.3f}s")
            print(f"  - Total requests: {api.get('total_requests', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance metrics test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive production monitoring test suite"""
    print("=" * 60)
    print("PRODUCTION MONITORING SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Production Dashboard", test_production_dashboard),
        ("Log Aggregation", test_log_aggregation),
        ("Incident Management", test_incident_management),
        ("Backup Monitoring", test_backup_monitoring),
        ("Alerting Integration", test_alerting_integration),
        ("Incident Detection", test_incident_detection),
        ("Service Health", test_service_health),
        ("Performance Metrics", test_performance_metrics),
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
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All production monitoring tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the output above.")
        return False

if __name__ == "__main__":
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)