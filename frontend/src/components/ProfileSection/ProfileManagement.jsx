import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import UserAPI from '../../api/userApi';
import styles from './ProfileManagement.module.css';

export const ProfileManagement = () => {
  const authContext = useAuth();
  const { user } = authContext;
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    bio: '',
    location: '',
    learning_level: 'beginner',
    career_interests: [],
    technical_skills: [],
    soft_skills: [],
    long_term_goals: [],
    preferences: {}
  });

  const userAPI = new UserAPI(authContext);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const profileData = await userAPI.getProfile();
      setProfile(profileData);
      setFormData({
        name: profileData.name || '',
        email: profileData.email || '',
        bio: profileData.bio || '',
        location: profileData.location || '',
        learning_level: profileData.learning_level || 'beginner',
        career_interests: profileData.career_interests || [],
        technical_skills: profileData.technical_skills || [],
        soft_skills: profileData.soft_skills || [],
        long_term_goals: profileData.long_term_goals || [],
        preferences: profileData.preferences || {}
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayInputChange = (field, value) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item);
    setFormData(prev => ({
      ...prev,
      [field]: items
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const result = await userAPI.updateProfile(formData);
      setProfile(result.profile);
      alert('Profile updated successfully!');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Error updating profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const result = await userAPI.uploadAvatar(file);
      alert('Profile picture updated successfully!');
      fetchProfile(); // Refresh profile data
    } catch (error) {
      console.error('Error uploading avatar:', error);
      alert('Error uploading profile picture. Please try again.');
    }
  };

  const exportData = async () => {
    try {
      const data = await userAPI.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `upskillmee-user-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Error exporting data. Please try again.');
    }
  };

  const deleteAccount = async () => {
    if (!window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      return;
    }

    try {
      await userAPI.deleteAccount();
      alert('Account deleted successfully.');
      // Logout user after account deletion
      authContext.logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Error deleting account. Please try again.');
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading profile...</div>;
  }

  return (
    <div className={styles.profileManagement}>
      <div className={styles.header}>
        <h2>Profile Management</h2>
        <div className={styles.avatarSection}>
          <div className={styles.avatarContainer}>
            <img 
              src={profile?.avatar_url || "https://via.placeholder.com/80x80"} 
              alt="Profile Avatar"
              className={styles.avatar}
            />
            <label className={styles.avatarUpload}>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleAvatarUpload}
                style={{ display: 'none' }}
              />
              Change Photo
            </label>
          </div>
        </div>
      </div>

      <div className={styles.tabs}>
        <button 
          className={`${styles.tab} ${activeTab === 'basic' ? styles.active : ''}`}
          onClick={() => setActiveTab('basic')}
        >
          Basic Info
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'learning' ? styles.active : ''}`}
          onClick={() => setActiveTab('learning')}
        >
          Learning Profile
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'skills' ? styles.active : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          Skills & Goals
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'privacy' ? styles.active : ''}`}
          onClick={() => setActiveTab('privacy')}
        >
          Privacy & Data
        </button>
      </div>

      <div className={styles.tabContent}>
        {activeTab === 'basic' && (
          <div className={styles.section}>
            <h3>Basic Information</h3>
            <div className={styles.formGroup}>
              <label>Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className={styles.input}
                placeholder="City, Country"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Bio</label>
              <textarea
                value={formData.bio}
                onChange={(e) => handleInputChange('bio', e.target.value)}
                className={styles.textarea}
                placeholder="Tell us about yourself..."
                rows={4}
              />
            </div>
          </div>
        )}

        {activeTab === 'learning' && (
          <div className={styles.section}>
            <h3>Learning Profile</h3>
            <div className={styles.formGroup}>
              <label>Learning Level</label>
              <select
                value={formData.learning_level}
                onChange={(e) => handleInputChange('learning_level', e.target.value)}
                className={styles.select}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label>Career Interests</label>
              <input
                type="text"
                value={formData.career_interests.join(', ')}
                onChange={(e) => handleArrayInputChange('career_interests', e.target.value)}
                className={styles.input}
                placeholder="Web Development, Data Science, AI (comma-separated)"
              />
            </div>
          </div>
        )}

        {activeTab === 'skills' && (
          <div className={styles.section}>
            <h3>Skills & Goals</h3>
            <div className={styles.formGroup}>
              <label>Technical Skills</label>
              <input
                type="text"
                value={formData.technical_skills.join(', ')}
                onChange={(e) => handleArrayInputChange('technical_skills', e.target.value)}
                className={styles.input}
                placeholder="JavaScript, Python, React (comma-separated)"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Soft Skills</label>
              <input
                type="text"
                value={formData.soft_skills.join(', ')}
                onChange={(e) => handleArrayInputChange('soft_skills', e.target.value)}
                className={styles.input}
                placeholder="Communication, Leadership, Problem Solving (comma-separated)"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Long-term Goals</label>
              <input
                type="text"
                value={formData.long_term_goals.join(', ')}
                onChange={(e) => handleArrayInputChange('long_term_goals', e.target.value)}
                className={styles.input}
                placeholder="Become a Full-stack Developer, Start a Tech Company (comma-separated)"
              />
            </div>
          </div>
        )}

        {activeTab === 'privacy' && (
          <div className={styles.section}>
            <h3>Privacy & Data Management</h3>
            <div className={styles.privacyActions}>
              <div className={styles.actionItem}>
                <h4>Export Your Data</h4>
                <p>Download all your data in JSON format for your records.</p>
                <button onClick={exportData} className={styles.exportButton}>
                  Export Data
                </button>
              </div>
              <div className={styles.actionItem}>
                <h4>Delete Account</h4>
                <p>Permanently delete your account and all associated data.</p>
                <button onClick={deleteAccount} className={styles.deleteButton}>
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <button 
          onClick={handleSave} 
          disabled={saving}
          className={styles.saveButton}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
};