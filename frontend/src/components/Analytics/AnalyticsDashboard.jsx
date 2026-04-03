import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { analyticsService } from '../../api/analyticsApi';
import styles from './AnalyticsDashboard.module.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AnalyticsDashboard = ({ userId, isAdmin = false }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    fetchAnalyticsData();
  }, [userId, timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      if (isAdmin) {
        data = await analyticsService.getAnalyticsDashboard(timeRange);
      } else {
        data = await analyticsService.getUserDashboard(userId);
      }
      
      setAnalyticsData(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const trackEvent = async (eventType, metadata = {}) => {
    try {
      await analyticsService.trackEvent(eventType, metadata);
      // Refresh analytics data after tracking event
      setTimeout(() => {
        fetchAnalyticsData();
      }, 1000);
    } catch (err) {
      console.error('Error tracking event:', err);
    }
  };

  const generateSessionId = () => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('session_id', sessionId);
    return sessionId;
  };

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h3>Error Loading Analytics</h3>
        <p>{error}</p>
        <button onClick={fetchAnalyticsData} className={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className={styles.noData}>
        <h3>No Analytics Data Available</h3>
        <p>Start using the platform to see your analytics.</p>
      </div>
    );
  }

  // Prepare chart data
  const engagementChartData = {
    labels: ['Messages', 'Sessions', 'Active Days', 'Projects'],
    datasets: [
      {
        label: 'Engagement Metrics',
        data: [
          analyticsData.engagement?.engagement_metrics?.messages_per_day || 0,
          analyticsData.engagement?.session_analysis?.total_sessions || 0,
          analyticsData.engagement?.engagement_metrics?.active_days_streak || 0,
          analyticsData.learning?.completed_projects || 0,
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 99, 132, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const learningProgressData = {
    labels: Object.keys(analyticsData.learning?.skill_progress || {}),
    datasets: [
      {
        label: 'Skill Progress (%)',
        data: Object.values(analyticsData.learning?.skill_progress || {}),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
        fill: true,
      },
    ],
  };

  const funnelData = isAdmin && analyticsData.funnel ? {
    labels: analyticsData.funnel.map(stage => stage.stage),
    datasets: [
      {
        label: 'Users',
        data: analyticsData.funnel.map(stage => stage.users_completed),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1,
      },
    ],
  } : null;

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h2>{isAdmin ? 'System Analytics Dashboard' : 'Your Learning Analytics'}</h2>
        <div className={styles.controls}>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className={styles.timeRangeSelect}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button onClick={fetchAnalyticsData} className={styles.refreshButton}>
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className={styles.summaryCards}>
        {isAdmin ? (
          <>
            <div className={styles.card}>
              <h3>Total Users</h3>
              <div className={styles.metric}>{analyticsData.summary?.total_users || 0}</div>
            </div>
            <div className={styles.card}>
              <h3>Active Users (7d)</h3>
              <div className={styles.metric}>{analyticsData.summary?.active_users_7d || 0}</div>
            </div>
            <div className={styles.card}>
              <h3>Total Events</h3>
              <div className={styles.metric}>{analyticsData.summary?.total_events || 0}</div>
            </div>
            <div className={styles.card}>
              <h3>Avg Events/User</h3>
              <div className={styles.metric}>
                {analyticsData.summary?.avg_events_per_user?.toFixed(1) || 0}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className={styles.card}>
              <h3>Messages Sent</h3>
              <div className={styles.metric}>
                {analyticsData.engagement?.total_events || 0}
              </div>
            </div>
            <div className={styles.card}>
              <h3>Active Days</h3>
              <div className={styles.metric}>
                {analyticsData.engagement?.engagement_metrics?.active_days_streak || 0}
              </div>
            </div>
            <div className={styles.card}>
              <h3>Projects Completed</h3>
              <div className={styles.metric}>
                {analyticsData.learning?.completed_projects || 0}
              </div>
            </div>
            <div className={styles.card}>
              <h3>Learning Pace</h3>
              <div className={styles.metric}>
                {analyticsData.learning?.learning_pace?.toFixed(1) || 0}x
              </div>
            </div>
          </>
        )}
      </div>

      {/* Charts */}
      <div className={styles.chartsGrid}>
        {/* Engagement Chart */}
        <div className={styles.chartContainer}>
          <h3>Engagement Overview</h3>
          <Bar 
            data={engagementChartData}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top',
                },
                title: {
                  display: true,
                  text: 'User Engagement Metrics',
                },
              },
            }}
          />
        </div>

        {/* Learning Progress Chart */}
        {Object.keys(analyticsData.learning?.skill_progress || {}).length > 0 && (
          <div className={styles.chartContainer}>
            <h3>Learning Progress</h3>
            <Line 
              data={learningProgressData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  title: {
                    display: true,
                    text: 'Skill Development Progress',
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                  },
                },
              }}
            />
          </div>
        )}

        {/* Conversion Funnel (Admin only) */}
        {isAdmin && funnelData && (
          <div className={styles.chartContainer}>
            <h3>Conversion Funnel</h3>
            <Bar 
              data={funnelData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  title: {
                    display: true,
                    text: 'User Conversion Funnel',
                  },
                },
              }}
            />
          </div>
        )}
      </div>

      {/* Detailed Metrics */}
      <div className={styles.detailedMetrics}>
        <div className={styles.metricsSection}>
          <h3>Engagement Details</h3>
          <div className={styles.metricsList}>
            <div className={styles.metricItem}>
              <span>Messages per Day:</span>
              <span>{analyticsData.engagement?.engagement_metrics?.messages_per_day?.toFixed(1) || 0}</span>
            </div>
            <div className={styles.metricItem}>
              <span>Avg Response Time:</span>
              <span>{analyticsData.engagement?.engagement_metrics?.response_time_avg?.toFixed(1) || 0}s</span>
            </div>
            <div className={styles.metricItem}>
              <span>Session Duration:</span>
              <span>{analyticsData.engagement?.engagement_metrics?.session_duration_avg?.toFixed(1) || 0} min</span>
            </div>
            <div className={styles.metricItem}>
              <span>Project Completion Rate:</span>
              <span>{(analyticsData.engagement?.engagement_metrics?.project_completion_rate * 100)?.toFixed(1) || 0}%</span>
            </div>
          </div>
        </div>

        {!isAdmin && (
          <div className={styles.metricsSection}>
            <h3>Learning Insights</h3>
            <div className={styles.metricsList}>
              <div className={styles.metricItem}>
                <span>Active Projects:</span>
                <span>{analyticsData.learning?.active_projects || 0}</span>
              </div>
              <div className={styles.metricItem}>
                <span>Milestone Completion:</span>
                <span>{(analyticsData.learning?.milestone_completion_rate * 100)?.toFixed(1) || 0}%</span>
              </div>
              <div className={styles.metricItem}>
                <span>Last Activity:</span>
                <span>
                  {analyticsData.engagement?.last_activity 
                    ? new Date(analyticsData.engagement.last_activity).toLocaleDateString()
                    : 'N/A'
                  }
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Event Tracking Demo */}
      <div className={styles.eventTracking}>
        <h3>Event Tracking Demo</h3>
        <div className={styles.eventButtons}>
          <button 
            onClick={() => trackEvent('USER_LOGIN')}
            className={styles.eventButton}
          >
            Track Login
          </button>
          <button 
            onClick={() => trackEvent('PROFILE_UPDATED')}
            className={styles.eventButton}
          >
            Track Profile Update
          </button>
          <button 
            onClick={() => trackEvent('PROJECT_CREATED', { project_type: 'demo' })}
            className={styles.eventButton}
          >
            Track Project Creation
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;