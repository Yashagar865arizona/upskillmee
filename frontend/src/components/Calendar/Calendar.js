import React, { useState, useMemo } from "react";
import { useTheme } from "../../context/ThemeContext";
import styles from "./Calendar.module.css";
import { FiChevronLeft, FiChevronRight, FiCheckCircle } from "react-icons/fi";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import { useNavigate } from "react-router-dom";

export default function Calendar() {
  const { allProjects } = useLearningPlan();
  const { theme } = useTheme();
  const navigate=useNavigate();
  const today = new Date();
const formattedToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedDate, setSelectedDate] = useState(formattedToday);

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
      d.getDate()
    ).padStart(2, "0")}`;
  };

  const tasks = useMemo(() => {
    if (!allProjects) return [];
    return allProjects.flatMap((project) =>
      project.tasks.map((task) => ({
        id: task.task_id,
        title: task.title,
        description: task.description,
        completed: task.completed,
        date: formatDate(task.due_date),
        projectTitle: project.title,
        priority: task.priority || "low",
        projectId: project.id, 
      }))
    );
  }, [allProjects]);

  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDay = new Date(currentYear, currentMonth, 1).getDay();

  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let d = 1; d <= daysInMonth; d++) days.push(d);

  const monthNames = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
  ];

  const filteredTasks = selectedDate
    ? tasks.filter((t) => t.date === selectedDate)
    : tasks;

  const getTasksForDate = (date) => tasks.filter((t) => t.date === date);

  return (
    <div className={`${styles.container} ${theme === "dark" ? styles.dark : styles.light}`}>
      <div className={styles.header}>
        <button
          onClick={() => setCurrentMonth((m) => (m === 0 ? 11 : m - 1))}
          className={styles.navBtn}
        >
          <FiChevronLeft />
        </button>
        <h4 className={styles.monthTitle}>
          {monthNames[currentMonth]} {currentYear}
        </h4>
        <button
          onClick={() => setCurrentMonth((m) => (m === 11 ? 0 : m + 1))}
          className={styles.navBtn}
        >
          <FiChevronRight />
        </button>
      </div>

      <div className={styles.calendarWrapper}>
        <div className={styles.grid}>
          {["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map((d) => (
            <div key={d} className={styles.dayHeader}>{d}</div>
          ))}
          {days.map((day, idx) => {
            const dayDate = day
              ? `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(
                  2,
                  "0"
                )}`
              : null;
            const dayTasks = day ? getTasksForDate(dayDate) : [];
            return (
              <div
                key={idx}
                className={`${styles.day} ${dayDate === selectedDate ? styles.selected : ""}`}
                onClick={() => day && setSelectedDate(dayDate)}
              >
                {day}
                <div className={styles.dotsWrapper}>
                  {dayTasks.map((task) => (
                    <span
                      key={task.id}
                      className={`${styles.dot} ${
                        task.priority === "high"
                          ? styles.high
                          : task.priority === "medium"
                          ? styles.medium
                          : styles.low
                      }`}
                    ></span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

      
        <div className={styles.tasks}>
          <h4>Tasks</h4>
          {filteredTasks.length > 0 ? (
            filteredTasks.map((task) => (
              <div key={task.id} className={styles.taskItem} onClick={() => navigate(`/projects?projectId=${task.projectId}`)}>
                <span className={task.completed ? styles.completed : ""}>
                  {task.completed && <FiCheckCircle className={styles.checkIcon} />}
                  {task.title} – {task.description}
                </span>
                <small>
                  {task.date} | <b>{task.projectTitle}</b> {" "}
                  <span
                    className={
                      task.priority === "high"
                        ? styles.high
                        : task.priority === "medium"
                        ? styles.medium
                        : styles.low
                    }
                  >
                  </span>
                </small>
              </div>
            ))
          ) : (
            <p className={styles.noTask}>No tasks</p>
          )}
        </div>
      </div>
    </div>
  );
}
