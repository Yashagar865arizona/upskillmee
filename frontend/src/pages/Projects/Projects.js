import React, { useEffect, useState } from "react";
import { useLearningPlan } from "../Chat/context/LearningPlanContext";
import styles from "./Projects.module.css";
import { useLocation } from "react-router-dom";
import { taskCompletion } from "../../api/learningApi";
import { useAuth } from "../../context/AuthContext";
import LoadingSpinner from "../../components/Loading/LoadingSpinner";
import config from "../../config";
import { motion, AnimatePresence } from "framer-motion";
import EvaluationReportModal from "./EvaluationReportModal";
import { FiChevronDown, FiChevronUp } from "react-icons/fi";
import FeedbackModal from "../../components/Feedback/FeedbackModal";
import FeedbackButton from "../../components/Feedback/FeedbackButton";

const Projects = () => {
  const { allProjects, refreshPlans, updateAllProjects } = useLearningPlan();
  const location = useLocation();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(null);
  const [completedTasks, setCompletedTasks] = useState({});
  const [finalFile, setFinalFile] = useState(null);
  const [reportModal, setReportModal] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  const toggleExpand = (index) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);
  useEffect(() => {
    if (allProjects.length === 0) return;

    const params = new URLSearchParams(location.search);
    const projectId =
      params.get("projectId") || localStorage.getItem("last_selected_project");

    if (projectId) {
      const project = allProjects.find((p) => p.projectId === projectId);
      if (project) {
        setSelectedProject(project);
        localStorage.setItem("last_selected_project", project.projectId);

        const initialCompleted = {};
        (project.tasks || []).forEach((task, index) => {
          initialCompleted[index] = {
            completed: task.completed === true && task.status === "completed",
            completed_at: task.completed_at || null,
          };
        });
        setCompletedTasks(initialCompleted);
      }
    }
  }, [allProjects, location.search]);

  const handleProjectClick = (project) => {
    setSelectedProject(project);
    localStorage.setItem("last_selected_project", project.projectId);

    const initialCompleted = {};
    (project.tasks || []).forEach((task, index) => {
      initialCompleted[index] = {
        completed: task.completed === true && task.status === "completed",
        completed_at: task.completed_at || null,
      };
    });
    setCompletedTasks(initialCompleted);
    setFinalFile(null);
  };

  const handleBack = () => {
    setSelectedProject(null);
    setCompletedTasks({});
    setFinalFile(null);
    localStorage.removeItem("last_selected_project");
  };

  const handleFileChange = (taskIndex, file) => {
    setCompletedTasks((prev) => ({
      ...prev,
      [taskIndex]: { ...prev[taskIndex], file },
    }));
  };

  const handleRemarkChange = (taskIndex, remark) => {
    setCompletedTasks((prev) => ({
      ...prev,
      [taskIndex]: { ...prev[taskIndex], remark },
    }));
  };

  const handleSubmitTask = async (taskIndex, taskId) => {
    const taskSubmission = completedTasks[taskIndex];
    if (!taskSubmission?.file && !taskSubmission?.remark) {
      alert("Please upload a file or add a remark before submitting.");
      return;
    }

    const formData = new FormData();

    if (taskSubmission.file) {
      formData.append("file", taskSubmission.file);
    }
    if (taskSubmission.remark) {
      formData.append("remark", taskSubmission.remark);
    }

    try {
      const res = await fetch(
        `${config.API_BASE_URL}/learning/tasks/${taskId}/submit`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await res.json();
      if (data.score !== undefined) {
        alert(
          `Task submitted!\nScore: ${data.score}\nFeedback: ${data.feedback}`
        );
      } else {
        alert("Task submitted successfully!");
      }

      await refreshPlans();
    } catch (error) {
      console.error("Task submission failed:", error);
      alert("Error submitting task.");
    }
  };

  useEffect(() => {
    if (!selectedProject || Object.keys(completedTasks).length > 0) {
      return;
    }

    const initialCompleted = {};
    (selectedProject.tasks || []).forEach((task, index) => {
      initialCompleted[index] = {
        completed: task.completed === true && task.status === "completed",
        completed_at: task.completed_at || null,
      };
    });
    setCompletedTasks(initialCompleted);
  }, [selectedProject]);

  if (loading) {
    return (
      <div className={styles.loaderWrapper}>
        <LoadingSpinner
          size="large"
          text="Loading your profile..."
          fullScreen={true}
        />
      </div>
    );
  }
  return (
    <div className={styles.container}>
      {!selectedProject ? (
        allProjects.length > 0 ? (
          <div className={styles.projectGrid}>
            {allProjects.map((project) => (
              <div
                key={project.projectId}
                className={styles.projectCard}
                onClick={() => handleProjectClick(project)}
              >
                <div className={styles.cardHeader}>
                  <h2 className={styles.projectTitle}>
                    {project.title?.split(":").slice(1).join(":").trim() ||
                      project.title}
                  </h2>
                  <span
                    className={`${styles.status} ${
                      project.status ? styles.active : styles.inactive
                    }`}
                  >
                    {project.status ? "Active" : "Inactive"}
                  </span>
                </div>

                <p className={styles.description}>
                  {project.description?.substring(0, 120)}...
                </p>

                <div className={styles.progressWrapper}>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progress}
                      style={{ width: `${project.progress_percentage || 0}%` }}
                    />
                  </div>
                  <span className={styles.progressText}>
                    {project.progress_percentage || 0}% Complete
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No projects found.</p>
        )
      ) : (
        <div className={styles.projectDetail}>
          <button className={styles.backButton} onClick={handleBack}>
            ← Back to Projects
          </button>

          <motion.div
            className={styles.detailCard}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h2 className={styles.detailTitle}>{selectedProject.title}</h2>
            <p className={styles.detailDescription}>
              {selectedProject.description}
            </p>

            {(selectedProject.tasks || []).length > 0 ? (
              <div className={styles.taskList}>
                {(selectedProject.tasks || []).map((task, index) => {
                  const taskState = completedTasks[index] || {};
                  const isCompleted = taskState.completed || false;

                  return (
                    <motion.div
                      className={`${styles.taskBlock} ${
                        isCompleted ? styles.taskCompleted : ""
                      }`}
                      key={task.task_id || index}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      whileHover={{ scale: !isCompleted ? 1.02 : 1 }}
                    >
                      <div className={styles.taskHeader}>
                        <input type="checkbox" checked={isCompleted} readOnly />
                        <span
                          className={`${styles.taskTitle} ${
                            isCompleted ? styles.completedText : ""
                          }`}
                        >
                          {task.title}: <span>{task.description}</span>
                        </span>

                        {task?.evaluation_report?.score !== undefined && (
                          <span
                            className={styles.evaluationScore}
                            style={{
                              color:
                                task?.evaluation_report?.score < 75
                                  ? "#f44336"
                                  : "#4caf50",
                              background:
                                task?.evaluation_report?.score < 75
                                  ? "#ffebee"
                                  : "#e8f5e9",
                            }}
                          >
                            ⭐ {task?.evaluation_report?.score}/100
                          </span>
                        )}

                        {task?.evaluation_report?.score < 75 && (
                          <motion.button
                            className={styles.viewReportBtn}
                            whileTap={{ scale: 0.95 }}
                            whileHover={{ scale: 1.05 }}
                            onClick={() =>
                              setReportModal(task.evaluation_report)
                            }
                          >
                            ⚠ Needs Improvement
                            <span className={styles.tooltip}>
                              Click to view report
                            </span>
                          </motion.button>
                        )}

                        <button
                          className={styles.expandButton}
                          onClick={() => toggleExpand(index)}
                        >
                          {expandedIndex === index ? (
                            <FiChevronUp size={20} />
                          ) : (
                            <FiChevronDown size={20} />
                          )}
                        </button>
                      </div>
                      {expandedIndex === index && (
                        <div className={styles.mainTaskActions}>
                          <div className={styles.taskActions}>
                            {!isCompleted ? (
                              <>
                                <input
                                  type="file"
                                  className={styles.fileInput}
                                  onChange={(e) =>
                                    handleFileChange(index, e.target.files[0])
                                  }
                                />
                                <textarea
                                  placeholder="Add a remark (optional)"
                                  className={styles.remarkInput}
                                  value={taskState.remark || ""}
                                  onChange={(e) =>
                                    handleRemarkChange(index, e.target.value)
                                  }
                                />
                              </>
                            ) : (
                              <motion.div
                                className={styles.evaluationFeedback}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3 }}
                              >
                                <h4>Feedback</h4>
                                <p>
                                  {task?.evaluation_report?.feedback ??
                                    "No feedback available yet"}
                                </p>
                              </motion.div>
                            )}
                          </div>
                          <div className={styles.submitWrapper}>
                            {!isCompleted ? (
                              <motion.button
                                className={styles.submitButton}
                                whileTap={{ scale: 0.95 }}
                                whileHover={{ scale: 1.05 }}
                                onClick={() =>
                                  handleSubmitTask(index, task.task_id)
                                }
                              >
                                🚀 Submit Task
                              </motion.button>
                            ) : (
                              <motion.button
                                className={styles.viewReportButton}
                                whileTap={{ scale: 0.95 }}
                                whileHover={{ scale: 1.05 }}
                                onClick={() => {
                                  setReportModal(task.evaluation_report);
                                  console.log(
                                    "%%%%%%%%%%%%%%%%%%%%%%$$$$$$$",
                                    task.evaluation_report
                                  );
                                }}
                              >
                                🚀 View Report
                              </motion.button>
                            )}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <p className={styles.noTaskText}>
                No tasks found for this project.
              </p>
            )}
          </motion.div>
        </div>
      )}
      <AnimatePresence>
        {reportModal && (
          <EvaluationReportModal
            report={reportModal}
            onClose={() => setReportModal(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Projects;
