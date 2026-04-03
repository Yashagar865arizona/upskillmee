import React from 'react';
import styles from './Chat_RightSidebar.module.css';
import MainChat from '../Chat/MainChat';

const Chat_RightSidebar = () => {
  return (
    <div className={styles.rightSidebar}>
      <div className={styles.progressSection}>
        <div className={styles.progressBar}>
          <div className={styles.progressInfo}>
            <span>All Tasks Progress</span>
            <span>70% complete</span>
          </div>
          <div className={styles.progressTrack}>
            <div
              className={`${styles.progressFill} ${styles.blue}`}
              style={{ width: '70%' }}
            ></div>
          </div>
        </div>
        <div className={styles.progressBar}>
          <div className={styles.progressInfo}>
            <span>Weekly Progress</span>
            <span>60% complete</span>
          </div>
          <div className={styles.progressTrack}>
            <div
              className={`${styles.progressFill} ${styles.yellow}`}
              style={{ width: '60%' }}
            ></div>
          </div>
        </div>
        <div className={styles.progressBar}>
          <div className={styles.progressInfo}>
            <span>Monthly Progress</span>
            <span>20% complete</span>
          </div>
          <div className={styles.progressTrack}>
            <div
              className={`${styles.progressFill} ${styles.red}`}
              style={{ width: '20%' }}
            ></div>
          </div>
        </div>
      </div>
      <div className={styles.chatWrapper}>
        <MainChat />
      </div>
    </div>
  );
};

export default Chat_RightSidebar;