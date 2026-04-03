import React from 'react';
import ProjectBoard from './ProjectBoard';
import styles from './MainContent.module.css';

export const MainContent = () => {
  return (
    <div className={styles.mainContent}>
      <ProjectBoard />
    </div>
  );
};