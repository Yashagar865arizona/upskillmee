import { apiRequest } from './apiUtils';

const FEEDBACK_BASE_URL = '/api/v1/feedback';

// Feedback submission
export const submitFeedback = async (feedbackData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/submit`, {
    method: 'POST',
    body: JSON.stringify(feedbackData),
  });
};

export const getMyFeedback = async (limit = 50) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/my-feedback?limit=${limit}`);
};

export const getFeedbackAnalytics = async (days = 30) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/analytics?days=${days}`);
};

// Support tickets
export const createSupportTicket = async (ticketData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/support/tickets`, {
    method: 'POST',
    body: JSON.stringify(ticketData),
  });
};

export const getMySupportTickets = async (limit = 50) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/support/tickets?limit=${limit}`);
};

export const addTicketMessage = async (ticketId, messageData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/support/tickets/${ticketId}/messages`, {
    method: 'POST',
    body: JSON.stringify(messageData),
  });
};

export const getTicketMessages = async (ticketId) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/support/tickets/${ticketId}/messages`);
};

// Feature usage tracking
export const trackFeatureUsage = async (usageData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/usage/track`, {
    method: 'POST',
    body: JSON.stringify(usageData),
  });
};

export const getFeatureUsageAnalytics = async (featureName = null, days = 30) => {
  const params = new URLSearchParams({ days: days.toString() });
  if (featureName) {
    params.append('feature_name', featureName);
  }
  return apiRequest(`${FEEDBACK_BASE_URL}/usage/analytics?${params}`);
};

// Onboarding analytics
export const startOnboardingStep = async (stepData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/onboarding/start-step`, {
    method: 'POST',
    body: JSON.stringify(stepData),
  });
};

export const completeOnboardingStep = async (stepData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/onboarding/complete-step`, {
    method: 'POST',
    body: JSON.stringify(stepData),
  });
};

export const getOnboardingProgress = async () => {
  return apiRequest(`${FEEDBACK_BASE_URL}/onboarding/progress`);
};

export const getOnboardingAnalytics = async (days = 30) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/onboarding/analytics?days=${days}`);
};

// A/B testing
export const getABTestAssignment = async (featureFlag) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/ab-tests/assignment/${featureFlag}`);
};

export const trackABTestConversion = async (conversionData) => {
  return apiRequest(`${FEEDBACK_BASE_URL}/ab-tests/conversion`, {
    method: 'POST',
    body: JSON.stringify(conversionData),
  });
};

export const getMyABTestExperiments = async () => {
  return apiRequest(`${FEEDBACK_BASE_URL}/ab-tests/my-experiments`);
};

// Utility functions for easier usage
export const useFeatureTracking = () => {
  const trackFeature = async (featureName, action, metadata = {}) => {
    try {
      await trackFeatureUsage({
        feature_name: featureName,
        action: action,
        metadata: metadata,
        session_id: getSessionId(),
        page_url: window.location.href,
        user_agent: navigator.userAgent
      });
    } catch (error) {
      console.warn('Failed to track feature usage:', error);
    }
  };

  return { trackFeature };
};

export const useOnboardingTracking = () => {
  const startStep = async (stepName, metadata = {}) => {
    try {
      await startOnboardingStep({
        step_name: stepName,
        metadata: metadata
      });
    } catch (error) {
      console.warn('Failed to start onboarding step:', error);
    }
  };

  const completeStep = async (stepName, metadata = {}) => {
    try {
      await completeOnboardingStep({
        step_name: stepName,
        metadata: metadata
      });
    } catch (error) {
      console.warn('Failed to complete onboarding step:', error);
    }
  };

  return { startStep, completeStep };
};

export const useABTesting = () => {
  const getVariant = async (featureFlag) => {
    try {
      const response = await getABTestAssignment(featureFlag);
      return response.variant || 'control';
    } catch (error) {
      console.warn('Failed to get A/B test variant:', error);
      return 'control';
    }
  };

  const trackConversion = async (experimentId, eventName, eventData = {}) => {
    try {
      await trackABTestConversion({
        experiment_id: experimentId,
        event_name: eventName,
        event_data: eventData
      });
    } catch (error) {
      console.warn('Failed to track A/B test conversion:', error);
    }
  };

  return { getVariant, trackConversion };
};

// Helper function to get or create session ID
const getSessionId = () => {
  let sessionId = sessionStorage.getItem('ponder_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('ponder_session_id', sessionId);
  }
  return sessionId;
};

// Auto-track page views
export const trackPageView = (pageName) => {
  const { trackFeature } = useFeatureTracking();
  trackFeature('page_navigation', 'page_view', {
    page_name: pageName,
    referrer: document.referrer,
    timestamp: new Date().toISOString()
  });
};

// Auto-track clicks
export const trackClick = (elementName, elementType = 'button') => {
  const { trackFeature } = useFeatureTracking();
  trackFeature('user_interaction', 'click', {
    element_name: elementName,
    element_type: elementType,
    timestamp: new Date().toISOString()
  });
};