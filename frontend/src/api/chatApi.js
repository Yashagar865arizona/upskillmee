import axios from 'axios';
import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

export const sendMessage = async (message, userId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: userId
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to send message');
    }

    return response;
  } catch (error) {
    console.error('Error in sendMessage:', error);
    throw error;
  }
};

export const sendMessageStream = async (userId, messageData, onChunk) => {
  try {
    // Handle both old string format and new object format
    const requestBody = typeof messageData === 'string' 
      ? { message: messageData, user_id: userId }
      : { ...messageData, user_id: userId };
    
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || 'Failed to send message';
      } catch {
        errorMessage = errorText || 'Failed to send message';
      }
      throw new Error(errorMessage);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onChunk(data);
          } catch (e) {
            console.error('Error parsing chunk:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error sending streaming message:', error);
    throw error;
  }
};
