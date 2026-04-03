import axios from 'axios';
import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

/**
 * Fetch the user's skill map data from the backend.
 * Falls back to deriving skills from projects if the API is not yet available.
 */
export const getUserSkillMap = async (userId, token) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/skill-map`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  } catch (error) {
    // API not yet available — return null so the component can derive from projects
    return null;
  }
};
