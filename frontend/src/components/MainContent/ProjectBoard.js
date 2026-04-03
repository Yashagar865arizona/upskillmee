import React, { useState, useEffect, useContext } from 'react';
import { Plus, BookOpen, Target, Clock, CheckCircle, List } from 'lucide-react';
import ProjectCard from './ProjectCard';
import TaskTracker from './TaskTracker';
import { AuthContext } from '../../context/AuthContext';
import { getUserProjects, createProjectFromPlan, updateProjectStatus, getUserLearningPlans } from '../../api/projectApi';
import styles from './ProjectBoard.module.css';

const ProjectBoard = () => {
  const { user, token } = useContext(AuthContext);
  const [learningPlans, setLearningPlans] = useState([]);
  const [userProjects, setUserProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('plans'); // 'plans', 'projects', or 'tasks'
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    if (user && token) {
      loadData();
    }
  }, [user, token]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load both learning plans and user projects
      const [plansData, projectsData] = await Promise.all([
        getUserLearningPlans(user.id, token),
        getUserProjects(user.id, token)
      ]);

      console.log('Loaded learning plans:', plansData);
      console.log('Loaded user projects:', projectsData);

      setLearningPlans(Array.isArray(plansData) ? plansData : []);
      setUserProjects(Array.isArray(projectsData) ? projectsData : []);
    } catch (error) {
      console.error('Error loading project data:', error);
      setError('Failed to load projects. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // const handleAcceptPlan = async (plan) => {
  //   try {
  //     console.log('Accepting learning plan:', plan);
      
  //     // Create a new project from the learning plan
  //     const newProject = await createProjectFromPlan(plan, user.id, token);
      
  //     // Add to user projects
  //     setUserProjects(prev => [...prev, newProject]);
      
  //     // Remove from learning plans (or mark as accepted)
  //     setLearningPlans(prev => prev.filter(p => p.id !== plan.id));
      
  //     console.log('Successfully accepted learning plan and created project');
  //   } catch (error) {
  //     console.error('Error accepting plan:', error);
  //     setError('Failed to accept learning plan. Please try again.');
  //   }
  // };
const handleAcceptPlan = async (plan) => {
  try {
    console.log('Accepting learning plan:', plan);
    
    // Create a new project from the learning plan
    const newProject = await createProjectFromPlan(plan, user.id, token);

    // Make sure tasks array exists (use plan.tasks if backend doesn’t return them immediately)
    const projectWithTasks = {
      ...newProject,
      tasks: newProject.tasks?.length ? newProject.tasks : plan.tasks || []
    };
    
    // Add to user projects
    setUserProjects(prev => [...prev, projectWithTasks]);
    
    // Remove from learning plans
    setLearningPlans(prev => prev.filter(p => p.id !== plan.id));
    
    console.log('Successfully accepted learning plan and created project');
  } catch (error) {
    console.error('Error accepting plan:', error);
    setError('Failed to accept learning plan. Please try again.');
  }
};

  const handleRejectPlan = async (plan) => {
    try {
      console.log('Rejecting learning plan:', plan);
      
      // For now, just remove from the list
      // In the future, we might want to save this preference
      setLearningPlans(prev => prev.filter(p => p.id !== plan.id));
      
      console.log('Successfully rejected learning plan');
    } catch (error) {
      console.error('Error rejecting plan:', error);
      setError('Failed to reject learning plan. Please try again.');
    }
  };

  const getProjectStats = () => {
    const total = userProjects.length;
    const inProgress = userProjects.filter(p => p.status === 'accepted' || p.status === 'in_progress').length;
    const completed = userProjects.filter(p => p.status === 'completed').length;
    
    return { total, inProgress, completed };
  };

  const stats = getProjectStats();

  if (loading) {
    return (
      <div className={styles.projectBoard}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Loading your learning journey...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.projectBoard}>
      <div className={styles.header}>
        <h1 className={styles.title}>Your Learning Journey</h1>
        <p className={styles.subtitle}>
          Discover new learning paths and track your progress
        </p>
      </div>

      {error && (
        <div className={styles.error}>
          <p>{error}</p>
          <button onClick={loadData} className={styles.retryButton}>
            Try Again
          </button>
        </div>
      )}

      <div className={styles.stats}>
        <div className={styles.statCard}>
          <BookOpen className={styles.statIcon} />
          <div className={styles.statContent}>
            <span className={styles.statNumber}>{stats.total}</span>
            <span className={styles.statLabel}>Total Projects</span>
          </div>
        </div>
        <div className={styles.statCard}>
          <Clock className={styles.statIcon} />
          <div className={styles.statContent}>
            <span className={styles.statNumber}>{stats.inProgress}</span>
            <span className={styles.statLabel}>In Progress</span>
          </div>
        </div>
        <div className={styles.statCard}>
          <CheckCircle className={styles.statIcon} />
          <div className={styles.statContent}>
            <span className={styles.statNumber}>{stats.completed}</span>
            <span className={styles.statLabel}>Completed</span>
          </div>
        </div>
      </div>

      <div className={styles.tabs}>
        <button 
          className={`${styles.tab} ${activeTab === 'plans' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('plans')}
        >
          <Target className={styles.tabIcon} />
          New Learning Plans ({learningPlans.length})
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'projects' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('projects')}
        >
          <BookOpen className={styles.tabIcon} />
          My Projects ({userProjects.length})
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'tasks' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          <List className={styles.tabIcon} />
          Task Tracking
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'plans' && (
          <div className={styles.section}>
            {learningPlans.length === 0 ? (
              <div className={styles.empty}>
                <Plus className={styles.emptyIcon} />
                <h3>No New Learning Plans</h3>
                <p>Start a conversation with the AI to generate personalized learning plans!</p>
              </div>
            ) : (
              <div className={styles.grid}>
                {learningPlans.map((plan, index) => (
                  <ProjectCard
                    key={plan.id || index}
                    project={plan}
                    onAccept={handleAcceptPlan}
                    onReject={handleRejectPlan}
                    isLearningPlan={true}
                    showActions={true}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'projects' && (
          <div className={styles.section}>
            {userProjects.length === 0 ? (
              <div className={styles.empty}>
                <BookOpen className={styles.emptyIcon} />
                <h3>No Projects Yet</h3>
                <p>Accept a learning plan to start your first project!</p>
              </div>
            ) : (
              <div className={styles.grid}>
                {userProjects.map((project, index) => (
                  <ProjectCard
                    key={project.id || index}
                    project={project}
                    isLearningPlan={false}
                    showActions={false}
                    onViewDetails={() => {
                      setSelectedProject(project);
                      setActiveTab('tasks');
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className={styles.section}>
            {userProjects.length === 0 ? (
              <div className={styles.empty}>
                <List className={styles.emptyIcon} />
                <h3>No Projects to Track</h3>
                <p>Accept a learning plan to start tracking your progress!</p>
              </div>
            ) : !selectedProject ? (
              <div className={styles.projectSelector}>
                <h3>Select a Project to Track</h3>
                <div className={styles.projectList}>
                  {userProjects.filter(p => p.status === 'accepted' || p.status === 'in_progress').map((project, index) => (
                    <div
                      key={project.id || index}
                      className={styles.projectOption}
                      onClick={() => setSelectedProject(project)}
                    >
                      <div className={styles.projectInfo}>
                        <h4>{project.title}</h4>
                        <p>{project.description}</p>
                      </div>
                      <div className={styles.projectProgress}>
                        <div className={styles.progressBar}>
                          <div 
                            className={styles.progressFill}
                            style={{ width: `${project.completion_percentage || 0}%` }}
                          />
                        </div>
                        <span>{project.completion_percentage || 0}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className={styles.taskTrackerContainer}>
                <button 
                  className={styles.backButton}
                  onClick={() => setSelectedProject(null)}
                >
                  ← Back to Project Selection
                </button>
                <TaskTracker 
                  project={selectedProject}
                  onProgressUpdate={(projectId, percentage) => {
                    // Update the project in the list
                    setUserProjects(prev => prev.map(p => 
                      p.id === projectId 
                        ? { ...p, completion_percentage: percentage }
                        : p
                    ));
                  }}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectBoard;