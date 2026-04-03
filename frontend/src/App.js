import React, { useState } from 'react';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar/Sidebar';
import RightSidebar from './components/RightSidebar/RightSidebar';
import Dashboard from './pages/Dashboard/Dashboard';
import ChatPage from './pages/Chat/ChatPage';
import Community from './pages/Community/Community';
import Marketplace from './pages/Marketplace/Marketplace';
import Learn from './pages/Learn/Learn';
import Projects from './pages/Projects/Projects';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import ClearData from './pages/Admin/ClearData';
import Settings from './pages/Settings/Settings';
import Onboarding from './pages/OnBoarding/Onboarding';
import AllTasksList from './components/MainContent/AllTasksList';
import Home from './pages/Home/Home';
import styles from './App.module.css';
import { LearningPlanProvider } from './pages/Chat/context/LearningPlanContext';
import { useAuth } from './context/AuthContext';
import Calendar from './components/Calendar/Calendar';
import ProtectedRoute from './protectedRoute';
import OAuthSuccess from './OAuthSuccess';

function App() {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const showRightSidebar = location.pathname === '/dashboard';
const isAuthPage = location.pathname.startsWith('/auth') && location.pathname !== '/auth/success';

  // const isAuthPage = location.pathname.startsWith('/auth');
  const isAdminPage = location.pathname.startsWith('/admin');
  const isOnboardingPage = location.pathname.startsWith('/onboarding');

  
  if (location.pathname === '/' && !isAuthenticated) {
    return (
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    );
  }

  
  if (location.pathname === '/' && isAuthenticated && user) {
    if (!user.is_onboarding) return <Navigate to="/onboarding" replace />;
    return <Navigate to="/dashboard" replace />;
  }

  
  if (!isAuthenticated && !isAuthPage && !isAdminPage && !isOnboardingPage) {
    return <Navigate to="/auth/login" replace />;
  }

  
  if (isAuthPage) {
    if (isAuthenticated && user) {
      if (!user.is_onboarding) return <Navigate to="/onboarding" replace />;
      return <Navigate to="/dashboard" replace />;
    }
    return (
      <Routes>
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />
      </Routes>
    );
  }

  if (isAdminPage) {
    return (
      <Routes>
        <Route path="/admin/clear-data" element={<ClearData />} />
      </Routes>
    );
  }

  if (isOnboardingPage) {
    if (user?.is_onboarding) return <Navigate to="/dashboard" replace />;
    return (
      <Routes>
        <Route path="/onboarding" element={<Onboarding />} />
      </Routes>
    );
  }
if (location.pathname === '/auth/success') {
  return (
    <Routes>
      <Route path="/auth/success" element={<OAuthSuccess />} />
    </Routes>
  );
}

  return (
    <LearningPlanProvider>
      <div className={styles.app}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(prev => !prev)} />

        <div className={styles.mainContent}>
          <Routes>
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
            <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
            <Route path="/community" element={<ProtectedRoute><Community /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/marketplace" element={<ProtectedRoute><Marketplace /></ProtectedRoute>} />
            <Route path="/learn" element={<ProtectedRoute><Learn /></ProtectedRoute>} />
            <Route path="/alltaskslist" element={<ProtectedRoute><AllTasksList /></ProtectedRoute>} />
            <Route path="/calendar" element={<ProtectedRoute><Calendar /></ProtectedRoute>} />
            

            <Route path="*" element={<div>Page Not Found</div>} />
          </Routes>
        </div>

        {showRightSidebar && <RightSidebar />}
      </div>
    </LearningPlanProvider>
  );
}



export default App;
