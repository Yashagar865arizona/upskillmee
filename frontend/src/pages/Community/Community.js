// src/pages/Community/Community.js
import React from 'react';
import ComingSoon from '../../components/ComingSoon/ComingSoon';
import styles from './Community.module.css';

const Community = () => {
  return (
    <div className={styles.container}>
      <ComingSoon feature="Community" />
    </div>
  );
};

export default Community;