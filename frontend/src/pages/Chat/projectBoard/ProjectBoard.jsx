import React, { useEffect, useState } from "react";
import styles from "./ProjectBoard.module.css";
import { useLearningPlan } from "../context/LearningPlanContext";
import { useAuth } from "../../../context/AuthContext";
import ProjectEditModal from "./ProjectEditModal";
import { useTheme } from "../../../context/ThemeContext";

/**
 * ProjectBoard Component
 * Displays the complete learning plan with all projects
 */
export const ProjectBoard = () => {
  const { darkMode} = useTheme();
  const { projects, updateProjects, refreshPlans } = useLearningPlan();
  const { user } = useAuth();
  const userName = user?.full_name.split(" ")[0] || "Your";

  // State for the edit modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);

  useEffect(() => {
    if (!projects || projects.length === 0) {
      loadFromLocalStorage();
    }
  }, [projects]);

  const loadFromLocalStorage = () => {
    try {
      const userId = localStorage.getItem("userId") || "anonymous";
      const savedPlan = localStorage.getItem(`upskillmee_learning_plan_${userId}`);
      if (savedPlan) {
        const parsedPlan = JSON.parse(savedPlan);
        if (
          !(
            parsedPlan &&
            parsedPlan.length === 1 &&
            parsedPlan[0].title === "Test Project 1"
          )
        ) {
          updateProjects(parsedPlan);
        }
      }
    } catch (error) {
      console.error("Error loading projects:", error);
    }
  };

  // Open the edit modal for a specific project
  const handleEditClick = (project, index) => {
    setEditingProject(project);
    setEditingIndex(index);
    setIsModalOpen(true);
  };

  // Handle saving the edited project
  const handleSaveProject = (editedProject, index) => {
    const updatedProjects = [...projects];
    updatedProjects[index] = editedProject;
    updateProjects(updatedProjects);
  };

  if (!projects || projects.length === 0) {
    return (
      <div className={styles.projectBoard}>
        <div className={styles.emptyState}>
          <h3>No Projects Yet</h3>
          <p>Start a conversation to create your first learning plan!</p>
        </div>
      </div>
    );
  }
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <div className={styles.projectBoard}>
      <div className={styles.goalsContainer}>
        <div className={styles.goalHeader}>
          <div className={styles.goalTitle}>{userName}'s Learning Journey</div>
        </div>
        <div className={styles.progressContainer}>
          {projects.map((project, index) => (
            <div key={index} className={styles.taskItem}>
              <div className={styles.taskHeader}>
                <div className={styles.taskHeaderContent}>
                  <span className={styles.taskLabel}>
                    {index === 0 ? "Current Week" : `Week ${index + 1}`}
                  </span>
                  <h3 className={styles.taskTitle}>{project.title}</h3>
                </div>
                <button
                  onClick={() => handleEditClick(project, index)}
                  className={styles.editButton}
                  aria-label={`Edit ${project.title}`}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M18.5 2.50001C18.8978 2.10219 19.4374 1.87869 20 1.87869C20.5626 1.87869 21.1022 2.10219 21.5 2.50001C21.8978 2.89784 22.1213 3.4374 22.1213 4.00001C22.1213 4.56262 21.8978 5.10219 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              </div>
              <div className={styles.taskContent}>
                <div className={styles.taskDescription}>
                  {project.description && (
                    <>
                      <div className={styles.sectionHeader}>Description</div>
                      <p className={styles.descriptionText}>
                        {project.description}
                      </p>
                    </>
                  )}

                  {project.tasks && project.tasks.length > 0 && (
                    <>
                      <div className={styles.sectionHeader}>Tasks</div>
                      <div style={{ counterReset: "step" }}>
                        {project.tasks.map((task, taskIndex) => (
                          <div
                            key={task.task_id || taskIndex}
                            className={styles.stepItem}
                          >
                            {task.description}
                          </div>
                        ))}
                      </div>
                    </>
                  )}

                  {project.resources && project.resources.length > 0 && (
                    <>
                      <div className={styles.sectionHeader}>Resources</div>
                      {project.resources.map((resource, resourceIndex) => (
                        <p key={resourceIndex} className={styles.resourceItem}>
                          {resource}
                        </p>
                      ))}
                    </>
                  )}

                  {project.skills && project.skills.length > 0 && (
                    <>
                      <div className={styles.sectionHeader}>Skills</div>
                      {project.skills.map((skill, skillIndex) => (
                        <p key={skillIndex} className={styles.skillItem}>
                          {skill}
                        </p>
                      ))}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Edit Modal */}
      <ProjectEditModal
        project={editingProject}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveProject}
        projectIndex={editingIndex}
      />
    </div>
  );
};
