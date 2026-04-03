import React from "react";
import styles from "./Chat.module.css";

export const ChatMessage = ({ content, isUser, userName, plan, isLoading }) => {
  const messageClass = isUser ? styles.userMessage : styles.aiMessage;
  const name = isUser ? (userName || 'You') : 'Ponder';

  // If this message has a plan, show a special indicator
  const hasPlan = !!plan;

  return (
    <div 
      className={`${styles.messageWrapper} ${messageClass} ${isUser ? styles.userMessageWrapper : styles.botMessageWrapper}`}
      data-loading={isLoading ? "true" : "false"}
    >
      <div className={styles.messageHeader}>
        <span className={styles.userName}>{name}</span>
        {hasPlan && (
          <span className={styles.planBadge}>
            🎯 Learning Plan Created! Check Project Board
          </span>
        )}
      </div>
      <div className={styles.messageContent}>
        {content}
      </div>
    </div>
  );
};
