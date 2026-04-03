import React, { useState, useEffect } from "react";
import styles from "./RightSidebar.module.css";
import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import { motion } from "framer-motion";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { Sparkles, Rocket } from "lucide-react";
import { getRandom } from "@anilseervi/inspirational-quotes";
import PsychometricTest from "../../pages/Settings/PsychometricTest";

const RightSidebar = () => {
  const { theme } = useTheme();
  const { user, updateProfile} = useAuth();
  const showPsychometric = user?.psychometric_status !== "submitted";
  const [showTest, setShowTest] = useState(false);
  const { projects = [] } = useLearningPlan();
  const [tasks, setTasks] = useState([]);
  const [progress, setProgress] = useState([]);
  const [skills, setSkills] = useState([]);
  const [quote, setQuote] = useState("");

  
  useEffect(() => {
    if (Array.isArray(projects) && projects.length > 0) {
      const allTasks = projects.flatMap((project) =>
        (project.tasks || []).map((t) => ({
          title: t.title || "Untitled Task",
          deadline: t.due_date ? new Date(t.due_date) : null,
          completed: Boolean(t.completed),
        }))
      );
      setTasks(allTasks);

      const completedSkills = projects
        .filter((p) => p.progress_percentage === 100)
        .flatMap((p) => p.skills || []);
      const uniqueSkills = [...new Set(completedSkills)];
      setSkills(uniqueSkills);
    } else {
      setTasks([]);
      setSkills([]);
    }
  }, [projects]);

 
  useEffect(() => {
    const todayKey = new Date().toDateString();
    const stored = localStorage.getItem(`daily-quote-${todayKey}`);
    if (stored) {
      setQuote(JSON.parse(stored));
    } else {
      const newQuote = getRandom();
      setQuote(newQuote);
      localStorage.setItem(`daily-quote-${todayKey}`, JSON.stringify(newQuote));
    }
  }, []);

  
  useEffect(() => {
    if (!Array.isArray(tasks) || tasks.length === 0) {
      setProgress([]);
      return;
    }

    const totalTasks = tasks.length;
    const completedTasks = tasks.filter((t) => t.completed).length;
    const allProjectPercent =
      totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    const weeklyTasks = tasks.filter(
      (t) => t.deadline && t.deadline >= startOfWeek && t.deadline <= endOfWeek
    );
    const completedWeekly = weeklyTasks.filter((t) => t.completed).length;
    const weeklyPercent =
      weeklyTasks.length > 0
        ? Math.round((completedWeekly / weeklyTasks.length) * 100)
        : 0;

    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    const monthlyTasks = tasks.filter(
      (t) =>
        t.deadline &&
        t.deadline.getMonth() === currentMonth &&
        t.deadline.getFullYear() === currentYear
    );
    const completedMonthly = monthlyTasks.filter((t) => t.completed).length;
    const monthlyPercent =
      monthlyTasks.length > 0
        ? Math.round((completedMonthly / monthlyTasks.length) * 100)
        : 0;

    setProgress([
      { label: "All Projects", percent: allProjectPercent },
      { label: "Weekly", percent: weeklyPercent },
      { label: "Monthly", percent: monthlyPercent },
    ]);
  }, [tasks]);

  
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();

  const calendarDays = [];
  for (let i = 0; i < firstDay; i++) calendarDays.push(null);
  for (let d = 1; d <= daysInMonth; d++) calendarDays.push(d);

  const getTasksCount = (day) =>
    tasks.filter(
      (t) =>
        t.deadline &&
        t.deadline.getFullYear() === year &&
        t.deadline.getMonth() === month &&
        t.deadline.getDate() === day &&
        t.completed
    ).length;

  const getTasksTotal = (day) =>
    tasks.filter(
      (t) =>
        t.deadline &&
        t.deadline.getFullYear() === year &&
        t.deadline.getMonth() === month &&
        t.deadline.getDate() === day
    ).length;


  if (showTest) {
    return <PsychometricTest onComplete={() => setShowTest(false)} />;
  }
  return (
    <div
      className={`${styles.rightSidebar} ${
        theme === "dark" ? styles.dark : styles.light
      }`}
    >
      {showPsychometric && (
                <div className={styles.testCard}>
                  <h3>🧠 Psychometric Test</h3>
                  <p>Take this short test to personalize your experience.</p>
                  <button
                    className={styles.takeTestBtn}
                    onClick={() => setShowTest(true)}
                  >
                    Take Psychometric Test
                  </button>
                </div>
              )}
     
      <motion.div
        className={styles.calendarSection}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        <h4>📅 Monthly Tasks</h4>
        <div className={styles.calendarGrid}>
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d, i) => (
            <div key={i} className={styles.calendarHeader}>
              {d}
            </div>
          ))}
          {calendarDays.map((day, i) => (
            <div
              key={i}
              className={`${styles.calendarDay} ${
                day && getTasksCount(day) > 0 ? styles.completed : ""
              }`}
              title={
                day
                  ? `Completed: ${getTasksCount(day)} / ${getTasksTotal(day)}`
                  : ""
              }
            >
              {day && (
                <>
                  <span>{day}</span>
                  {getTasksTotal(day) > 0 && (
                    <div className={styles.dayProgress}>
                      <div
                        className={styles.dayProgressFill}
                        style={{
                          width: `${
                            (getTasksCount(day) / getTasksTotal(day)) * 100
                          }%`,
                        }}
                      ></div>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </motion.div>

      
      {Array.isArray(skills) && skills.length > 0 && (
        <motion.div
          className={styles.skillRadar}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <h4 className={styles.skillRadarTitle}>💪 Skill Strengths</h4>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart
              outerRadius={70}
              data={skills.map((s) => ({
                skill: s.split(' ')[0],
                strength: Math.floor(Math.random() * 50) + 50,
              }))}
            >
              <PolarGrid />
              <PolarAngleAxis
                dataKey="skill"
                tick={{
                  fontSize: 12,
                  fill: theme === "dark" ? "#fff" : "#000",
                }}
              />
              <PolarRadiusAxis
                angle={30}
                domain={[0, 100]}
                tick={{
                  fontSize: 10,
                  fill: theme === "dark" ? "#ddd" : "#333",
                }}
              />
              <Radar
                name="Skill Strength"
                dataKey="strength"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.5}
              />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

    
      <motion.div
        className={styles.motivationBox}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <Sparkles className={styles.sparkleIcon} />
        {quote ? (
          <span className={styles.motivationText}>
            &ldquo;{quote.quote}&rdquo; ― <strong>{quote.author}</strong>
          </span>
        ) : (
          <span className={styles.motivationText}>Loading inspiration…</span>
        )}
        <Rocket className={styles.rocketIcon} />
      </motion.div>
    </div>
  );
};

export default RightSidebar;
