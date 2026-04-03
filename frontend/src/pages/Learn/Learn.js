// src/pages/Learn/Learn.js
import React, { useState, useEffect } from 'react';
import LearningPlan from '../../components/LearningPlan/LearningPlan';
import PlanFeedback from '../../components/PlanFeedback/PlanFeedback';
import styles from './Learn.module.css';

const Learn = () => {
  const [activePlan, setActivePlan] = useState(null);
  const [userPlans, setUserPlans] = useState([]);

  useEffect(() => {
    // TODO: Fetch user's learning plans from backend
    const fetchPlans = async () => {
      try {
        const response = await fetch('/api/plans');
        const data = await response.json();
        setUserPlans(data);
        if (data.length > 0) {
          setActivePlan(data[0]);
        }
      } catch (error) {
        console.error('Error fetching plans:', error);
      }
    };

    fetchPlans();
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.mainContent}>
        <LearningPlan plan={activePlan} />
      </div>
      <div className={styles.sidebar}>
        <PlanFeedback plans={userPlans} />
      </div>
    </div>
  );
};

export default Learn;