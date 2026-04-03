#!/usr/bin/env python3
"""
Health check script for the Ponder backend service.
This script is used by Docker health checks and monitoring systems.
"""

import sys
import requests
import json
from typing import Dict, Any

def check_health() -> Dict[str, Any]:
    """
    Perform comprehensive health check of the backend service.
    
    Returns:
        Dict containing health status and details
    """
    try:
        # Check main health endpoint
        response = requests.get(
            "http://localhost:8000/api/v1/health",
            timeout=10
        )
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Check if all critical services are healthy
            critical_services = ['database', 'redis', 'ai_service']
            all_healthy = all(
                health_data.get('services', {}).get(service, {}).get('status') == 'healthy'
                for service in critical_services
            )
            
            return {
                'status': 'healthy' if all_healthy else 'degraded',
                'details': health_data,
                'timestamp': health_data.get('timestamp'),
                'version': health_data.get('version')
            }
        else:
            return {
                'status': 'unhealthy',
                'error': f'Health endpoint returned {response.status_code}',
                'details': response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'status': 'unhealthy',
            'error': f'Failed to connect to health endpoint: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error during health check: {str(e)}'
        }

def main():
    """Main function for health check script."""
    health_status = check_health()
    
    # Print health status as JSON
    print(json.dumps(health_status, indent=2))
    
    # Exit with appropriate code
    if health_status['status'] == 'healthy':
        sys.exit(0)
    elif health_status['status'] == 'degraded':
        sys.exit(1)  # Warning status
    else:
        sys.exit(2)  # Critical status

if __name__ == "__main__":
    main()