// src/pages/Dashboard/Dashboard.js
import React, { useState, useEffect } from 'react';
import { useLearningPlan } from '../../pages/Chat/context/LearningPlanContext';
import styles from './Dashboard.module.css';
import LearningProgress  from '../../components/LearningPlan/LearningProgress';
import TasksList from '../../components/MainContent/TasksList';
import SkillMap from '../../components/SkillMap/SkillMap';
import { useTheme } from '../../context/ThemeContext';
import FeedbackButton from '../../components/Feedback/FeedbackButton';
import ReferralWidget from '../../components/Referral/ReferralWidget';

const generateTasks = (project) => {
  return {
    daily: project?.tasks?.map(task => ({
      title: task,
      completed: false
    })) || [],
    weekly: project?.weekly_goals?.map(goal => ({
      title: goal,
      completed: false
    })) || [],
    monthly: project?.milestones?.map(milestone => ({
      title: milestone,
      completed: false
    })) || []
  };
};

const Dashboard = () => {
  const {theme}=useTheme();

  const { projects } = useLearningPlan();
  const [tasks, setTasks] = useState({
    daily: [],
    weekly: [],
    monthly: []
  });

  useEffect(() => {
    if (projects && projects.length > 0) {
      const generatedTasks = generateTasks(projects[0]);
      setTasks(generatedTasks);
    }
  }, [projects]);

  return (
    <div className={`${styles.dashboard} ${
            theme === "dark" ? styles.dark : styles.light
          }`}>
        <LearningProgress/>
        <SkillMap/>
        <TasksList/>
        <ReferralWidget/>
        <FeedbackButton position="bottom-right" variant="floating"/>
    </div>
  );
};

export default Dashboard;