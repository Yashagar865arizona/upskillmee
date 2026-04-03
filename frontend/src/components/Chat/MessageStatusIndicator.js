import React from 'react';
import styles from './MessageStatusIndicator.module.css';

const MessageStatusIndicator = ({ status, timestamp, showTimestamp = true }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'sending':
        return (
          <div className={styles.sendingIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </div>
        );
      case 'sent':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
        );
      case 'delivered':
        return (
          <div className={styles.deliveredIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          </div>
        );
      case 'read':
        return (
          <div className={styles.readIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" strokeWidth="0">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" strokeWidth="0">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          </div>
        );
      case 'failed':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10"/>
            <path d="M15 9l-6 6M9 9l6 6"/>
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'sending':
        return 'Sending...';
      case 'sent':
        return 'Sent';
      case 'delivered':
        return 'Delivered';
      case 'read':
        return 'Read';
      case 'failed':
        return 'Failed to send';
      default:
        return '';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffMinutes = Math.ceil(diffTime / (1000 * 60));
    const diffHours = Math.ceil(diffTime / (1000 * 60 * 60));
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <div className={`${styles.statusIndicator} ${styles[status]}`}>
      <div className={styles.statusIcon}>
        {getStatusIcon()}
      </div>
      {showTimestamp && timestamp && (
        <span className={styles.timestamp}>
          {formatTimestamp(timestamp)}
        </span>
      )}
      <span className={styles.statusText} title={getStatusText()}>
        {getStatusText()}
      </span>
    </div>
  );
};

export default MessageStatusIndicator;