// src/pages/Marketplace/Marketplace.js
import React from 'react';
import ComingSoon from '../../components/ComingSoon/ComingSoon';
import styles from './Marketplace.module.css';

const Marketplace = () => {
  return (
    <div className={styles.container}>
      <ComingSoon feature="Marketplace" />
    </div>
  );
};

export default Marketplace;