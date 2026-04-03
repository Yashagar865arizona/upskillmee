import React, { memo } from "react";
import { Play, Clock, BookOpen, ArrowRight } from "lucide-react";
import "./LearningProgress.css";
import { useTheme } from "../../context/ThemeContext";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import { useNavigate } from "react-router-dom";

const LearningProgress = memo(function LearningProgress() {
  const { darkMode } = useTheme();
  const { projects } = useLearningPlan();
  const navigate = useNavigate();

  
  const currentProject =
    projects.find((project) => project.completed_tasks < project.total_tasks) ||
    projects[0] ||
    { tasks: [], skills: [], title: "", description: "", total_tasks: 0, completed_tasks: 0 };

  const tasksTotal = currentProject.total_tasks || 0;
  const tasksDone = currentProject.completed_tasks || 0;
  const overall = tasksTotal > 0 ? Math.round((tasksDone / tasksTotal) * 100) : 0;

  const hoursSpent = currentProject.tasks?.reduce(
    (sum, t) => sum + (t.timeSpent || 0),
    0
  );

  const skillsCount = currentProject.skills?.length || 0;

  if (!projects || projects.length === 0) {
    return (
      <div className="lp-card">
        <p>No active learning projects found.</p>
      </div>
    );
  }

  const iconColors = {
    blue: darkMode ? "#ffffff" : "#2563eb",
    green: darkMode ? "#ffffff" : "#22c55e",
    yellow: darkMode ? "#ffffff" : "#eab308",
  };

  const handleContinue = () => {
    navigate(`/projects?projectId=${currentProject.projectId}`);
  };

  return (
    <div className="lp-card">
      <div className="lp-header">
        <div>
          <h2 className="lp-title">Active Learning</h2>
          <p className="lp-subtitle">Your current learning journey 📖</p>
        </div>

        <button
          type="button"
          className="lp-linkButton"
          aria-label="View all"
          onClick={() => navigate("/projects")}
        >
          View all{" "}
          <ArrowRight
            className="lp-iconSm"
            color={darkMode ? "#ffffff" : "#0d9488"}
          />
        </button>
      </div>

     
      <div className="lp-gradientCard">
        <div className="lp-projectTop">
          <div className="lp-projectInfo">
            <h3 className="lp-projectTitle">{currentProject.title}</h3>
            <p className="lp-projectDesc">{currentProject.description}</p>

            <div className="lp-progressSection">
              <div className="lp-progressHeader">
                <span className="lp-progressLabel">Overall Progress</span>
                <span className="lp-progressValue">{overall}%</span>
              </div>
              <div
                className="lp-progressBar"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={overall}
              >
                <div
                  className="lp-progressFill"
                  style={{ width: `${overall}%` }}
                />
              </div>
            </div>

            <div className="lp-statsGrid">
              <div className="lp-statCard">
                <div className="lp-statIcon lp-iconBlue">
                  <BookOpen
                    className="lp-iconXs"
                    color={iconColors.blue}
                  />
                </div>
                <div>
                  <p className="lp-statValue">{tasksDone}/{tasksTotal}</p>
                  <p className="lp-statLabel">Tasks</p>
                </div>
              </div>

              <div className="lp-statCard">
                <div className="lp-statIcon lp-iconGreen">
                  <Clock
                    className="lp-iconXs"
                    color={iconColors.green}
                  />
                </div>
                <div>
                  <p className="lp-statValue">{hoursSpent}h</p>
                  <p className="lp-statLabel">Spent</p>
                </div>
              </div>

              <div className="lp-statCard">
                <div className="lp-statIcon lp-iconYellow">
                  <Play
                    className="lp-iconXs"
                    color={iconColors.yellow}
                  />
                </div>
                <div>
                  <p className="lp-statValue">{skillsCount}</p>
                  <p className="lp-statLabel">Skills</p>
                </div>
              </div>
            </div>
          </div>

          <button
            type="button"
            className="lp-ctaButton"
            onClick={handleContinue}
          >
            <Play className="lp-iconSm" color="#fff" />
            <span>Continue</span>
          </button>
        </div>
      </div>
    </div>
  );
});

export default LearningProgress;
