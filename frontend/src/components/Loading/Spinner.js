import React from 'react';
import styles from './Loading.module.css';

const Spinner = ({
  size = 'medium',
  color = 'primary',
  fullScreen = false,
  text = null,
  className = ''
}) => {
  const spinnerClasses = [
    styles.spinner,
    styles[`spinner${size.charAt(0).toUpperCase() + size.slice(1)}`],
    styles[`spinner${color.charAt(0).toUpperCase() + color.slice(1)}`],
    className
  ].filter(Boolean).join(' ');

  const content = (
    <div className={styles.spinnerContainer}>
      <div className={spinnerClasses} />
      {text && <p className={styles.loadingText}>{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className={styles.fullScreenLoader}>
        {content}
      </div>
    );
  }

  return content;
};

// Predefined spinner configurations
export const LoadingSpinner = ({ text = "Loading..." }) => (
  <Spinner size="large" text={text} />
);

export const FullScreenSpinner = ({ text = "Loading..." }) => (
  <Spinner size="xlarge" text={text} fullScreen />
);

export const ButtonSpinner = () => (
  <Spinner size="small" color="white" />
);

export const InlineSpinner = () => (
  <Spinner size="small" />
);

export default Spinner;