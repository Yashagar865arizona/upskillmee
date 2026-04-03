import React from 'react';
import styles from './PlanFeedback.module.css';
import { submitPlanFeedback } from '../../api/learningApi';

const PlanFeedback = ({ plans = [] }) => {
  const handleFeedback = async (planId, isPositive) => {
    try {
      await submitPlanFeedback(planId, isPositive);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  return (
    <div className={styles.planFeedbackContainer}>
      <h3>Generated Learning Plans</h3>
      {plans.length === 0 ? (
        <p>No learning plans generated yet. Start a chat to create one!</p>
      ) : (
        <div className={styles.plansList}>
          {plans.map((plan, index) => (
            <div key={plan.id || index} className={styles.planItem}>
              <h4>{plan.title || `Learning Plan ${index + 1}`}</h4>
              <p>{plan.description || 'No description available'}</p>
              <div className={styles.feedbackButtons}>
                <button
                  onClick={() => handleFeedback(plan.id, true)}
                  className={`${styles.feedbackButton} ${styles.positive}`}
                >
                  👍
                </button>
                <button
                  onClick={() => handleFeedback(plan.id, false)}
                  className={`${styles.feedbackButton} ${styles.negative}`}
                >
                  👎
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlanFeedback;
