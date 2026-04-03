import React from 'react';
import styles from './Loading.module.css';

const LoadingSpinner = ({ 
  size = 'medium', 
  color = 'primary', 
  text = null,
  className = '',
  fullScreen = false 
}) => {
  const sizeClass = styles[`spinner${size.charAt(0).toUpperCase() + size.slice(1)}`];
  const colorClass = styles[`spinner${color.charAt(0).toUpperCase() + color.slice(1)}`];
  
  const spinner = (
    <div className={`${styles.spinnerContainer} ${className}`}>
      <div className={`${styles.spinner} ${sizeClass} ${colorClass}`} />
      {text && <p className={styles.loadingText}>{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className={styles.fullScreenLoader}>
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;