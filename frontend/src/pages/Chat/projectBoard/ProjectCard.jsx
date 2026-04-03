import React from "react";
import styles from "./ProjectBoard.module.css";

// Simple helper function to determine the type of skill
const getSkillType = (skill, index) => {
  // Cycle through 5 types based on index
  const types = ['technical', 'analytical', 'communication', 'validation', 'research'];
  return types[index % types.length];
};

// Simple helper function to determine the phase based on index
const getPhase = (index) => {
  const phases = ['discovery', 'validation', 'business', 'prototype', 'pitch'];
  return phases[index % phases.length];
};

const ProjectCard = ({ project, index = 0 }) => {
  // Log the project structure for debugging
  console.log(`Rendering ProjectCard for project at index ${index}:`, project);

  // Handle different project structures
  let title, description, tasks, skills, resources, weeks, duration, funFactor;

  // Extract data from project
  if (typeof project === 'object') {
    title = project.title || '';
    description = project.description || '';
    tasks = Array.isArray(project.tasks) ? project.tasks : [];
    skills = Array.isArray(project.skills) ? project.skills : [];
    resources = Array.isArray(project.resources) ? project.resources : [];
    weeks = project.weeks || '';
    duration = project.duration || '';
    funFactor = project.funFactor || '';

    // Handle nested structures
    if (project.content) {
      if (!title && project.content.title) title = project.content.title;
      if (!description && project.content.description) description = project.content.description;
      if (tasks.length === 0 && Array.isArray(project.content.tasks)) tasks = project.content.tasks;
      if (skills.length === 0 && Array.isArray(project.content.skills)) skills = project.content.skills;
      if (resources.length === 0 && Array.isArray(project.content.resources)) resources = project.content.resources;
      if (!weeks && project.content.weeks) weeks = project.content.weeks;
      if (!duration && project.content.duration) duration = project.content.duration;
      if (!funFactor && project.content.funFactor) funFactor = project.content.funFactor;
    }
  } else {
    console.error('Invalid project structure:', project);
    title = 'Invalid Project';
    description = 'This project has an invalid structure.';
  }

  // Use duration if available, otherwise fall back to weeks
  const timeframe = duration || weeks || "";

  return (
    <div className={styles.projectCard}>
      <h3 className={styles.cardTitle} data-phase={getPhase(index)}>
        {title}
      </h3>

      {timeframe && (
        <div className={styles.timeframe}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: "6px" }}>
            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 6V12L16 14" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          {timeframe}
        </div>
      )}

      {description && (
        <p className={styles.cardDescription}>{description}</p>
      )}

      {funFactor && (
        <div className={styles.funFactor}>
          <span>✨ Fun Factor</span>
          {funFactor}
        </div>
      )}

      {tasks && tasks.length > 0 && (
        <div className={styles.sectionContainer}>
          <h4 className={styles.sectionTitle}>Tasks</h4>
          <div className={styles.taskList}>
            {tasks.map((task, index) => (
              <div key={index} className={styles.task}>
                {task}
              </div>
            ))}
          </div>
        </div>
      )}

      {skills && skills.length > 0 && (
        <div className={styles.sectionContainer}>
          <h4 className={styles.sectionTitle}>Skills to Develop</h4>
          <div className={styles.skillTags}>
            {skills.map((skill, index) => (
              <div
                key={index}
                className={styles.skillTag}
                data-type={getSkillType(skill, index)}
              >
                {skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {resources && resources.length > 0 && (
        <div className={styles.sectionContainer}>
          <h4 className={styles.sectionTitle}>Resources</h4>
          <div className={styles.taskList}>
            {resources.map((resource, index) => (
              <div key={index} className={styles.task}>
                {resource}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectCard;
