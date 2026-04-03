import React from 'react';
import styles from './ConnectionStatus.module.css';

const ConnectionStatus = ({ 
  isConnected, 
  isConnecting, 
  reconnectAttempts, 
  onReconnect 
}) => {
  if (isConnected) {
    return (
      <div className={`${styles.status} ${styles.connected}`}>
        <div className={styles.indicator}></div>
        <span>Connected</span>
      </div>
    );
  }

  if (isConnecting) {
    return (
      <div className={`${styles.status} ${styles.connecting}`}>
        <div className={styles.spinner}></div>
        <span>Connecting...</span>
      </div>
    );
  }

  return (
    <div className={`${styles.status} ${styles.disconnected}`}>
      <div className={styles.indicator}></div>
      <span>
        Disconnected
        {reconnectAttempts > 0 && ` (${reconnectAttempts} attempts)`}
      </span>
      <button 
        className={styles.reconnectButton}
        onClick={onReconnect}
        title="Reconnect"
      >
        ↻
      </button>
    </div>
  );
};

export default ConnectionStatus;