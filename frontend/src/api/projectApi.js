import axios from 'axios';
import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

// Get user's projects
export const getUserProjects = async (userId, token) => {
  try {
    console.log(`Fetching projects for user ${userId}`);
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/projects`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('User projects raw response:', response.data);

    // Explicitly log each project's ID
    if (Array.isArray(response.data)) {
      response.data.forEach((proj, idx) => {
        console.log(`Project ${idx + 1} ID:`, proj.id || proj.projectId,"--------------------------------------------------------------");
      });
    }

    return response.data;
  } catch (error) {
    console.error('Error fetching user projects:', error);
    return [];
  }
};


// Create a new project from learning plan
export const createProjectFromPlan = async (planData, userId, token) => {
  try {
    console.log('Creating project from learning plan:', planData);
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/projects`, {
      title: planData.title,
      description: planData.description,
      domain: planData.domain || 'general',
      difficulty: planData.difficulty || 'beginner',
      status: 'accepted',
      steps: planData.projects || [],
      project_metadata: {
        learning_plan_data: planData,
        created_from: 'learning_plan'
      }
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('Project created:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating project:', error);
    throw error;
  }
};

// Update project status (accept/reject)
export const updateProjectStatus = async (projectId, status, userId, token) => {
  try {
    console.log(`Updating project ${projectId} status to ${status}`);
    const response = await axios.put(`${API_BASE_URL}/users/${userId}/projects/${projectId}`, {
      status: status
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('Project status updated:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating project status:', error);
    throw error;
  }
};

// Update project progress
export const updateProjectProgress = async (projectId, progressData, userId, token) => {
  try {
    console.log(`Updating project ${projectId} progress:`, progressData);
    const response = await axios.put(`${API_BASE_URL}/users/${userId}/projects/${projectId}/progress`, progressData, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('Project progress updated:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating project progress:', error);
    throw error;
  }
};

// Run project assessment
export const assessProject = async (projectId, token) => {
  const response = await axios.post(
    `${API_BASE_URL}/projects/${projectId}/assess`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

// Fetch existing project assessment
export const getProjectAssessment = async (projectId, token) => {
  const response = await axios.get(
    `${API_BASE_URL}/projects/${projectId}/assessment`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

// Get learning plans for a user
export const getUserLearningPlans = async (userId, token) => {
  try {
    console.log(`Fetching learning plans for user ${userId}`);
    const response = await axios.get(`${API_BASE_URL}/learning/plans/${userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    console.log('Learning plans response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching learning plans:', error);
    return [];
  }
};