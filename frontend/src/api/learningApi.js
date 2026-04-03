import axios from 'axios';
import config from '../config';

const API_BASE_URL = config.API_BASE_URL;


export const getLearningPlans = async (userId) => {
  try {
    console.log(`Fetching learning plans for user ${userId}`);
    const response = await axios.get(`${API_BASE_URL}/learning/plans/${userId}`);
    console.log('Learning plans raw response::::::::::::::::::::::::::::::', response.data);

  // Check nested projects
    if (Array.isArray(response.data)) {
      response.data.forEach((plan, idx) => {
        console.log(`Plan ${idx + 1} ID:`, plan.id);
        if (plan.content?.projects) {
          if (Array.isArray(plan.content.projects)) {
            plan.content.projects.forEach((proj, pidx) => {
              console.log(`  Project ${pidx + 1} ID:`, proj.id || proj.projectId,"---------------------------------------------------------------");
            });
          } else {
            console.log('  Single project ID:', plan.content.projects.id || plan.content.projects.projectId);
          }
        }
      });
    }

    return response.data;
  } catch (error) {
    console.error('Error fetching learning plans:', error);
    return [];
  }
};


export const saveLearningPlan = async (plan, userId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/learning/plans`, {
      plan,
      user_id: userId
    });
    console.log(")))))))))))))))))))))))))))",response)
    return response.data.plan;
  } catch (error) {
    console.error('Error saving learning plan:', error);
    throw error;
  }
};

export const submitPlanFeedback = async (planId, isPositive, userId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/learning/feedback`, {
      plan_id: planId,
      is_positive: isPositive,
      user_id: userId
    });
    return response.data.success;
  } catch (error) {
    console.error('Error submitting plan feedback:', error);
    throw error;
  }
};

export const taskCompletion = async (taskId, completed, token) => {
  console.log("Completing task:", taskId, "completed:", completed);
  try {
    const response = await axios.post(
      `${API_BASE_URL}/learning/tasks/${taskId}/toggle-completion`,
      completed,
      { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } }
    );
    
    console.log("Task completion response:", response.data);
    return response.data.completed; 
  } catch (error) {
    console.error('Error completing task:', error);
    throw error;
  }
}


