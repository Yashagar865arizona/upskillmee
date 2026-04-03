import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const analyticsApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/analytics`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
analyticsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
analyticsApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Analytics API Error:', error);
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const analyticsService = {
  // Event tracking
  trackEvent: async (eventType, metadata = {}, sessionId = null) => {
    try {
      const response = await analyticsApi.post('/events', {
        event_type: eventType,
        metadata,
        session_id: sessionId || getSessionId(),
      });
      return response.data;
    } catch (error) {
      console.error('Error tracking event:', error);
      throw error;
    }
  },

  // User engagement metrics
  getUserEngagement: async (userId, days = 30) => {
    try {
      const response = await analyticsApi.get(`/engagement/${userId}?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user engagement:', error);
      throw error;
    }
  },

  getEngagementSummary: async (userId, days = 30) => {
    try {
      const response = await analyticsApi.get(`/engagement/summary/${userId}?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching engagement summary:', error);
      throw error;
    }
  },

  // Learning analytics
  getLearningAnalytics: async (userId) => {
    try {
      const response = await analyticsApi.get(`/learning/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching learning analytics:', error);
      throw error;
    }
  },

  getLearningProgress: async (userId) => {
    try {
      const response = await analyticsApi.get(`/progress/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching learning progress:', error);
      throw error;
    }
  },

  // Conversion funnel
  getConversionFunnel: async (days = 30) => {
    try {
      const response = await analyticsApi.get(`/funnel?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching conversion funnel:', error);
      throw error;
    }
  },

  getUserFunnelProgress: async (userId) => {
    try {
      const response = await analyticsApi.get(`/funnel/user/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user funnel progress:', error);
      throw error;
    }
  },

  // Dashboard data
  getAnalyticsDashboard: async (days = 30) => {
    try {
      const response = await analyticsApi.get(`/dashboard?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching analytics dashboard:', error);
      throw error;
    }
  },

  getUserDashboard: async (userId) => {
    try {
      const response = await analyticsApi.get(`/dashboard/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user dashboard:', error);
      throw error;
    }
  },

  // System metrics
  getEngagementMetrics: async (days = 30) => {
    try {
      const response = await analyticsApi.get(`/metrics/engagement?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching engagement metrics:', error);
      throw error;
    }
  },

  getLearningMetrics: async (days = 30) => {
    try {
      const response = await analyticsApi.get(`/metrics/learning?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching learning metrics:', error);
      throw error;
    }
  },

  getSystemMetrics: async () => {
    try {
      const response = await analyticsApi.get('/metrics/system');
      return response.data;
    } catch (error) {
      console.error('Error fetching system metrics:', error);
      throw error;
    }
  },
};

// Helper functions
function getSessionId() {
  let sessionId = sessionStorage.getItem('analytics_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('analytics_session_id', sessionId);
  }
  return sessionId;
}

// Auto-track page views
export const trackPageView = (pageName, metadata = {}) => {
  analyticsService.trackEvent('PAGE_VIEW', {
    page: pageName,
    timestamp: new Date().toISOString(),
    ...metadata,
  }).catch(error => {
    console.error('Failed to track page view:', error);
  });
};

// Auto-track user actions
export const trackUserAction = (action, metadata = {}) => {
  analyticsService.trackEvent('USER_ACTION', {
    action,
    timestamp: new Date().toISOString(),
    ...metadata,
  }).catch(error => {
    console.error('Failed to track user action:', error);
  });
};

// Session management
export const startSession = () => {
  const sessionId = getSessionId();
  analyticsService.trackEvent('SESSION_STARTED', {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
  }).catch(error => {
    console.error('Failed to track session start:', error);
  });
  return sessionId;
};

export const endSession = () => {
  const sessionId = getSessionId();
  analyticsService.trackEvent('SESSION_ENDED', {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
  }).catch(error => {
    console.error('Failed to track session end:', error);
  });
  sessionStorage.removeItem('analytics_session_id');
};

export default analyticsService;