import React from "react";
import styles from "./UserProfile.module.css";
import { useAuth } from '../../../context/AuthContext';

/**
 * UserProfile Component
 * Displays user information including name, gems, points, and avatar
 * 
 * @param {Object} props - Component props
 * @param {number} props.gems - User's gem count
 * @param {number} props.points - User's point count
 */
export const UserProfile = ({ gems, points }) => {
  const { user } = useAuth();
  
  return (
    <div className={styles.profileContainer}>
      {/* Notifications/Stats Section */}
      <div className={styles.notifications}>
        {/* Gems Counter */}
        <div className={`${styles.notification} ${styles.purple}`}>
          <div className={styles.iconWrapper}>
            <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg" className={styles.notificationIcon}>
              {/* Diamond/Gem shape */}
              <path d="M10.25 1.5H5.75L0.5 5.525L8 15.5L15.5 5.525L10.25 1.5Z" fill="#9450E0"/>
              <path d="M8 15.5L11.125 5.525H4.7L8 15.5ZM2.375 2.875L0.5 5.525H4.7L5.75 1.5L2.375 2.875ZM13.625 2.875L10.25 1.5L11.125 5.525H15.5L13.625 2.875Z" fill="#C28FEF"/>
            </svg>
          </div>
          {gems}
        </div>

        {/* Points Counter */}
        <div className={`${styles.notification} ${styles.blue}`}>
          <div className={styles.iconWrapper}>
            <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg" className={styles.notificationIcon}>
              {/* Lightning bolt shape */}
              <path d="M9.58667 2.02575C9.64368 1.75969 9.51452 1.48857 9.27198 1.36522C9.02945 1.24187 8.73428 1.29717 8.55284 1.49995L1.75284 9.09995C1.59506 9.2763 1.55566 9.52891 1.65224 9.74493C1.74883 9.96095 1.96336 10.1 2.19999 10.1H7.45779L6.4133 14.9743C6.35629 15.2404 6.48546 15.5115 6.72799 15.6348C6.97052 15.7582 7.2657 15.7029 7.44713 15.5001L14.2471 7.90011C14.4049 7.72376 14.4443 7.47115 14.3477 7.25513C14.2511 7.03911 14.0366 6.90003 13.8 6.90003H8.54218L9.58667 2.02575Z" fill="#7884FF"/>
            </svg>
          </div>
          {points}
        </div>
      </div>

      {/* User Profile Box */}
      <div className={styles.profileBox}>
        {/* User Info (Avatar + Name) */}
        <div className={styles.profileInfo}>
          <img src={user?.avatar} alt={`${user?.name}'s avatar`} className={styles.avatar} />
          <span className={styles.userName}>{user?.name}</span>
        </div>
        {/* Dropdown Arrow */}
        <div className={styles.dropdownArrow}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" strokeWidth="2.5">
            <path d="M6 9L12 15L18 9" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  );
};
