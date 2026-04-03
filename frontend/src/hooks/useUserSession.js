import { useState, useEffect } from 'react';

export const useUserSession = () => {
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(null);

  useEffect(() => {
    // Try to get existing session from localStorage
    const storedUserId = localStorage.getItem('userId');
    const storedUserName = localStorage.getItem('userName');
    
    if (storedUserId) {
      setUserId(storedUserId);
      setUserName(storedUserName);
    } else {
      // Create new user ID if none exists
      const newUserId = `user_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('userId', newUserId);
      setUserId(newUserId);
    }
  }, []);

  const updateUserName = (name) => {
    localStorage.setItem('userName', name);
    setUserName(name);
  };

  return {
    userId,
    userName,
    updateUserName,
  };
};
