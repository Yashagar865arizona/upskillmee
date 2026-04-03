import React, { memo } from "react";
import "./TasksList.css";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import { useNavigate } from "react-router-dom";

const TasksList = memo(function TasksList() {
  const { projects } = useLearningPlan();
  const navigate = useNavigate();

  const tasks =
  
    projects?.flatMap((project) =>
      (project.tasks || []).map((task, idx) => ({
        id: `${project.projectId}-${idx}`,
        title: task.description || `Task ${idx + 1}`,
        projectId: project.projectId, 
        project: project.title || "Untitled Project",
        dueDate: task.due_date ? task.due_date.split("T")[0] : "No deadline",
        priority: task.priority || "medium",
        completed: !!task.completed,
        overdue: false, 
        emoji: project.emoji || "📌",
      }))
    ) || [];

  const visibleTasks = tasks.slice(0, 5);

  const handleViewAll = () => {
    navigate("/alltaskslist");
  };

  return (
    <div className="tasks-container">
      <div className="tasks-header">
        <div>
          <h2 className="tasks-title">Learning Tasks </h2>
          <p className="tasks-subtitle">Stay on track with your goals 🎯</p>
        </div>
        {tasks.length > 5 && (
          <button className="view-all-btn" onClick={handleViewAll}>
            View all →
          </button>
        )}
      </div>

      <div className="tasks-list">
        {visibleTasks.map((task) => (
          <div
            key={task.id}
            className={`task-card ${
              task.overdue
                ? "task-overdue"
                : task.completed
                ? "task-completed"
                : "task-active"
            }`}
          >
            <div className="task-emoji">{task.emoji}</div>

            <div className="task-info">
              <input
                type="checkbox"
                checked={task.completed}
                readOnly
                className="task-checkbox"
              />

              <div className="task-details">
                <h3 className={`task-title ${task.completed ? "completed" : ""}`}>
                  {task.title}
                </h3>

                <p className="task-project">{task.project}</p>

                <div className="task-meta">
                  <span className={`due-date ${task.overdue ? "overdue" : ""}`}>
                    {task.dueDate}
                  </span>
                  <span className={`priority ${task.priority}`}>
                    {task.priority}
                  </span>+
                </div>
              </div>

              {!task.completed && <button className="start-btn" onClick={() => navigate(`/projects?projectId=${task.projectId}`)}>Start</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

export default TasksList;
