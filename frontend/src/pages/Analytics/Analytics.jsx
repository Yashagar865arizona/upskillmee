import React, { useContext } from 'react';
import { AuthContext } from '../../context/AuthContext';
import AnalyticsDashboard from '../../components/Analytics/AnalyticsDashboard';
import styles from './Analytics.module.css';

const Analytics = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return (
      <div className={styles.container}>
        <div className={styles.loginPrompt}>
          <h2>Please log in to view your analytics</h2>
          <p>You need to be logged in to access your learning analytics and progress data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <AnalyticsDashboard 
        userId={user.id} 
        isAdmin={user.is_admin || false}
      />
    </div>
  );
};

export default Analytics;