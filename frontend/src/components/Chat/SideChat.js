import React, { useState, useRef, useEffect } from 'react';
import { sendMessageStream } from '../../api/chatApi';
import styles from './SideChat.module.css';
import avatar from '../../assets/avatar.png';

const SideChat = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messageIdRef = useRef(1);
  const messagesEndRef = useRef(null);
  const currentResponseRef = useRef(null);

  const handleSend = async () => {
    if (newMessage.trim() === '') return;

    const userMessage = {
      id: messageIdRef.current++,
      sender: 'user',
      text: newMessage,
      avatar: avatar
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    currentResponseRef.current = null;

    try {
      await sendMessageStream('default_user', newMessage, (chunk) => {
        if (!currentResponseRef.current) {
          currentResponseRef.current = {
            id: messageIdRef.current++,
            sender: 'bot',
            text: '',
            avatar: avatar
          };
          setMessages(prev => [...prev, currentResponseRef.current]);
        }
        currentResponseRef.current.text += chunk.text || '';
        setMessages(prev => [...prev.slice(0, -1), { ...currentResponseRef.current }]);
      });
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: messageIdRef.current++,
        sender: 'bot',
        text: "Sorry, I encountered an error. Please try again.",
        avatar: avatar
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);

  return (
    <div className={styles.sideChatContainer}>
      <div className={styles.chatMessages}>
        <div className={styles.welcomeMessage}>
          <p>How can I help you with this page?</p>
        </div>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.message} ${styles[msg.sender]}`}
          >
            <img src={msg.avatar} alt={msg.sender} className={styles.avatar} />
            <div className={styles.messageContent}>
              {(msg.text || '').split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className={styles.chatInput}>
        <textarea
          placeholder="Ask a question..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          rows={1}
          className={styles.messageInput}
        />
        <button 
          className={styles.sendButton} 
          onClick={handleSend}
          disabled={!newMessage.trim()}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default SideChat;
