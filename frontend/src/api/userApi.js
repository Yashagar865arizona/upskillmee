import config from '../config';

class UserAPI {
  constructor(authContext) {
    this.authContext = authContext;
  }

  async makeRequest(url, options = {}) {
    const { makeAuthenticatedRequest } = this.authContext;
    return makeAuthenticatedRequest(url, options);
  }

  async getProfile() {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/profile`);
    if (!response.ok) {
      throw new Error('Failed to fetch profile');
    }
    return response.json();
  }

  async updateProfile(profileData) {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update profile');
    }
    return response.json();
  }

  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/avatar`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to upload avatar');
    }
    return response.json();
  }

  async getSettings() {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/settings`);
    if (!response.ok) {
      throw new Error('Failed to fetch settings');
    }
    return response.json();
  }

  async updateSettings(settingsData) {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settingsData)
    });

    if (!response.ok) {
      throw new Error('Failed to update settings');
    }
    return response.json();
  }

  async exportData() {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me/export`);
    if (!response.ok) {
      throw new Error('Failed to export data');
    }
    return response.json();
  }

  async deleteAccount() {
    const response = await this.makeRequest(`${config.API_BASE_URL}/users/me`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete account');
    }
    return response.json();
  }
}

export default UserAPI;