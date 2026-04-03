import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { TaskProvider } from './context/TaskContext';
import AuthProvider from './context/AuthContext';
import ThemeProvider from './context/ThemeContext';
import App from './App';
import './index.css';
import { UserProvider } from './context/UserContext';

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <UserProvider>
        <TaskProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </TaskProvider>
        </UserProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
