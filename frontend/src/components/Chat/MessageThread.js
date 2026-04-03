import React, { useState, useEffect } from 'react';
import styles from './MessageThread.module.css';

const MessageThread = ({ 
  conversations, 
  selectedThread, 
  onThreadSelect, 
  onNewConversation,
  currentUserId 
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getConversationPreview = (conversation) => {
    if (!conversation.messages || conversation.messages.length === 0) {
      return 'New conversation';
    }
    const lastMessage = conversation.messages[conversation.messages.length - 1];
    return lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '');
  };

  return (
    <div className={`${styles.threadContainer} ${isCollapsed ? styles.collapsed : ''}`}>
      <div className={styles.threadHeader}>
        <h3>Conversations</h3>
        <div className={styles.threadActions}>
          <button 
            className={styles.newConversationBtn}
            onClick={onNewConversation}
            title="Start new conversation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </button>
          <button 
            className={styles.collapseBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={isCollapsed ? "M9 18l6-6-6-6" : "M18 15l-6-6-6 6"}/>
            </svg>
          </button>
        </div>
      </div>
      
      {!isCollapsed && (
        <div className={styles.threadList}>
          {conversations.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No conversations yet</p>
              <button onClick={onNewConversation} className={styles.startChatBtn}>
                Start your first chat
              </button>
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`${styles.threadItem} ${
                  selectedThread?.id === conversation.id ? styles.active : ''
                }`}
                onClick={() => onThreadSelect(conversation)}
              >
                <div className={styles.threadInfo}>
                  <div className={styles.threadTitle}>
                    {conversation.topic || 'Untitled Conversation'}
                  </div>
                  <div className={styles.threadPreview}>
                    {getConversationPreview(conversation)}
                  </div>
                  <div className={styles.threadMeta}>
                    <span className={styles.threadDate}>
                      {formatDate(conversation.updated_at || conversation.created_at)}
                    </span>
                    {conversation.agent_mode && (
                      <span className={`${styles.agentMode} ${styles[conversation.agent_mode]}`}>
                        {conversation.agent_mode}
                      </span>
                    )}
                  </div>
                </div>
                {conversation.unread_count > 0 && (
                  <div className={styles.unreadBadge}>
                    {conversation.unread_count}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default MessageThread;