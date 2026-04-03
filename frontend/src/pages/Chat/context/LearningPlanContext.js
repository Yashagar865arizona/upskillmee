import React, { createContext, useState, useContext, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";

const LearningPlanContext = createContext();
const BASE_STORAGE_KEY = "ponder_learning_plan";

export const LearningPlanProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [projects, setProjects] = useState([]);
  const [allProjects, setAllProjects] = useState([]);

  const userId = user?.id || "anonymous";
  const STORAGE_KEY = `${BASE_STORAGE_KEY}_${userId}`;
  const ALL_STORAGE_KEY = `${BASE_STORAGE_KEY}_${userId}_all`;

  
  const saveToLocalStorage = (projectsData, allProjectsData) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(projectsData));
    localStorage.setItem(ALL_STORAGE_KEY, JSON.stringify(allProjectsData));
  };

  
  useEffect(() => {
    const savedProjects = localStorage.getItem(STORAGE_KEY);
    const savedAllProjects = localStorage.getItem(ALL_STORAGE_KEY);

    if (savedProjects) {
      try {
        setProjects(JSON.parse(savedProjects));
      } catch (e) {
        console.error("Error parsing saved projects:", e);
      }
    }

    if (savedAllProjects) {
      try {
        setAllProjects(JSON.parse(savedAllProjects));
      } catch (e) {
        console.error("Error parsing saved allProjects:", e);
      }
    }
  }, [userId]);

  // Save to localStorage whenever projects/allProjects change
  useEffect(() => {
    saveToLocalStorage(projects, allProjects);
  }, [projects, allProjects]);

  // Fetch projects from backend
  const fetchPlansFromBackend = useCallback(async () => {
    if (!isAuthenticated) {
      setProjects([]);
      setAllProjects([]);
      return;
    }

    try {
      const { getLearningPlans } = await import("../../../api/learningApi");
      const plans = await getLearningPlans(userId);
      if (!plans || plans.length === 0) return;

      // Current plan projects
      const currentPlan = plans[0];
      let projectsFromCurrentPlan = [];
      if (currentPlan.content) {
        if (Array.isArray(currentPlan.content.projects)) {
          projectsFromCurrentPlan = currentPlan.content.projects.map((proj, idx) => ({
            ...proj,
            projectId: proj.id || `${currentPlan.id}-proj-${idx + 1}`,
          }));
        } else if (typeof currentPlan.content.projects === "object") {
          projectsFromCurrentPlan = [
            { ...currentPlan.content.projects, projectId: currentPlan.id || `${currentPlan.id}-proj-1` },
          ];
        } else if (currentPlan.content.title && currentPlan.content.description) {
          projectsFromCurrentPlan = [
            { ...currentPlan.content, projectId: currentPlan.id || `${currentPlan.id}-proj-1` },
          ];
        }
      } else {
        projectsFromCurrentPlan = [
          {
            id: currentPlan.id,
            projectId: currentPlan.id,
            title: currentPlan.title,
            description: currentPlan.description,
            created_at: currentPlan.created_at,
          },
        ];
      }

      // All projects from all plans
      const allProjectsFromPlans = plans.flatMap((plan) => {
        if (plan.content) {
          if (Array.isArray(plan.content.projects)) {
            return plan.content.projects.map((proj, idx) => ({
              ...proj,
              projectId: proj.id || `${plan.id}-proj-${idx + 1}`,
              planId: plan.id,
            }));
          } else if (typeof plan.content.projects === "object") {
            return [{ ...plan.content.projects, projectId: plan.id || `${plan.id}-proj-1`, planId: plan.id }];
          } else if (plan.content.title && plan.content.description) {
            return [{ ...plan.content, projectId: plan.id || `${plan.id}-proj-1`, planId: plan.id }];
          }
        }
        return [
          {
            id: plan.id,
            projectId: plan.id,
            title: plan.title,
            description: plan.description,
            created_at: plan.created_at,
            planId: plan.id,
          },
        ];
      });

      setProjects(projectsFromCurrentPlan);
      setAllProjects(allProjectsFromPlans);
      saveToLocalStorage(projectsFromCurrentPlan, allProjectsFromPlans);
      return { projects: projectsFromCurrentPlan, allProjects: allProjectsFromPlans };
    } catch (error) {
      console.error("Error fetching learning plans:", error);
    }
  }, [isAuthenticated, userId]);

  // Initial fetch
  useEffect(() => {
    fetchPlansFromBackend();
  }, [fetchPlansFromBackend]);

  const updateProjects = useCallback((newProjects) => {
    setProjects(newProjects);
  }, []);

  const updateAllProjects = useCallback((newAllProjects) => {
    setAllProjects(newAllProjects);
  }, []);

  return (
    <LearningPlanContext.Provider
      value={{ projects, allProjects, updateProjects, updateAllProjects, refreshPlans: fetchPlansFromBackend, userId }}
    >
      {children}
    </LearningPlanContext.Provider>
  );
};

export const useLearningPlan = () => {
  const context = useContext(LearningPlanContext);
  if (!context) throw new Error("useLearningPlan must be used within a LearningPlanProvider");
  return context;
};
