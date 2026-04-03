import React, { useState, useEffect, useContext } from 'react';
import { CheckCircle, Circle, Flag, Calendar, Award, TrendingUp, BookOpen, Target } from 'lucide-react';
import { AuthContext } from '../../context/AuthContext';
import { updateProjectProgress } from '../../api/projectApi';
import styles from './MilestoneTracker.module.css';

const MilestoneTracker = ({ project, onMilestoneUpdate }) => {
  const { user, token } = useContext(AuthContext);
  const [completedMilestones, setCompletedMilestones] = useState(new Set());
  const [loading, setLoading] = useState(false);

  // Initialize completed milestones from project metadata
  useEffect(() => {
    if (project?.project_metadata?.completed_milestones) {
      setCompletedMilestones(new Set(project.project_metadata.completed_milestones));
    }
  }, [project]);

  const getMilestones = () => {
    if (!project) return [];
    
    const milestones = [];
    
    // Extract milestones from project steps or learning plan data
    if (project.steps && Array.isArray(project.steps)) {
      project.steps.forEach((step, index) => {
        if (typeof step === 'string') {
          milestones.push({
            id: `milestone-${index}`,
            title: step,
            description: `Complete ${step}`,
            type: 'project',
            order: index,
            estimatedWeeks: Math.ceil((index + 1) * 1.5)
          });
        } else if (step.title) {
          milestones.push({
            id: `milestone-${index}`,
            title: step.title,
            description: step.description || `Complete ${step.title}`,
            type: 'project',
            order: index,
            estimatedWeeks: step.weeks ? parseInt(step.weeks.split('-')[1] || step.weeks) : Math.ceil((index + 1) * 1.5),
            skills: step.skills || [],
            resources: step.resources || []
          });
        }
      });
    }
    
    // If no steps, try to extract from learning plan metadata
    if (milestones.length === 0 && project.project_metadata?.learning_plan_data?.projects) {
      const planProjects = project.project_metadata.learning_plan_data.projects;
      planProjects.forEach((planProject, index) => {
        milestones.push({
          id: `plan-milestone-${index}`,
          title: planProject.title,
          description: planProject.description || `Complete ${planProject.title}`,
          type: 'learning',
          order: index,
          estimatedWeeks: planProject.weeks ? parseInt(planProject.weeks.split('-')[1] || planProject.weeks) : Math.ceil((index + 1) * 2),
          skills: planProject.skills || [],
          resources: planProject.resources || [],
          funFactor: planProject.fun_factor
        });
      });
    }
    
    return milestones.sort((a, b) => a.order - b.order);
  };

  const toggleMilestoneCompletion = async (milestoneId) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const newCompletedMilestones = new Set(completedMilestones);
      const wasCompleted = newCompletedMilestones.has(milestoneId);
      
      if (wasCompleted) {
        newCompletedMilestones.delete(milestoneId);
      } else {
        newCompletedMilestones.add(milestoneId);
      }
      
      setCompletedMilestones(newCompletedMilestones);
      
      // Calculate new progress percentage based on milestones
      const allMilestones = getMilestones();
      const completionPercentage = Math.round((newCompletedMilestones.size / allMilestones.length) * 100);
      
      // Update backend with enhanced milestone metrics
      const progressData = {
        completion_percentage: completionPercentage,
        project_metrics: {
          completed_milestones: Array.from(newCompletedMilestones),
          total_milestones: allMilestones.length,
          milestone_completion_date: new Date().toISOString(),
          milestone_completion_rate: completionPercentage / 100,
          milestones_completed_this_week: 1 // Could be enhanced to track weekly completions
        },
        activity_metrics: {
          last_milestone_activity: new Date().toISOString(),
          milestone_engagement: completionPercentage > 75 ? 'excellent' : completionPercentage > 50 ? 'good' : 'needs_improvement'
        },
        learning_metrics: {
          milestone_momentum: !wasCompleted ? 'accelerating' : 'decelerating',
          learning_depth: Math.min(100, completionPercentage * 1.2), // Enhanced learning depth metric
          skill_development_score: completionPercentage + (newCompletedMilestones.size * 5) // Bonus for each milestone
        }
      };
      
      await updateProjectProgress(project.id, progressData, user.id, token);
      
      // Notify parent component
      if (onMilestoneUpdate) {
        onMilestoneUpdate(project.id, completionPercentage, newCompletedMilestones.size);
      }
      
      // Show milestone completion feedback
      if (!wasCompleted) {
        console.log(`🎯 Milestone achieved! Progress: ${completionPercentage}%`);
        // Could add celebration animation or toast notification here
      } else {
        console.log(`↩️ Milestone unmarked. Progress: ${completionPercentage}%`);
      }
    } catch (error) {
      console.error('Error updating milestone completion:', error);
      // Revert the change on error
      setCompletedMilestones(completedMilestones);
    } finally {
      setLoading(false);
    }
  };

  const getProgressStats = () => {
    const allMilestones = getMilestones();
    const completed = completedMilestones.size;
    const total = allMilestones.length;
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    return { completed, total, percentage };
  };

  const getEstimatedTimeRemaining = () => {
    const milestones = getMilestones();
    const remainingMilestones = milestones.filter(m => !completedMilestones.has(m.id));
    
    if (remainingMilestones.length === 0) return 'Completed!';
    
    const totalWeeks = remainingMilestones.reduce((sum, milestone) => sum + (milestone.estimatedWeeks || 2), 0);
    
    if (totalWeeks < 1) return '< 1 week';
    if (totalWeeks === 1) return '1 week';
    if (totalWeeks < 4) return `${totalWeeks} weeks`;
    
    const months = Math.round(totalWeeks / 4);
    return `${months} month${months > 1 ? 's' : ''}`;
  };

  const getNextMilestone = () => {
    const milestones = getMilestones();
    return milestones.find(m => !completedMilestones.has(m.id));
  };

  if (!project) {
    return (
      <div className={styles.milestoneTracker}>
        <div className={styles.empty}>
          <Flag className={styles.emptyIcon} />
          <p>No project selected</p>
        </div>
      </div>
    );
  }

  const stats = getProgressStats();
  const milestones = getMilestones();
  const nextMilestone = getNextMilestone();

  return (
    <div className={styles.milestoneTracker}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h3 className={styles.title}>Project Milestones</h3>
          <p className={styles.subtitle}>{project.title}</p>
        </div>
        
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <Award className={styles.statIcon} />
            <div className={styles.statContent}>
              <span className={styles.statNumber}>{stats.completed}</span>
              <span className={styles.statLabel}>Completed</span>
            </div>
          </div>
          
          <div className={styles.statCard}>
            <Flag className={styles.statIcon} />
            <div className={styles.statContent}>
              <span className={styles.statNumber}>{stats.total}</span>
              <span className={styles.statLabel}>Total</span>
            </div>
          </div>
          
          <div className={styles.statCard}>
            <TrendingUp className={styles.statIcon} />
            <div className={styles.statContent}>
              <span className={styles.statNumber}>{stats.percentage}%</span>
              <span className={styles.statLabel}>Progress</span>
            </div>
          </div>
          
          <div className={styles.statCard}>
            <Calendar className={styles.statIcon} />
            <div className={styles.statContent}>
              <span className={styles.statNumber}>{getEstimatedTimeRemaining()}</span>
              <span className={styles.statLabel}>Remaining</span>
            </div>
          </div>
        </div>
      </div>

      {nextMilestone && (
        <div className={styles.nextMilestone}>
          <div className={styles.nextMilestoneHeader}>
            <Flag className={styles.nextMilestoneIcon} />
            <h4>Next Milestone</h4>
          </div>
          <div className={styles.nextMilestoneContent}>
            <h5>{nextMilestone.title}</h5>
            <p>{nextMilestone.description}</p>
            {nextMilestone.funFactor && (
              <div className={styles.funFactor}>
                <strong>Why it's engaging:</strong> {nextMilestone.funFactor}
              </div>
            )}
            <button 
              className={styles.startButton}
              onClick={() => toggleMilestoneCompletion(nextMilestone.id)}
              disabled={loading}
            >
              {loading ? 'Updating...' : 'Mark as Complete'}
            </button>
          </div>
        </div>
      )}

      <div className={styles.milestoneList}>
        <h4 className={styles.sectionTitle}>All Milestones</h4>
        <div className={styles.timeline}>
          {milestones.map((milestone, index) => {
            const isCompleted = completedMilestones.has(milestone.id);
            const isNext = nextMilestone && nextMilestone.id === milestone.id;
            
            return (
              <div
                key={milestone.id}
                className={`${styles.milestoneItem} ${isCompleted ? styles.completed : ''} ${isNext ? styles.next : ''}`}
                onClick={() => toggleMilestoneCompletion(milestone.id)}
              >
                <div className={styles.milestoneMarker}>
                  {isCompleted ? (
                    <CheckCircle className={styles.milestoneIcon} />
                  ) : (
                    <Circle className={styles.milestoneIcon} />
                  )}
                  {index < milestones.length - 1 && (
                    <div className={`${styles.timelineLine} ${isCompleted ? styles.completedLine : ''}`} />
                  )}
                </div>
                
                <div className={styles.milestoneContent}>
                  <div className={styles.milestoneHeader}>
                    <h5 className={styles.milestoneTitle}>{milestone.title}</h5>
                    <span className={styles.milestoneTime}>
                      ~{milestone.estimatedWeeks} week{milestone.estimatedWeeks !== 1 ? 's' : ''}
                    </span>
                  </div>
                  
                  <p className={styles.milestoneDescription}>{milestone.description}</p>
                  
                  {milestone.skills && milestone.skills.length > 0 && (
                    <div className={styles.milestoneSkills}>
                      <strong>Skills:</strong>
                      <div className={styles.skillTags}>
                        {milestone.skills.slice(0, 3).map((skill, skillIndex) => (
                          <span key={skillIndex} className={styles.skillTag}>
                            {skill}
                          </span>
                        ))}
                        {milestone.skills.length > 3 && (
                          <span className={styles.skillTag}>
                            +{milestone.skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {isCompleted && (
                    <div className={styles.completionBadge}>
                      <Award className={styles.badgeIcon} />
                      <span>Completed!</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {stats.percentage === 100 && (
        <div className={styles.projectCompletion}>
          <Award className={styles.completionIcon} />
          <h4>Project Complete! 🎉</h4>
          <p>Congratulations on completing all milestones!</p>
          <div className={styles.completionSummary}>
            <div className={styles.achievementSummary}>
              <h5>Your achievements:</h5>
              <div className={styles.achievementGrid}>
                <div className={styles.achievementItem}>
                  <Flag className={styles.achievementIcon} />
                  <span>{stats.total} milestones completed</span>
                </div>
                <div className={styles.achievementItem}>
                  <Calendar className={styles.achievementIcon} />
                  <span>Project timeline mastered</span>
                </div>
                <div className={styles.achievementItem}>
                  <TrendingUp className={styles.achievementIcon} />
                  <span>Consistent progress maintained</span>
                </div>
              </div>
            </div>
            <div className={styles.nextJourney}>
              <h5>Continue your learning journey:</h5>
              <div className={styles.journeyOptions}>
                <button className={styles.journeyButton}>
                  <BookOpen className={styles.journeyIcon} />
                  <div>
                    <strong>Advanced Learning</strong>
                    <span>Explore deeper topics</span>
                  </div>
                </button>
                <button className={styles.journeyButton}>
                  <Target className={styles.journeyIcon} />
                  <div>
                    <strong>New Challenge</strong>
                    <span>Start a harder project</span>
                  </div>
                </button>
                <button className={styles.journeyButton}>
                  <Award className={styles.journeyIcon} />
                  <div>
                    <strong>Share Success</strong>
                    <span>Showcase your work</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MilestoneTracker;