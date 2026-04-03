import React, { useState } from 'react';
import styles from './ProfileSection.module.css';
import { useAuth } from '../../context/AuthContext';
import { ProfileManagement } from './ProfileManagement';

export const ProfileSection = () => {
  const { user } = useAuth();
  const [showManagement, setShowManagement] = useState(false);
  
  // Default avatar if user hasn't uploaded one
  const defaultAvatar = "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/8e5ea8a29c7b4d1b9b5b4342ebb1ba7d?apiKey=6d52bc9029684ea6804919348d39f130&";
  
  if (showManagement) {
    return (
      <div className={styles.profileContainer}>
        <button 
          onClick={() => setShowManagement(false)}
          className={styles.backButton}
        >
          ← Back to Profile
        </button>
        <ProfileManagement />
      </div>
    );
  }
  
  return (
    <div className={styles.profileSection}>
      <div className={styles.profileInfo}>
        <img 
          src={user?.avatar || defaultAvatar} 
          alt={`${user?.name || 'User'}'s avatar`}
          className={styles.avatar}
        />
        <div className={styles.userInfo}>
          <span className={styles.userName}>{user?.name || 'User'}</span>
          <span className={styles.userEmail}>{user?.email}</span>
        </div>
      </div>
      <button 
        onClick={() => setShowManagement(true)}
        className={styles.manageButton}
      >
        Manage Profile
      </button>
    </div>
  );
};
