import React, { useState, useEffect, useContext } from 'react';
import { CheckCircle, Circle, Clock, Target, BookOpen, Trophy, ChevronRight, Flag } from 'lucide-react';
import { AuthContext } from '../../context/AuthContext';
import { updateProjectProgress } from '../../api/projectApi';
import MilestoneTracker from './MilestoneTracker';
import styles from './TaskTracker.module.css';

const TaskTracker = ({ project, onProgressUpdate }) => {
  const { user, token } = useContext(AuthContext);
  const [completedTasks, setCompletedTasks] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [expandedProjects, setExpandedProjects] = useState(new Set());
  const [activeView, setActiveView] = useState('tasks'); // 'tasks' or 'milestones'

  // Initialize completed tasks from project metadata
  useEffect(() => {
    if (project?.project_metadata?.completed_tasks) {
      setCompletedTasks(new Set(project.project_metadata.completed_tasks));
    }
  }, [project]);

  const getProjectTasks = () => {
    if (!project) return [];
    
    // Extract tasks from project steps or learning plan data
    const tasks = [];
    
    if (project.steps && Array.isArray(project.steps)) {
      project.steps.forEach((step, stepIndex) => {
        if (typeof step === 'string') {
          tasks.push({
            id: `step-${stepIndex}`,
            title: step,
            type: 'project',
            projectIndex: stepIndex
          });
        } else if (step.title) {
          tasks.push({
            id: `step-${stepIndex}`,
            title: step.title,
            description: step.description,
            type: 'project',
            projectIndex: stepIndex
          });
          
          // Add sub-tasks if they exist
          if (step.tasks && Array.isArray(step.tasks)) {
            step.tasks.forEach((task, taskIndex) => {
              tasks.push({
                id: `step-${stepIndex}-task-${taskIndex}`,
                title: task,
                type: 'task',
                projectIndex: stepIndex,
                taskIndex: taskIndex,
                isSubTask: true
              });
            });
          }
        }
      });
    }
    
    // If no steps, try to extract from learning plan metadata
    if (tasks.length === 0 && project.project_metadata?.learning_plan_data?.projects) {
      const planProjects = project.project_metadata.learning_plan_data.projects;
      planProjects.forEach((planProject, projectIndex) => {
        if (planProject.tasks && Array.isArray(planProject.tasks)) {
          planProject.tasks.forEach((task, taskIndex) => {
            tasks.push({
              id: `plan-${projectIndex}-task-${taskIndex}`,
              title: task,
              type: 'learning',
              projectIndex: projectIndex,
              taskIndex: taskIndex,
              projectTitle: planProject.title
            });
          });
        }
      });
    }
    
    return tasks;
  };

  const toggleTaskCompletion = async (taskId) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const newCompletedTasks = new Set(completedTasks);
      const wasCompleted = newCompletedTasks.has(taskId);
      
      if (wasCompleted) {
        newCompletedTasks.delete(taskId);
      } else {
        newCompletedTasks.add(taskId);
      }
      
      setCompletedTasks(newCompletedTasks);
      
      // Calculate new progress percentage
      const allTasks = getProjectTasks();
      const completionPercentage = Math.round((newCompletedTasks.size / allTasks.length) * 100);
      
      // Update backend with enhanced metrics
      const progressData = {
        completion_percentage: completionPercentage,
        project_metrics: {
          completed_tasks: Array.from(newCompletedTasks),
          total_tasks: allTasks.length,
          last_updated: new Date().toISOString(),
          completion_rate: completionPercentage / 100,
          tasks_completed_today: 1 // Could be enhanced to track daily completions
        },
        activity_metrics: {
          last_activity: new Date().toISOString(),
          engagement_level: completionPercentage > 75 ? 'high' : completionPercentage > 50 ? 'medium' : 'low'
        },
        learning_metrics: {
          progress_momentum: !wasCompleted ? 'increasing' : 'decreasing',
          consistency_score: Math.min(100, completionPercentage + 10) // Simple consistency metric
        }
      };
      
      await updateProjectProgress(project.id, progressData, user.id, token);
      
      // Notify parent component
      if (onProgressUpdate) {
        onProgressUpdate(project.id, completionPercentage);
      }
      
      // Show completion feedback
      if (!wasCompleted) {
        console.log(`✅ Task completed! Progress: ${completionPercentage}%`);
        // Could add toast notification here
      } else {
        console.log(`↩️ Task unmarked. Progress: ${completionPercentage}%`);
      }
    } catch (error) {
      console.error('Error updating task completion:', error);
      // Revert the change on error
      setCompletedTasks(completedTasks);
    } finally {
      setLoading(false);
    }
  };

  const toggleProjectExpansion = (projectIndex) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectIndex)) {
      newExpanded.delete(projectIndex);
    } else {
      newExpanded.add(projectIndex);
    }
    setExpandedProjects(newExpanded);
  };

  const getTaskIcon = (task, isCompleted) => {
    if (isCompleted) {
      return <CheckCircle className={`${styles.taskIcon} ${styles.completed}`} />;
    }
    
    switch (task.type) {
      case 'learning':
        return <BookOpen className={styles.taskIcon} />;
      case 'project':
        return <Target className={styles.taskIcon} />;
      case 'task':
        return <Circle className={styles.taskIcon} />;
      default:
        return <Circle className={styles.taskIcon} />;
    }
  };

  const getProgressStats = () => {
    const allTasks = getProjectTasks();
    const completed = completedTasks.size;
    const total = allTasks.length;
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    return { completed, total, percentage };
  };

  const groupTasksByProject = () => {
    const tasks = getProjectTasks();
    const grouped = {};
    
    tasks.forEach(task => {
      const projectKey = task.projectTitle || `Project ${task.projectIndex + 1}`;
      if (!grouped[projectKey]) {
        grouped[projectKey] = {
          title: projectKey,
          index: task.projectIndex,
          tasks: []
        };
      }
      grouped[projectKey].tasks.push(task);
    });
    
    return Object.values(grouped);
  };

  if (!project) {
    return (
      <div className={styles.taskTracker}>
        <div className={styles.empty}>
          <Target className={styles.emptyIcon} />
          <p>No project selected</p>
        </div>
      </div>
    );
  }

  const stats = getProgressStats();
  const groupedTasks = groupTasksByProject();

  return (
    <div className={styles.taskTracker}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h3 className={styles.title}>{project.title}</h3>
          <p className={styles.description}>{project.description}</p>
        </div>
        
        <div className={styles.progressSection}>
          <div className={styles.progressCircle}>
            <div className={styles.progressRing}>
              <svg className={styles.progressSvg} viewBox="0 0 36 36">
                <path
                  className={styles.progressBackground}
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={styles.progressForeground}
                  strokeDasharray={`${stats.percentage}, 100`}
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className={styles.progressText}>
                <span className={styles.progressNumber}>{stats.percentage}%</span>
              </div>
            </div>
          </div>
          
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statNumber}>{stats.completed}</span>
              <span className={styles.statLabel}>Completed</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>{stats.total}</span>
              <span className={styles.statLabel}>Total Tasks</span>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.progressVisualization}>
        <div className={styles.progressBar}>
          <div className={styles.progressBarBackground}>
            <div 
              className={styles.progressBarFill}
              style={{ width: `${stats.percentage}%` }}
            />
          </div>
          <div className={styles.progressLabels}>
            <span className={styles.progressLabel}>Progress</span>
            <span className={styles.progressPercentage}>{stats.percentage}%</span>
          </div>
        </div>
        
        <div className={styles.taskBreakdown}>
          <div className={styles.breakdownItem}>
            <div className={styles.breakdownDot} style={{ backgroundColor: '#10b981' }} />
            <span>Completed: {stats.completed}</span>
          </div>
          <div className={styles.breakdownItem}>
            <div className={styles.breakdownDot} style={{ backgroundColor: '#6b7280' }} />
            <span>Remaining: {stats.total - stats.completed}</span>
          </div>
        </div>
      </div>

      <div className={styles.viewTabs}>
        <button 
          className={`${styles.viewTab} ${activeView === 'tasks' ? styles.activeViewTab : ''}`}
          onClick={() => setActiveView('tasks')}
        >
          <BookOpen className={styles.tabIcon} />
          Detailed Tasks
        </button>
        <button 
          className={`${styles.viewTab} ${activeView === 'milestones' ? styles.activeViewTab : ''}`}
          onClick={() => setActiveView('milestones')}
        >
          <Flag className={styles.tabIcon} />
          Milestones
        </button>
      </div>

      {activeView === 'tasks' && (
        <div className={styles.taskGroups}>
          {groupedTasks.map((group, groupIndex) => (
            <div key={groupIndex} className={styles.taskGroup}>
              <div 
                className={styles.groupHeader}
                onClick={() => toggleProjectExpansion(group.index)}
              >
                <div className={styles.groupTitle}>
                  <ChevronRight 
                    className={`${styles.chevron} ${expandedProjects.has(group.index) ? styles.expanded : ''}`} 
                  />
                  <span>{group.title}</span>
                </div>
                <div className={styles.groupProgress}>
                  {group.tasks.filter(task => completedTasks.has(task.id)).length} / {group.tasks.length}
                </div>
              </div>
              
              {expandedProjects.has(group.index) && (
                <div className={styles.taskList}>
                  {group.tasks.map((task) => {
                    const isCompleted = completedTasks.has(task.id);
                    return (
                      <div
                        key={task.id}
                        className={`${styles.taskItem} ${isCompleted ? styles.completedTask : ''} ${task.isSubTask ? styles.subTask : ''}`}
                        onClick={() => toggleTaskCompletion(task.id)}
                      >
                        <div className={styles.taskContent}>
                          {getTaskIcon(task, isCompleted)}
                          <div className={styles.taskDetails}>
                            <span className={styles.taskTitle}>{task.title}</span>
                            {task.description && (
                              <span className={styles.taskDescription}>{task.description}</span>
                            )}
                          </div>
                        </div>
                        {isCompleted && (
                          <Trophy className={styles.completionBadge} />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeView === 'milestones' && (
        <MilestoneTracker 
          project={project}
          onMilestoneUpdate={(projectId, percentage, completedCount) => {
            if (onProgressUpdate) {
              onProgressUpdate(projectId, percentage);
            }
          }}
        />
      )}

      {stats.percentage === 100 && activeView === 'tasks' && (
        <div className={styles.completionCelebration}>
          <Trophy className={styles.celebrationIcon} />
          <h4>Congratulations!</h4>
          <p>You've completed this project! 🎉</p>
          <div className={styles.completionActions}>
            <div className={styles.learningAssessment}>
              <h5>What you've accomplished:</h5>
              <ul className={styles.accomplishmentsList}>
                <li>Completed {stats.total} learning tasks</li>
                <li>Gained hands-on experience in {project.domain || 'your chosen field'}</li>
                <li>Developed practical skills through project-based learning</li>
              </ul>
            </div>
            <div className={styles.nextStepsSection}>
              <h5>Recommended next steps:</h5>
              <div className={styles.nextStepsGrid}>
                <div className={styles.nextStepCard}>
                  <BookOpen className={styles.nextStepIcon} />
                  <span>Explore advanced topics in {project.domain || 'this area'}</span>
                </div>
                <div className={styles.nextStepCard}>
                  <Target className={styles.nextStepIcon} />
                  <span>Start a more challenging project</span>
                </div>
                <div className={styles.nextStepCard}>
                  <Trophy className={styles.nextStepIcon} />
                  <span>Share your project with the community</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskTracker;