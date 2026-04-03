import React from 'react';
import TaskCard from '../MainContent/TaskCard';
import styles from './LearningPlan.module.css';

const LearningPlan = ({ plan }) => {
  if (!plan) {
    return (
      <div className={styles.learningPlan}>
        <div className={styles.empty}>
          <h2>No Learning Plan Selected</h2>
          <p>Start a conversation with the AI to create a personalized learning plan.</p>
        </div>
      </div>
    );
  }

  const formatTasks = (tasks, concepts = [], category) => {
    return tasks.map((task, index) => ({
      type: category,
      title: task,
      description: concepts[index] || '',
      completed: false,
      category: category === 'daily' ? 'learning' : category === 'weekly' ? 'coding' : 'project'
    }));
  };

  // Handle both new and old plan formats
  const getDailyTasks = () => {
    if (plan.timeline?.daily?.[0]?.tasks) {
      return formatTasks(
        plan.timeline.daily[0].tasks,
        plan.timeline.daily[0].learning_concepts,
        'daily'
      );
    }
    return formatTasks(
      plan.milestones || [],
      [],
      'daily'
    );
  };

  const getWeeklyTasks = () => {
    if (plan.timeline?.weekly?.[0]?.milestones) {
      return formatTasks(
        plan.timeline.weekly[0].milestones,
        Array(plan.timeline.weekly[0].milestones.length).fill('Weekly Milestone'),
        'weekly'
      );
    }
    return [];
  };

  const getMonthlyTasks = () => {
    if (plan.timeline?.monthly?.final_objectives) {
      return formatTasks(
        plan.timeline.monthly.final_objectives,
        Array(plan.timeline.monthly.final_objectives.length).fill('Monthly Objective'),
        'monthly'
      );
    }
    return [];
  };

  const dailyTasks = getDailyTasks();
  const weeklyTasks = getWeeklyTasks();
  const monthlyTasks = getMonthlyTasks();

  return (
    <div className={styles.learningPlan}>
      <header className={styles.header}>
        <h1>{plan.title}</h1>
        <p className={styles.overview}>{plan.overview}</p>
      </header>

      {plan.prerequisites && (
        <div className={styles.prerequisites}>
          <h2>Prerequisites</h2>
          <ul className={styles.prerequisitesList}>
            {plan.prerequisites.required.map((req, index) => (
              <li key={index}>{req}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.timeline}>
        <TaskCard
          title="Daily Tasks"
          date={new Date().toLocaleDateString()}
          tasks={dailyTasks}
          type="daily"
        />
        {weeklyTasks.length > 0 && (
          <TaskCard
            title="Weekly Milestones"
            date="This Week"
            tasks={weeklyTasks}
            type="weekly"
          />
        )}
        {monthlyTasks.length > 0 && (
          <TaskCard
            title="Monthly Objectives"
            date="This Month"
            tasks={monthlyTasks}
            type="monthly"
          />
        )}
      </div>
    </div>
  );
};

export default LearningPlan;