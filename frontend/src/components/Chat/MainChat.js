import React, { useState, useRef, useEffect, useCallback } from 'react';
import styles from './MainChat.module.css';
import avatar from '../../assets/avatar.png';
import { useTasks } from '../../context/TaskContext';
import { useAuth } from '../../context/AuthContext';
import AgentModeSelector from './AgentModeSelector';
import ConnectionStatus from './ConnectionStatus';
import MessageThread from './MessageThread';
import FileUpload from './FileUpload';
import MessageStatusIndicator from './MessageStatusIndicator';
import websocketService from '../../services/websocketService';

const MainChat = () => {
  const { updateCurrentPlan } = useTasks();
  const { token, user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [assistantName] = useState('AI Assistant');
  const [agentMode, setAgentMode] = useState('chat');
  const [availableModes, setAvailableModes] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0
  });
  const [isTyping, setIsTyping] = useState(false);
  const [messageStatuses, setMessageStatuses] = useState({});
  const [selectedThread, setSelectedThread] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showTypingUsers, setShowTypingUsers] = useState([]);
  const messageIdRef = useRef(1);
  const messagesEndRef = useRef(null);
  const currentResponseRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Initialize WebSocket connection when authenticated
  useEffect(() => {
    if (isAuthenticated && token && user) {
      console.log('Initializing WebSocket connection for user:', user.id);
      initializeWebSocket();
      loadConversations();
    } else {
      console.log('Not authenticated, disconnecting WebSocket');
      websocketService.disconnect();
    }

    return () => {
      websocketService.disconnect();
    };
  }, [isAuthenticated, token, user]);

  // Load conversations from backend
  const loadConversations = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/chat/history/${user.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const conversationList = Object.values(data.conversations || {}).map(conv => ({
          ...conv,
          messages: data.messages.filter(msg => msg.conversation_id === conv.id)
        }));
        setConversations(conversationList);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  // Initialize WebSocket connection
  const initializeWebSocket = useCallback(async () => {
    try {
      setConnectionStatus(prev => ({ ...prev, isConnecting: true }));
      
      // Set up event listeners
      websocketService.on('connected', handleWebSocketConnected);
      websocketService.on('disconnected', handleWebSocketDisconnected);
      websocketService.on('reconnecting', handleWebSocketReconnecting);
      websocketService.on('message', handleWebSocketMessage);
      websocketService.on('error', handleWebSocketError);
      websocketService.on('authenticated', handleWebSocketAuthenticated);

      // Connect to WebSocket
      await websocketService.connect(token, user.id);
      
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setConnectionStatus(prev => ({ 
        ...prev, 
        isConnecting: false, 
        isConnected: false 
      }));
    }
  }, [token, user]);

  // WebSocket event handlers
  const handleWebSocketConnected = useCallback(() => {
    console.log('WebSocket connected');
    setConnectionStatus({
      isConnected: true,
      isConnecting: false,
      reconnectAttempts: 0
    });
  }, []);

  const handleWebSocketDisconnected = useCallback(() => {
    console.log('WebSocket disconnected');
    setConnectionStatus(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false
    }));
  }, []);

  const handleWebSocketReconnecting = useCallback((data) => {
    console.log('WebSocket reconnecting:', data);
    setConnectionStatus(prev => ({
      ...prev,
      isConnecting: true,
      reconnectAttempts: data.attempt
    }));
  }, []);

  const handleWebSocketAuthenticated = useCallback(() => {
    console.log('WebSocket authenticated');
  }, []);

  const handleWebSocketError = useCallback((error) => {
    console.error('WebSocket error:', error);
    // Add error message to chat
    const errorMessage = {
      id: messageIdRef.current++,
      sender: 'system',
      text: 'Connection error occurred. Attempting to reconnect...',
      avatar: avatar,
      timestamp: new Date().toISOString(),
      isError: true
    };
    setMessages(prev => [...prev, errorMessage]);
  }, []);

  const handleWebSocketMessage = useCallback((data) => {
    console.log('Received WebSocket message:', data);

    // Handle different message types
    if (data.type === 'typing_indicator') {
      // Handle typing indicator from other users
      if (data.user_id !== user?.id) {
        if (data.is_typing) {
          setShowTypingUsers(prev => [...prev.filter(id => id !== data.user_id), data.user_id]);
        } else {
          setShowTypingUsers(prev => prev.filter(id => id !== data.user_id));
        }
      }
      return;
    }

    if (data.type === 'message_status') {
      // Handle message status updates
      setMessageStatuses(prev => ({
        ...prev,
        [data.message_id]: data.status
      }));
      return;
    }

    // Stop typing indicator when receiving a message
    setIsTyping(false);
    setShowTypingUsers([]);

    // Handle authentication required
    if (data.auth_required) {
      const authMessage = {
        id: messageIdRef.current++,
        sender: 'system',
        text: data.text || 'Authentication required. Please refresh the page.',
        avatar: avatar,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, authMessage]);
      return;
    }

    // Handle regular messages
    handleResponse(data);
  }, [user?.id]);

  const handleSend = async () => {
    if (newMessage.trim() === '' || !connectionStatus.isConnected) return;

    const messageId = messageIdRef.current++;
    const userMessage = {
      id: messageId,
      sender: 'user',
      text: newMessage,
      avatar: avatar,
      timestamp: new Date().toISOString(),
      status: 'sending',
      files: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    setMessageStatuses(prev => ({ ...prev, [messageId]: 'sending' }));
    
    const messageText = newMessage;
    setNewMessage('');
    setUploadedFiles([]);
    currentResponseRef.current = null;
    setIsTyping(true);

    // Show typing indicator for user
    handleTypingIndicator();

    try {
      // Get chat history for context (last 10 messages)
      const chatHistory = messages.slice(-10).map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text,
        timestamp: msg.timestamp
      }));
      
      console.log('Sending message with agentMode::::::::::::::::::::::::::::', agentMode);   
      // Send message via WebSocket
      websocketService.sendMessage(messageText, agentMode, chatHistory, uploadedFiles);
      
      // Update message status to sent
      setMessageStatuses(prev => ({ ...prev, [messageId]: 'sent' }));
      
      // Simulate delivery status (in real app, this would come from server)
      setTimeout(() => {
        setMessageStatuses(prev => ({ ...prev, [messageId]: 'delivered' }));
      }, 1000);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsTyping(false);
      setMessageStatuses(prev => ({ ...prev, [messageId]: 'failed' }));
      handleResponse({
        text: "Sorry, I encountered an error sending your message. Please try again.",
        sender: "bot",
        id: messageIdRef.current++
      });
    }
  };

  const handleTypingIndicator = () => {
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set typing timeout
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 3000);
  };

  // Handle user typing
  const handleUserTyping = useCallback((value) => {
    setNewMessage(value);
    
    // Send typing indicator to server
    if (connectionStatus.isConnected) {
      websocketService.sendTypingIndicator(true);
      
      // Clear existing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Stop typing after 2 seconds of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        websocketService.sendTypingIndicator(false);
      }, 2000);
    }
  }, [connectionStatus.isConnected]);

  const handleFileUpload = async (files) => {
    setUploadedFiles(prev => [...prev, ...files]);
    setShowFileUpload(false);
  };

  const removeUploadedFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleNewConversation = () => {
    setMessages([]);
    setSelectedThread(null);
    setUploadedFiles([]);
    setMessageStatuses({});
    setIsTyping(false);
    setShowTypingUsers([]);
  };

  const handleThreadSelect = (conversation) => {
    setSelectedThread(conversation);
    setMessageStatuses({});
    setIsTyping(false);
    setShowTypingUsers([]);
    
    // Load conversation messages with animation
    if (conversation.messages) {
      setMessages([]);
      setTimeout(() => {
        setMessages(conversation.messages.map(msg => ({
          ...msg,
          id: msg.id || messageIdRef.current++,
          sender: msg.role === 'user' ? 'user' : 'bot',
          text: msg.content,
          avatar: avatar,
          timestamp: msg.created_at || msg.timestamp
        })));
      }, 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReconnect = useCallback(() => {
    if (isAuthenticated && token && user) {
      initializeWebSocket();
    }
  }, [isAuthenticated, token, user, initializeWebSocket]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);

  const handleResponse = useCallback((data) => {
    // Update available modes if provided
    if (data.agent_info?.available_modes) {
      setAvailableModes(data.agent_info.available_modes);
    }
    
    // Update agent mode if provided and different from current
    if (data.agent_mode && data.agent_mode !== agentMode) {
      setAgentMode(data.agent_mode);
    }
    
    if (data.type === "learning_plan") {
      // First, show a message about creating the plan
      const loadingMessage = {
        id: messageIdRef.current++,
        sender: 'bot',
        text: "I'll help you create a learning plan. First, let me ask you a few questions to understand your needs better.",
        avatar: avatar,
        agentMode: data.agent_mode || 'plan',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, loadingMessage]);
      
      // If we actually got a plan, update it
      if (data.plan) {
        updateCurrentPlan(data.plan);
        const planMessage = {
          id: messageIdRef.current++,
          sender: 'bot',
          text: `Great! I've created a personalized learning plan for ${data.plan.title}. You can view the full plan in the learning section.`,
          avatar: avatar,
          agentMode: data.agent_mode || 'plan',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, planMessage]);
      }
    } else {
      // Handle regular text responses
      const botMessage = {
        id: data.id || messageIdRef.current++,
        sender: 'bot',
        text: data.text || '',
        avatar: avatar,
        agentMode: data.agent_mode || agentMode,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, botMessage]);
    }
  }, [agentMode, updateCurrentPlan]);

  return (
    <div className={styles.chatContainer}>
      <MessageThread
        conversations={conversations}
        selectedThread={selectedThread}
        onThreadSelect={handleThreadSelect}
        onNewConversation={handleNewConversation}
        currentUserId={user?.id}
      />
      
      <div className={styles.chatMain}>
        <div className={styles.chatHeader}>
          <div className={styles.assistantInfo}>
            <img src={avatar} alt="AI Assistant" className={styles.assistantAvatar} />
            <span className={styles.assistantName}>{assistantName}</span>
            {selectedThread && (
              <span className={styles.conversationTitle}>
                {selectedThread.topic || 'Conversation'}
              </span>
            )}
          </div>
          <ConnectionStatus
            isConnected={connectionStatus.isConnected}
            isConnecting={connectionStatus.isConnecting}
            reconnectAttempts={connectionStatus.reconnectAttempts}
            onReconnect={handleReconnect}
          />
        </div>
      <div className={styles.chatMessages}>
        <div className={styles.welcomeMessage}>
          <h2>Welcome to upskillmee</h2>
          <p>I'm your intelligent learning companion with specialized modes:</p>
          <ul>
            <li><strong>💬 Chat Mode:</strong> General conversation, motivation, and learning guidance</li>
            <li><strong>🔧 Work Mode:</strong> Technical help, debugging, and step-by-step project assistance</li>
            <li><strong>📋 Plan Mode:</strong> Create and customize personalized learning plans</li>
          </ul>
          <p>Select a mode below the chat and let's start your learning journey!</p>
        </div>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.message} ${styles[msg.sender]} ${msg.isError ? styles.error : ''} ${styles.messageWithAnimation}`}
          >
            <img src={msg.avatar} alt={msg.sender} className={styles.avatar} />
            <div className={styles.messageContent}>
              {/* File attachments */}
              {msg.files && msg.files.length > 0 && (
                <div className={styles.messageFiles}>
                  {msg.files.map((file) => (
                    <div key={file.id} className={styles.fileAttachment}>
                      {file.preview ? (
                        <img src={file.preview} alt={file.name} className={styles.filePreview} />
                      ) : (
                        <div className={styles.fileIcon}>
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14,2 14,8 20,8"/>
                          </svg>
                        </div>
                      )}
                      <div className={styles.fileInfo}>
                        <span className={styles.fileName}>{file.name}</span>
                        <span className={styles.fileSize}>
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Message text */}
              {(msg.text || '').split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
              
              {/* Message status and timestamp */}
              <div className={styles.messageFooter}>
                {msg.timestamp && (
                  <span className={styles.timestamp}>
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
                {msg.sender === 'user' && (
                  <MessageStatusIndicator 
                    status={messageStatuses[msg.id] || msg.status || 'sent'} 
                    timestamp={msg.timestamp}
                    showTimestamp={false}
                  />
                )}
              </div>
            </div>
          </div>
        ))}
        {(isTyping || showTypingUsers.length > 0) && (
          <div className={`${styles.message} ${styles.bot} ${styles.typingMessage}`}>
            <img src={avatar} alt="bot" className={styles.avatar} />
            <div className={styles.messageContent}>
              <div className={styles.typingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
              {showTypingUsers.length > 0 && (
                <div className={styles.typingText}>
                  {showTypingUsers.length === 1 ? 'Someone is typing...' : `${showTypingUsers.length} people are typing...`}
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <AgentModeSelector 
        currentMode={agentMode}
        onModeChange={setAgentMode}
        availableModes={availableModes}
      />
      <div className={styles.chatInputContainer}>
        {/* File upload preview */}
        {uploadedFiles.length > 0 && (
          <div className={styles.uploadPreview}>
            {uploadedFiles.map((file) => (
              <div key={file.id} className={styles.uploadedFile}>
                {file.preview ? (
                  <img src={file.preview} alt={file.name} className={styles.uploadPreviewImage} />
                ) : (
                  <div className={styles.uploadFileIcon}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14,2 14,8 20,8"/>
                    </svg>
                  </div>
                )}
                <span className={styles.uploadFileName}>{file.name}</span>
                <button 
                  className={styles.removeFileBtn}
                  onClick={() => removeUploadedFile(file.id)}
                  title="Remove file"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        <div className={styles.chatInput}>
          <button 
            className={styles.attachButton}
            onClick={() => setShowFileUpload(true)}
            title="Attach files"
            disabled={!connectionStatus.isConnected}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          
          <textarea
            placeholder={connectionStatus.isConnected ? "Type your message..." : "Connecting..."}
            value={newMessage}
            onChange={(e) => handleUserTyping(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            className={styles.messageInput}
            disabled={!connectionStatus.isConnected}
          />
          
          <button 
            className={styles.sendButton} 
            onClick={handleSend}
            disabled={(!newMessage.trim() && uploadedFiles.length === 0) || !connectionStatus.isConnected}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      {/* File Upload Modal */}
      {showFileUpload && (
        <FileUpload
          onFileUpload={handleFileUpload}
          onClose={() => setShowFileUpload(false)}
        />
      )}
      </div>
    </div>
  );
};

export default MainChat;
