import React, { useContext } from 'react';
import { AuthContext } from '../../context/AuthContext';
import MonitoringDashboard from '../../components/Monitoring/MonitoringDashboard';
import styles from './Monitoring.module.css';

const Monitoring = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return (
      <div className={styles.container}>
        <div className={styles.loginPrompt}>
          <h2>Please log in to view system monitoring</h2>
          <p>You need to be logged in to access system monitoring data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <MonitoringDashboard 
        isAdmin={user.is_admin || false}
      />
    </div>
  );
};

export default Monitoring;