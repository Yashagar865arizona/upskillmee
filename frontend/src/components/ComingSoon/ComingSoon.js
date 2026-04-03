import React from 'react';
import styles from './ComingSoon.module.css';

const ComingSoon = ({ feature }) => {
  return (
    <div className={styles.comingSoon}>
      <h2>{feature}</h2>
      <p>This feature is coming soon!</p>
      <p>We're working hard to bring you the best experience possible.</p>
    </div>
  );
};

export default ComingSoon; 