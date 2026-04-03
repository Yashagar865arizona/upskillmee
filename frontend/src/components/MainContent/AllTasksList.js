import React from "react";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import "./TasksList.css";
import { useNavigate } from "react-router-dom";

const AllTasksList = () => {
  const { projects } = useLearningPlan();
const navigate = useNavigate();
  const tasks = projects?.flatMap((project) =>
    (project.tasks || []).map((task, tIdx) => ({
      id: `${project.projectId}-${tIdx}`,
      title: task.description || `Task ${tIdx + 1}`,
      project: project.title || "Untitled Project",
      projectId: project.projectId,
      dueDate: task.due_date ? task.due_date.split("T")[0] : "No deadline",
      priority: task.priority || "medium",
      completed: !!task.completed,
      overdue: false,
      emoji: project.emoji || "📌",
    }))
  ) || [];

  return (
    <div className="tasks-container">
      <h2 className="tasks-title">All Learning Tasks 📚</h2>
      <div className="tasks-list">
        {tasks.map((task) => (
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
                  <span className={`priority ${task.priority}`}>{task.priority}</span>
                </div>
              </div>

              {!task.completed && <button className="start-btn" onClick={() => navigate(`/projects?projectId=${task.projectId}`)}>Start</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AllTasksList;
