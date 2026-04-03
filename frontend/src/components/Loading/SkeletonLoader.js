import React from 'react';
import styles from './Loading.module.css';

const SkeletonLoader = ({ 
  variant = 'text',
  width = '100%',
  height = null,
  lines = 1,
  className = '',
  animation = true,
  responsive = true
}) => {
  const skeletonClass = `${styles.skeleton} ${animation ? styles.skeletonAnimated : ''} ${responsive ? styles.responsive : ''} ${className}`;
  
  // Default heights for different variants with responsive support
  const getHeight = () => {
    if (height) return height;
    
    switch (variant) {
      case 'text':
        return responsive ? 'clamp(0.875rem, 2vw, 1rem)' : '1rem';
      case 'title':
        return responsive ? 'clamp(1.25rem, 3vw, 1.5rem)' : '1.5rem';
      case 'subtitle':
        return responsive ? 'clamp(1.125rem, 2.5vw, 1.25rem)' : '1.25rem';
      case 'avatar':
        return responsive ? 'clamp(2.5rem, 6vw, 3rem)' : '3rem';
      case 'button':
        return responsive ? 'clamp(2.25rem, 5vw, 2.5rem)' : '2.5rem';
      case 'card':
        return responsive ? 'clamp(10rem, 25vw, 12rem)' : '12rem';
      case 'image':
        return responsive ? 'clamp(6rem, 20vw, 8rem)' : '8rem';
      default:
        return responsive ? 'clamp(0.875rem, 2vw, 1rem)' : '1rem';
    }
  };

  const getBorderRadius = () => {
    switch (variant) {
      case 'avatar':
        return '50%';
      case 'button':
        return 'var(--radius-lg)';
      case 'card':
      case 'image':
        return 'var(--radius-xl)';
      default:
        return 'var(--radius-md)';
    }
  };

  const skeletonStyle = {
    width,
    height: getHeight(),
    borderRadius: getBorderRadius()
  };

  // For multiple lines of text
  if (variant === 'text' && lines > 1) {
    return (
      <div className={styles.skeletonGroup}>
        {Array.from({ length: lines }, (_, index) => (
          <div
            key={index}
            className={skeletonClass}
            style={{
              ...skeletonStyle,
              width: index === lines - 1 ? '75%' : width, // Last line is shorter
              marginBottom: index < lines - 1 ? 'var(--space-2)' : 0
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={skeletonClass}
      style={skeletonStyle}
    />
  );
};

// Predefined skeleton layouts
export const MessageSkeleton = () => (
  <div className={styles.messageSkeleton}>
    <SkeletonLoader variant="avatar" width="2.5rem" height="2.5rem" />
    <div className={styles.messageContent}>
      <SkeletonLoader variant="text" lines={2} />
    </div>
  </div>
);

export const ProjectCardSkeleton = () => (
  <div className={styles.projectCardSkeleton}>
    <SkeletonLoader variant="image" height="8rem" />
    <div className={styles.cardContent}>
      <SkeletonLoader variant="title" width="80%" />
      <SkeletonLoader variant="text" lines={3} />
      <div className={styles.cardActions}>
        <SkeletonLoader variant="button" width="6rem" />
        <SkeletonLoader variant="button" width="6rem" />
      </div>
    </div>
  </div>
);

export const DashboardSkeleton = () => (
  <div className={styles.dashboardSkeleton}>
    <div className={styles.headerSkeleton}>
      <SkeletonLoader variant="title" width="60%" />
      <SkeletonLoader variant="subtitle" width="40%" />
    </div>
    
    <div className={styles.statsSkeleton}>
      {Array.from({ length: 3 }, (_, index) => (
        <div key={index} className={styles.statCardSkeleton}>
          <SkeletonLoader variant="avatar" width="3rem" height="3rem" />
          <div>
            <SkeletonLoader variant="title" width="3rem" />
            <SkeletonLoader variant="text" width="5rem" />
          </div>
        </div>
      ))}
    </div>
    
    <div className={styles.contentSkeleton}>
      {Array.from({ length: 2 }, (_, index) => (
        <ProjectCardSkeleton key={index} />
      ))}
    </div>
  </div>
);

export default SkeletonLoader;