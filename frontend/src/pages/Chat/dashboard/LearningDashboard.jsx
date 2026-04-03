import React from 'react';
import { useLearningPlan } from '../context/LearningPlanContext';
import styles from './LearningDashboard.module.css';

const LearningDashboard = () => {
  const { projects } = useLearningPlan();
  const today = new Date();

  // Get current project (first project for now, can be enhanced with date logic later)
  const getCurrentProject = () => {
    return projects && projects.length > 0 ? projects[0] : null;
  };

  // Generate daily tasks from current project
  const getCurrentWeekTasks = () => {
    const currentProject = getCurrentProject();
    if (!currentProject || !currentProject.tasks) return [];
    
    // Break down weekly tasks into daily tasks
    return currentProject.tasks.map(task => ({
      title: task,
      completed: false
    }));
  };

  // Get current sprint (current project focus)
  const getCurrentSprint = () => {
    return getCurrentProject();
  };

  const dailyTasks = getCurrentWeekTasks();
  const currentSprint = getCurrentSprint();

  return (
    <div className={styles.dashboard}>
      {/* Today's Tasks */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Today's Tasks</h2>
        <div className={styles.date}>
          {today.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
        <div className={styles.taskList}>
          {dailyTasks.map((task, index) => (
            <div key={index} className={styles.task}>
              <input type="checkbox" checked={task.completed} />
              <span>{task.title}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Current Sprint */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Current Sprint</h2>
        {currentSprint && (
          <>
            <h3 className={styles.sprintTitle}>{currentSprint.title}</h3>
            <p className={styles.sprintDescription}>{currentSprint.description}</p>
            <div className={styles.skillTags}>
              {currentSprint.skills && currentSprint.skills.map((skill, index) => (
                <span key={index} className={styles.skillTag}>{skill}</span>
              ))}
            </div>
          </>
        )}
      </section>

      {/* Complete Learning Plan */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Your Learning Plan</h2>
        <div className={styles.timeline}>
          {projects && projects.map((project, index) => (
            <div 
              key={index} 
              className={`${styles.timelineItem} ${
                index === 0 ? styles.current : ''
              }`}
            >
              <div className={styles.timelineWeek}>
                {index === 0 ? 'Current Week' : `Week ${index + 1}`}
              </div>
              <div className={styles.timelineTitle}>{project.title}</div>
              {project.description && (
                <div className={styles.timelineDescription}>{project.description}</div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default LearningDashboard;
