import React from 'react';
import styles from './ResponsiveContainer.module.css';

const ResponsiveContainer = ({
  children,
  className = '',
  maxWidth = '1200px',
  padding = 'responsive',
  center = true
}) => {
  const containerClasses = [
    styles.container,
    styles[`padding-${padding}`],
    center ? styles.center : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div 
      className={containerClasses}
      style={{ maxWidth }}
    >
      {children}
    </div>
  );
};

export default ResponsiveContainer;