import React from 'react';
import styles from './MobileLoadingScreen.module.css';

const MobileLoadingScreen = ({ 
  message = "Loading...", 
  progress = null,
  showProgress = false,
  variant = 'default'
}) => {
  return (
    <div className={`${styles.loadingScreen} ${styles[variant]}`}>
      <div className={styles.loadingContent}>
        <div className={styles.spinnerContainer}>
          <div className={styles.spinner} />
          <div className={styles.pulseRing} />
        </div>
        
        <div className={styles.messageContainer}>
          <h2 className={styles.loadingMessage}>{message}</h2>
          
          {showProgress && progress !== null && (
            <div className={styles.progressContainer}>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>
              <span className={styles.progressText}>{Math.round(progress)}%</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Specialized loading screens for different contexts
export const AppLoadingScreen = () => (
  <MobileLoadingScreen 
    message="Starting Ponder AI..."
    variant="fullscreen"
  />
);

export const DataLoadingScreen = ({ message = "Loading your data..." }) => (
  <MobileLoadingScreen 
    message={message}
    variant="overlay"
  />
);

export const ProgressLoadingScreen = ({ message, progress }) => (
  <MobileLoadingScreen 
    message={message}
    progress={progress}
    showProgress={true}
    variant="overlay"
  />
);

export default MobileLoadingScreen;