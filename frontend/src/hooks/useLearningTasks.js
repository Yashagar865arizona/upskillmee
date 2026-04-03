import { useState, useEffect } from 'react';

export function useLearningTasks(projects) {
  const [tasks, setTasks] = useState({
    daily: [],
    weekly: [],
    monthly: []
  });
  const [progress, setProgress] = useState({
    daily: 0,
    weekly: 0,
    monthly: 0
  });

  // Update tasks when learning plan changes
  useEffect(() => {
    if (!projects?.length) return;

    console.log('useLearningTasks: Updating tasks from learning plan:', projects);
    const today = new Date();
    const startDate = new Date(projects[0].startDate || today);
    const currentWeekIndex = Math.floor((today - startDate) / (7 * 24 * 60 * 60 * 1000));
    
    // Get current week's project
    const currentProject = projects[currentWeekIndex] || projects[0];

    // Convert learning plan into task format
    const newTasks = {
      daily: currentProject.tasks.map(task => ({
        type: 'daily',
        title: task,
        description: '',
        completed: false,
        category: 'learning'
      })),
      weekly: projects.slice(currentWeekIndex, currentWeekIndex + 2).flatMap(project => 
        project ? [{
          type: 'weekly',
          title: project.title,
          description: project.description,
          completed: false,
          category: 'project'
        }] : []
      ),
      monthly: projects.slice(0, 4).map(project => ({
        type: 'monthly',
        title: project.title,
        description: project.description,
        completed: false,
        category: 'project'
      }))
    };

    setTasks(newTasks);
  }, [projects]);

  const toggleTaskCompletion = (taskType, taskIndex) => {
    setTasks(prev => {
      const newTasks = { ...prev };
      if (newTasks[taskType] && newTasks[taskType][taskIndex]) {
        newTasks[taskType] = [...newTasks[taskType]];
        newTasks[taskType][taskIndex] = {
          ...newTasks[taskType][taskIndex],
          completed: !newTasks[taskType][taskIndex].completed,
          completedAt: !newTasks[taskType][taskIndex].completed ? new Date().toISOString() : null
        };
      }
      return newTasks;
    });

    // Update progress
    setProgress(prev => {
      const newProgress = { ...prev };
      const taskList = tasks[taskType] || [];
      if (taskList.length > 0) {
        const completedCount = taskList.filter(task => task.completed).length;
        newProgress[taskType] = (completedCount / taskList.length) * 100;
      }
      return newProgress;
    });
  };

  return { tasks, progress, toggleTaskCompletion };
}
