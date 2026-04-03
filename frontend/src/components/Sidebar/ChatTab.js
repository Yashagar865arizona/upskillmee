import React from 'react';
import styles from './ChatTab.module.css';

const ChatTab = ({ assistantName, isActive }) => {
  return (
    <div className={`${styles.sidebarItem} ${isActive ? styles.active : ''}`}>
      <div className={styles.iconWrapper}>
        <img 
          src="/assets/assistant-avatar.png" 
          alt="AI Assistant" 
          className={styles.assistantIcon}
        />
      </div>
      <span className={styles.tabText}>Chat with {assistantName}</span>
    </div>
  );
};

export default ChatTab; 