// src/components/MainContent/TaskCard.js
import React, { useState, useEffect } from 'react';
import { Book, Code, Target, CheckCircle, Circle } from 'lucide-react';
import styles from './TaskCard.module.css';

const TaskCard = ({ title, date, tasks, type }) => {
  // Initialize from localStorage if available
  const [completedTasks, setCompletedTasks] = useState(() => {
    const saved = localStorage.getItem(`upskillmee_completed_tasks_${type}`);
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  // Save to localStorage whenever completedTasks changes
  useEffect(() => {
    localStorage.setItem(
      `upskillmee_completed_tasks_${type}`, 
      JSON.stringify(Array.from(completedTasks))
    );
  }, [completedTasks, type]);

  const toggleTaskCompletion = (index) => {
    setCompletedTasks(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const getTaskIcon = (taskType) => {
    switch(taskType) {
      case 'learning': return <Book className={styles.icon} />;
      case 'coding': return <Code className={styles.icon} />;
      case 'project': return <Target className={styles.icon} />;
      default: return <Circle className={styles.icon} />;
    }
  };

  return (
    <div className={styles.taskCard}>
      <div className={styles.taskHeader}>
        <h2>{title}</h2>
        <div className={styles.taskDate}>{date}</div>
      </div>
      {tasks.length === 0 && (
        <div className={styles.noTasks}>No tasks available</div>
      )}
      {tasks.map((task, index) => (
        <div 
          className={`${styles.taskItem} ${completedTasks.has(index) ? styles.completed : ''}`} 
          key={index}
          onClick={() => toggleTaskCompletion(index)}
        >
          <div className={styles.taskIconWrapper}>
            {completedTasks.has(index) ? 
              <CheckCircle className={`${styles.icon} ${styles.completed}`} /> : 
              getTaskIcon(task.category || 'learning')
            }
          </div>
          <div className={styles.taskDetails}>
            <div className={styles.taskTitle}>{task.title}</div>
            {task.description && (
              <div className={styles.taskDescription}>{task.description}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TaskCard;