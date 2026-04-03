import React, { useState } from 'react';
import { clearChatData } from '../../utils/clearLocalStorage';

const ClearData = () => {
  const [message, setMessage] = useState('');
  
  const handleClearLocalStorage = () => {
    const count = clearChatData();
    setMessage(`Cleared ${count} chat-related items from localStorage`);
  };
  
  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Development Tools</h1>
      <p>These tools are for development and testing purposes only.</p>
      
      <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Clear Chat Data</h2>
        <p>This will clear all chat-related data from your browser's localStorage.</p>
        <button 
          onClick={handleClearLocalStorage}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Clear Chat Data from localStorage
        </button>
        
        {message && (
          <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#e8f5e9', borderRadius: '4px' }}>
            {message}
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h2>Database Status</h2>
        <p>The database chat data has been cleared using the backend script.</p>
        <ul>
          <li>Deleted all messages from the messages table</li>
          <li>Deleted all conversations from the conversations table</li>
        </ul>
      </div>
    </div>
  );
};

export default ClearData; 