import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock, BookOpen, Target, Users, Calendar } from 'lucide-react';
import styles from './ProjectCard.module.css';

const ProjectCard = ({ 
  project, 
  onAccept, 
  onReject, 
  onViewDetails, 
  isLearningPlan = false,
  showActions = true 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAccept = async () => {
    setIsLoading(true);
    try {
      await onAccept(project);
    } catch (error) {
      console.error('Error accepting project:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    setIsLoading(true);
    try {
      await onReject(project);
    } catch (error) {
      console.error('Error rejecting project:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'accepted':
      case 'in_progress':
        return styles.statusAccepted;
      case 'completed':
        return styles.statusCompleted;
      case 'rejected':
        return styles.statusRejected;
      case 'pending':
      default:
        return styles.statusPending;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'accepted':
      case 'in_progress':
        return <Clock className={styles.statusIcon} />;
      case 'completed':
        return <CheckCircle className={styles.statusIcon} />;
      case 'rejected':
        return <XCircle className={styles.statusIcon} />;
      case 'pending':
      default:
        return <BookOpen className={styles.statusIcon} />;
    }
  };

  const formatDifficulty = (difficulty) => {
    if (!difficulty) return 'Beginner';
    return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
  };

  const getProjectCount = () => {
    if (project.projects && Array.isArray(project.projects)) {
      return project.projects.length;
    }
    if (project.steps && Array.isArray(project.steps)) {
      return project.steps.length;
    }
    return 0;
  };

  const getEstimatedTime = () => {
    const projectCount = getProjectCount();
    if (projectCount === 0) return 'Unknown';
    
    // Estimate 1-2 weeks per project
    const weeks = projectCount * 1.5;
    if (weeks < 1) return '< 1 week';
    if (weeks === 1) return '1 week';
    if (weeks < 4) return `${Math.round(weeks)} weeks`;
    
    const months = Math.round(weeks / 4);
    return `${months} month${months > 1 ? 's' : ''}`;
  };

  return (
    <div className={`${styles.projectCard} ${isLearningPlan ? styles.learningPlan : ''}`}>
      <div className={styles.cardHeader}>
        <div className={styles.titleSection}>
          <h3 className={styles.title}>{project.title}</h3>
          {!isLearningPlan && (
            <div className={`${styles.status} ${getStatusColor(project.status)}`}>
              {getStatusIcon(project.status)}
              <span>{project.status?.replace('_', ' ') || 'pending'}</span>
            </div>
          )}
        </div>
        {project.difficulty && (
          <div className={styles.difficulty}>
            <Target className={styles.difficultyIcon} />
            <span>{formatDifficulty(project.difficulty)}</span>
          </div>
        )}
      </div>

      <div className={styles.cardBody}>
        <p className={styles.description}>
          {project.description || 'No description available'}
        </p>

        <div className={styles.metadata}>
          <div className={styles.metadataItem}>
            <BookOpen className={styles.metadataIcon} />
            <span>{getProjectCount()} projects</span>
          </div>
          <div className={styles.metadataItem}>
            <Calendar className={styles.metadataIcon} />
            <span>{getEstimatedTime()}</span>
          </div>
          {project.domain && (
            <div className={styles.metadataItem}>
              <Users className={styles.metadataIcon} />
              <span>{project.domain}</span>
            </div>
          )}
        </div>

        {isExpanded && (
          <div className={styles.expandedContent}>
            <h4>Projects in this plan:</h4>
            <ul className={styles.projectList}>
              {(project.projects || project.steps || []).slice(0, 5).map((item, index) => (
                <li key={index} className={styles.projectItem}>
                  {typeof item === 'string' ? item : item.title || `Project ${index + 1}`}
                </li>
              ))}
              {getProjectCount() > 5 && (
                <li className={styles.projectItem}>
                  ... and {getProjectCount() - 5} more projects
                </li>
              )}
            </ul>
          </div>
        )}
      </div>

      <div className={styles.cardFooter}>
        <button 
          className={styles.detailsButton}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Show Less' : 'Show Details'}
        </button>

        {showActions && isLearningPlan && (
          <div className={styles.actions}>
            <button 
              className={`${styles.actionButton} ${styles.rejectButton}`}
              onClick={handleReject}
              disabled={isLoading}
            >
              <XCircle className={styles.actionIcon} />
              {isLoading ? 'Processing...' : 'Not Interested'}
            </button>
            <button 
              className={`${styles.actionButton} ${styles.acceptButton}`}
              onClick={handleAccept}
              disabled={isLoading}
            >
              <CheckCircle className={styles.actionIcon} />
              {isLoading ? 'Processing...' : 'Start Learning'}
            </button>
          </div>
        )}

        {!isLearningPlan && project.status === 'accepted' && (
          <div className={styles.progressSection}>
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ width: `${project.completion_percentage || 0}%` }}
              />
            </div>
            <span className={styles.progressText}>
              {project.completion_percentage || 0}% complete
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;