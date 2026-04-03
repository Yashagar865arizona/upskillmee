// src/components/Layout/Layout.js
import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../Sidebar/Sidebar';
import RightSidebar from '../RightSidebar/RightSidebar';
import ErrorBoundary from '../ErrorBoundary/ErrorBoundary';
import styles from './Layout.module.css';

const Layout = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <ErrorBoundary level="page">
      <div className={styles.layoutContainer}>
        <Sidebar 
          isMobile={isMobile}
          isOpen={sidebarOpen}
          onClose={handleSidebarClose}
        />
        
        {isMobile && sidebarOpen && (
          <div 
            className={styles.overlay}
            onClick={handleSidebarClose}
            aria-hidden="true"
          />
        )}
        
        <main className={styles.mainContent}>
          {isMobile && (
            <button
              className={styles.menuButton}
              onClick={handleSidebarToggle}
              aria-label="Toggle navigation menu"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 12H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M3 6H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          )}
          
          <ErrorBoundary level="component">
            <Outlet />
          </ErrorBoundary>
        </main>
        
        {!isMobile && <RightSidebar />}
      </div>
    </ErrorBoundary>
  );
};

export default Layout;