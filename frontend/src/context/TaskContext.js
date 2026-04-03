import React, { createContext, useContext } from 'react';
import { useLearningTasks } from '../hooks/useLearningTasks';
import { useAuth } from './AuthContext';

const TaskContext = createContext();

export function TaskProvider({ children, projects = [] }) {
  const { token } = useAuth();
  const { tasks, progress, toggleTaskCompletion } = useLearningTasks(projects);

  return (
    <TaskContext.Provider value={{ tasks, progress, toggleTaskCompletion }}>
      {children}
    </TaskContext.Provider>
  );
}

export function useTasks() {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return context;
}