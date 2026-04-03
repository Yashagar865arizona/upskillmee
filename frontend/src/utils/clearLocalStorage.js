/**
 * Utility function to clear chat-related data from localStorage
 * This is for development/testing purposes only
 */
export const clearChatData = () => {
  // Get all keys from localStorage
  const keys = Object.keys(localStorage);
  
  // Filter for chat-related keys
  const chatKeys = keys.filter(key => 
    key.startsWith('ponder_chat_messages') || 
    key.includes('chat') ||
    key.includes('message')
  );
  
  // Remove each chat-related key
  chatKeys.forEach(key => {
    localStorage.removeItem(key);
    console.log(`Cleared localStorage key: ${key}`);
  });
  
  console.log(`Cleared ${chatKeys.length} chat-related items from localStorage`);
  return chatKeys.length;
};

// For direct use in browser console
if (typeof window !== 'undefined') {
  window.clearChatData = clearChatData;
} 