/**
 * WebSocket service for real-time chat communication
 * Handles connection management, message sending, and automatic reconnection
 */

import config from '../config';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.messageQueue = [];
    this.listeners = new Map();
    this.heartbeatInterval = null;
    this.heartbeatTimeout = null;
    this.token = null;
    this.userId = null;
  }

  /**
   * Connect to WebSocket server
   * @param {string} token - JWT authentication token
   * @param {string} userId - User ID for the connection
   */
  connect(token, userId) {
    if (this.isConnecting || this.isConnected) {
      console.log('WebSocket already connecting or connected');
      return Promise.resolve();
    }

    this.token = token;
    this.userId = userId;
    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${config.WS_BASE_URL}/chat/ws`;
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;

          // Send authentication message
          this.sendAuth();

          // Start heartbeat
          this.startHeartbeat();

          // Process queued messages
          this.processMessageQueue();

          // Notify listeners
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.handleDisconnection();
          
          if (this.isConnecting) {
            reject(new Error('Failed to connect to WebSocket'));
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', error);
          
          if (this.isConnecting) {
            reject(error);
          }
        };

      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Send authentication message to server
   */
  sendAuth() {
    if (this.token) {
      this.send({
        type: 'auth',
        token: this.token
      });
    }
  }

  /**
   * Send a chat message
   * @param {string} message - The message text
   * @param {string} agentMode - The agent mode (chat, work, plan)
   * @param {Array} chatHistory - Previous messages for context
   * @param {Array} files - Uploaded files (optional)
   */
  sendMessage(message, agentMode = 'chat', chatHistory = [], files = []) {
    const messageData = {
      type: 'message',
      message: message,
      agent_mode: agentMode,
      chat_history: chatHistory,
      files: files.map(file => ({
        id: file.id,
        name: file.name,
        size: file.size,
        type: file.type,
        content: file.content || null,
        preview: file.preview || null
      })),
      timestamp: new Date().toISOString()
    };

    this.send(messageData);
  }

  /**
   * Send typing indicator
   * @param {boolean} isTyping - Whether user is typing
   */
  sendTypingIndicator(isTyping) {
    this.send({
      type: 'typing',
      is_typing: isTyping,
      timestamp: new Date().toISOString()
    });
  }
/**
   * Send agent mode change
   * @param {string} mode - The new agent mode
   */
  sendModeChange(mode) {
    this.send({
      type: 'mode_change',
      agent_mode: mode,
      timestamp: new Date().toISOString()
    });
  }
  /**
   * Send message status update
   * @param {string} messageId - Message ID
   * @param {string} status - Status (sent, delivered, read, failed)
   */
  sendMessageStatus(messageId, status) {
    this.send({
      type: 'message_status',
      message_id: messageId,
      status: status,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send data through WebSocket or queue if not connected
   * @param {Object} data - Data to send
   */
  send(data) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        this.messageQueue.push(data);
      }
    } else {
      console.log('WebSocket not connected, queuing message');
      this.messageQueue.push(data);
    }
  }

  /**
   * Handle incoming messages from server
   * @param {Object} data - Parsed message data
   */
  handleMessage(data) {
    // Handle heartbeat acknowledgment
    if (data.type === 'heartbeat_ack') {
      this.resetHeartbeatTimeout();
      return;
    }

    // Handle authentication acknowledgment
    if (data.status === 'acknowledged') {
      console.log('Authentication acknowledged');
      this.emit('authenticated');
      return;
    }

    // Handle regular messages
    this.emit('message', data);
  }

  /**
   * Handle WebSocket disconnection
   */
  handleDisconnection() {
    this.isConnected = false;
    this.isConnecting = false;
    this.stopHeartbeat();
    
    this.emit('disconnected');

    // Attempt reconnection if not manually disconnected
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('reconnectFailed');
    }
  }

  /**
   * Schedule automatic reconnection
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });

    setTimeout(() => {
      if (!this.isConnected && this.token) {
        this.connect(this.token, this.userId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Process queued messages after reconnection
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'heartbeat' });
        
        // Set timeout for heartbeat response
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('Heartbeat timeout - connection may be lost');
          this.disconnect();
        }, 5000);
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Reset heartbeat timeout
   */
  resetHeartbeatTimeout() {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Manually disconnect WebSocket
   */
  disconnect() {
    console.log('Manually disconnecting WebSocket');
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Get connection status
   * @returns {Object} Connection status information
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length
    };
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;