import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import styles from './MonitoringDashboard.module.css';

const MonitoringDashboard = ({ isAdmin = false }) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [errorSummary, setErrorSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  useEffect(() => {
    fetchMonitoringData();
    
    // Set up auto-refresh
    const interval = setInterval(fetchMonitoringData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Fetch health status (public endpoint)
      const healthResponse = await fetch('/api/v1/monitoring/health', {
        headers: { 'Content-Type': 'application/json' }
      });
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setHealthStatus(healthData);
      }

      if (isAdmin) {
        // Fetch admin-only data
        const [statusResponse, performanceResponse, errorResponse, alertsResponse] = await Promise.allSettled([
          fetch('/api/v1/monitoring/status', { headers }),
          fetch('/api/v1/monitoring/performance', { headers }),
          fetch('/api/v1/monitoring/errors?hours=24', { headers }),
          fetch('/api/v1/monitoring/alerts', { headers })
        ]);

        if (statusResponse.status === 'fulfilled' && statusResponse.value.ok) {
          const statusData = await statusResponse.value.json();
          setSystemStatus(statusData);
        }

        if (performanceResponse.status === 'fulfilled' && performanceResponse.value.ok) {
          const perfData = await performanceResponse.value.json();
          setPerformanceMetrics(perfData.performance_metrics);
        }

        if (errorResponse.status === 'fulfilled' && errorResponse.value.ok) {
          const errorData = await errorResponse.value.json();
          setErrorSummary(errorData.error_summary);
        }

        if (alertsResponse.status === 'fulfilled' && alertsResponse.value.ok) {
          const alertsData = await alertsResponse.value.json();
          setAlerts(alertsData.alerts || []);
        }
      }

    } catch (err) {
      console.error('Error fetching monitoring data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#27ae60';
      case 'unhealthy': return '#e74c3c';
      case 'warning': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  const getAlertSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#e74c3c';
      case 'warning': return '#f39c12';
      case 'info': return '#3498db';
      default: return '#95a5a6';
    }
  };

  if (loading && !systemStatus && !healthStatus) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Loading monitoring data...</p>
      </div>
    );
  }

  if (error && !healthStatus) {
    return (
      <div className={styles.error}>
        <h3>Error Loading Monitoring Data</h3>
        <p>{error}</p>
        <button onClick={fetchMonitoringData} className={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h2>System Monitoring Dashboard</h2>
        <div className={styles.controls}>
          <select 
            value={refreshInterval} 
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className={styles.refreshSelect}
          >
            <option value={10}>Refresh every 10s</option>
            <option value={30}>Refresh every 30s</option>
            <option value={60}>Refresh every 1min</option>
            <option value={300}>Refresh every 5min</option>
          </select>
          <button onClick={fetchMonitoringData} className={styles.refreshButton}>
            Refresh Now
          </button>
        </div>
      </div>

      {/* Health Status Cards */}
      <div className={styles.healthCards}>
        <div className={styles.card}>
          <h3>Overall Health</h3>
          <div 
            className={styles.healthStatus}
            style={{ color: getStatusColor(healthStatus?.overall_status) }}
          >
            {healthStatus?.overall_status || 'Unknown'}
          </div>
        </div>

        {healthStatus?.checks && (
          <>
            <div className={styles.card}>
              <h3>Database</h3>
              <div 
                className={styles.healthStatus}
                style={{ color: getStatusColor(healthStatus.checks.database?.status) }}
              >
                {healthStatus.checks.database?.status || 'Unknown'}
              </div>
              {healthStatus.checks.database?.response_time && (
                <div className={styles.metric}>
                  {(healthStatus.checks.database.response_time * 1000).toFixed(1)}ms
                </div>
              )}
            </div>

            <div className={styles.card}>
              <h3>System Resources</h3>
              <div 
                className={styles.healthStatus}
                style={{ color: getStatusColor(healthStatus.checks.system_resources?.status) }}
              >
                {healthStatus.checks.system_resources?.status || 'Unknown'}
              </div>
              {healthStatus.checks.system_resources?.cpu_percent && (
                <div className={styles.metric}>
                  CPU: {healthStatus.checks.system_resources.cpu_percent.toFixed(1)}%
                </div>
              )}
            </div>

            <div className={styles.card}>
              <h3>AI Services</h3>
              <div 
                className={styles.healthStatus}
                style={{ color: getStatusColor(healthStatus.checks.ai_services?.status) }}
              >
                {healthStatus.checks.ai_services?.status || 'Unknown'}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className={styles.alertsSection}>
          <h3>System Alerts</h3>
          <div className={styles.alerts}>
            {alerts.map((alert, index) => (
              <div 
                key={index} 
                className={styles.alert}
                style={{ borderLeftColor: getAlertSeverityColor(alert.severity) }}
              >
                <div className={styles.alertHeader}>
                  <span className={styles.alertType}>{alert.type}</span>
                  <span 
                    className={styles.alertSeverity}
                    style={{ color: getAlertSeverityColor(alert.severity) }}
                  >
                    {alert.severity}
                  </span>
                </div>
                <div className={styles.alertMessage}>{alert.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Admin-only sections */}
      {isAdmin && (
        <>
          {/* System Metrics */}
          {systemStatus && (
            <div className={styles.metricsSection}>
              <h3>System Metrics</h3>
              <div className={styles.metricsGrid}>
                <div className={styles.metricCard}>
                  <h4>Uptime</h4>
                  <div className={styles.metricValue}>
                    {(systemStatus.uptime_seconds / 3600).toFixed(1)}h
                  </div>
                </div>
                <div className={styles.metricCard}>
                  <h4>Total Errors (24h)</h4>
                  <div className={styles.metricValue}>
                    {systemStatus.errors?.total_errors || 0}
                  </div>
                </div>
                <div className={styles.metricCard}>
                  <h4>Error Rate</h4>
                  <div className={styles.metricValue}>
                    {systemStatus.errors?.error_rate?.toFixed(1) || 0}/hr
                  </div>
                </div>
                <div className={styles.metricCard}>
                  <h4>Monitored Endpoints</h4>
                  <div className={styles.metricValue}>
                    {Object.keys(systemStatus.performance || {}).length}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {performanceMetrics && Object.keys(performanceMetrics).length > 0 && (
            <div className={styles.performanceSection}>
              <h3>API Performance</h3>
              <div className={styles.performanceTable}>
                <table>
                  <thead>
                    <tr>
                      <th>Endpoint</th>
                      <th>Avg Response Time</th>
                      <th>Requests</th>
                      <th>Error Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(performanceMetrics).map(([endpoint, stats]) => (
                      <tr key={endpoint}>
                        <td className={styles.endpoint}>{endpoint}</td>
                        <td>{(stats.avg_response_time * 1000).toFixed(1)}ms</td>
                        <td>{stats.request_count}</td>
                        <td style={{ color: stats.error_rate > 0.1 ? '#e74c3c' : '#27ae60' }}>
                          {(stats.error_rate * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Error Summary */}
          {errorSummary && (
            <div className={styles.errorSection}>
              <h3>Error Summary (24h)</h3>
              <div className={styles.errorStats}>
                <div className={styles.errorStat}>
                  <span>Total Errors:</span>
                  <span>{errorSummary.total_errors}</span>
                </div>
                <div className={styles.errorStat}>
                  <span>Error Rate:</span>
                  <span>{errorSummary.error_rate.toFixed(1)} errors/hour</span>
                </div>
                <div className={styles.errorStat}>
                  <span>Most Common:</span>
                  <span>{errorSummary.most_common_error || 'None'}</span>
                </div>
              </div>
              
              {errorSummary.error_types && Object.keys(errorSummary.error_types).length > 0 && (
                <div className={styles.errorTypes}>
                  <h4>Error Types</h4>
                  {Object.entries(errorSummary.error_types).map(([type, count]) => (
                    <div key={type} className={styles.errorType}>
                      <span>{type}</span>
                      <span>{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* System Resources Detail */}
      {healthStatus?.checks?.system_resources?.status === 'healthy' && (
        <div className={styles.resourcesSection}>
          <h3>System Resources</h3>
          <div className={styles.resourcesGrid}>
            <div className={styles.resourceCard}>
              <h4>CPU Usage</h4>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ 
                    width: `${healthStatus.checks.system_resources.cpu_percent}%`,
                    backgroundColor: healthStatus.checks.system_resources.cpu_percent > 80 ? '#e74c3c' : '#27ae60'
                  }}
                ></div>
              </div>
              <div className={styles.resourceValue}>
                {healthStatus.checks.system_resources.cpu_percent.toFixed(1)}%
              </div>
            </div>

            <div className={styles.resourceCard}>
              <h4>Memory Usage</h4>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ 
                    width: `${healthStatus.checks.system_resources.memory.percent}%`,
                    backgroundColor: healthStatus.checks.system_resources.memory.percent > 85 ? '#e74c3c' : '#27ae60'
                  }}
                ></div>
              </div>
              <div className={styles.resourceValue}>
                {healthStatus.checks.system_resources.memory.percent.toFixed(1)}%
              </div>
            </div>

            <div className={styles.resourceCard}>
              <h4>Disk Usage</h4>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ 
                    width: `${healthStatus.checks.system_resources.disk.percent}%`,
                    backgroundColor: healthStatus.checks.system_resources.disk.percent > 90 ? '#e74c3c' : '#27ae60'
                  }}
                ></div>
              </div>
              <div className={styles.resourceValue}>
                {healthStatus.checks.system_resources.disk.percent.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {!isAdmin && (
        <div className={styles.adminNote}>
          <p>Additional monitoring features are available for administrators.</p>
        </div>
      )}
    </div>
  );
};

export default MonitoringDashboard;