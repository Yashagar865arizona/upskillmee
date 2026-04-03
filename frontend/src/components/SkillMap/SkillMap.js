import React, { useState, useEffect, useCallback } from "react";
import styles from "./SkillMap.module.css";
import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import { useLearningPlan } from "../../pages/Chat/context/LearningPlanContext";
import { getUserSkillMap } from "../../api/skillMapApi";
import { motion, AnimatePresence } from "framer-motion";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from "recharts";
import { Map, TrendingUp } from "lucide-react";

// Domain color palette
const DOMAIN_COLORS = {
  Frontend: { stroke: "#8b5cf6", fill: "#8b5cf6" },
  Backend: { stroke: "#06b6d4", fill: "#06b6d4" },
  Data: { stroke: "#f59e0b", fill: "#f59e0b" },
  DevOps: { stroke: "#10b981", fill: "#10b981" },
  Design: { stroke: "#ec4899", fill: "#ec4899" },
  Mobile: { stroke: "#f97316", fill: "#f97316" },
  AI: { stroke: "#6366f1", fill: "#6366f1" },
  Other: { stroke: "#64748b", fill: "#64748b" },
};

// Classify a skill string into a domain
const classifySkill = (skill) => {
  const s = skill.toLowerCase();
  if (/react|vue|angular|css|html|tailwind|javascript|typescript|frontend|ui|ux/.test(s)) return "Frontend";
  if (/node|express|fastapi|django|flask|sql|database|api|backend|server|python|java|go/.test(s)) return "Backend";
  if (/data|pandas|numpy|analytics|visualization|tableau|statistics|ml|machine.?learning/.test(s)) return "Data";
  if (/docker|kubernetes|ci.?cd|aws|azure|gcp|devops|terraform|deploy/.test(s)) return "DevOps";
  if (/figma|sketch|design|wireframe|prototype|illustration/.test(s)) return "Design";
  if (/react.native|flutter|swift|kotlin|ios|android|mobile/.test(s)) return "Mobile";
  if (/ai|llm|nlp|deep.?learning|neural|gpt|openai|transformer/.test(s)) return "AI";
  return "Other";
};

// Derive skill map data from projects when backend API is unavailable
const deriveFromProjects = (projects) => {
  if (!Array.isArray(projects) || projects.length === 0) return [];

  const skillMap = {};

  projects.forEach((project) => {
    const skills = project.skills || [];
    const progress = project.progress_percentage || 0;

    skills.forEach((skill) => {
      const domain = classifySkill(skill);
      if (!skillMap[skill]) {
        skillMap[skill] = { name: skill, domain, proficiency: 0, projects: [] };
      }
      skillMap[skill].proficiency = Math.min(
        100,
        skillMap[skill].proficiency + Math.round(progress * 0.5)
      );
      skillMap[skill].projects.push(project.title || "Untitled");
    });
  });

  return Object.values(skillMap);
};

// Aggregate skills into domain-level data for radar chart
const aggregateToDomains = (skills) => {
  const domains = {};

  skills.forEach(({ domain, proficiency }) => {
    if (!domains[domain]) {
      domains[domain] = { domain, total: 0, count: 0 };
    }
    domains[domain].total += proficiency;
    domains[domain].count += 1;
  });

  return Object.values(domains).map(({ domain, total, count }) => ({
    domain,
    proficiency: Math.round(total / count),
    skillCount: count,
  }));
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipDomain}>{data.domain}</p>
      <p className={styles.tooltipValue}>
        Proficiency: {data.proficiency}%
      </p>
      <p className={styles.tooltipSkills}>
        {data.skillCount} skill{data.skillCount !== 1 ? "s" : ""}
      </p>
    </div>
  );
};

const SkillMap = () => {
  const { theme } = useTheme();
  const { user, token } = useAuth();
  const { projects = [] } = useLearningPlan();
  const [skills, setSkills] = useState([]);
  const [domainData, setDomainData] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSkillMap = useCallback(async () => {
    setLoading(true);
    try {
      // Try API first
      const apiData = user?.id && token ? await getUserSkillMap(user.id, token) : null;

      if (apiData && Array.isArray(apiData.skills) && apiData.skills.length > 0) {
        setSkills(apiData.skills);
        setDomainData(aggregateToDomains(apiData.skills));
      } else {
        // Fallback: derive from projects
        const derived = deriveFromProjects(projects);
        setSkills(derived);
        setDomainData(aggregateToDomains(derived));
      }
    } catch {
      const derived = deriveFromProjects(projects);
      setSkills(derived);
      setDomainData(aggregateToDomains(derived));
    } finally {
      setLoading(false);
    }
  }, [user?.id, token, projects]);

  useEffect(() => {
    loadSkillMap();
  }, [loadSkillMap]);

  const filteredSkills = selectedDomain
    ? skills.filter((s) => s.domain === selectedDomain)
    : skills;

  // Empty state
  if (!loading && skills.length === 0) {
    return (
      <motion.div
        className={`${styles.skillMapCard} ${
          theme === "dark" ? styles.dark : styles.light
        }`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className={styles.header}>
          <Map size={20} className={styles.headerIcon} />
          <h3 className={styles.title}>Skill Map</h3>
        </div>
        <div className={styles.emptyState}>
          <TrendingUp size={48} className={styles.emptyIcon} />
          <p className={styles.emptyTitle}>Your skill map is growing!</p>
          <p className={styles.emptyText}>
            Complete projects to see your capabilities mapped across domains.
          </p>
        </div>
      </motion.div>
    );
  }

  if (loading) {
    return (
      <div
        className={`${styles.skillMapCard} ${
          theme === "dark" ? styles.dark : styles.light
        }`}
      >
        <div className={styles.header}>
          <Map size={20} className={styles.headerIcon} />
          <h3 className={styles.title}>Skill Map</h3>
        </div>
        <div className={styles.loadingState}>
          <div className={styles.spinner} />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className={`${styles.skillMapCard} ${
        theme === "dark" ? styles.dark : styles.light
      }`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className={styles.header}>
        <Map size={20} className={styles.headerIcon} />
        <h3 className={styles.title}>Skill Map</h3>
        <span className={styles.skillCount}>
          {skills.length} skill{skills.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Radar Chart */}
      <div className={styles.chartContainer}>
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart outerRadius={90} data={domainData}>
            <PolarGrid stroke={theme === "dark" ? "#374151" : "#e5e7eb"} />
            <PolarAngleAxis
              dataKey="domain"
              tick={{
                fontSize: 12,
                fill: theme === "dark" ? "#d1d5db" : "#374151",
                fontWeight: 500,
              }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{
                fontSize: 10,
                fill: theme === "dark" ? "#9ca3af" : "#6b7280",
              }}
            />
            <Radar
              name="Proficiency"
              dataKey="proficiency"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Domain Pills */}
      <div className={styles.domainPills}>
        <button
          className={`${styles.pill} ${!selectedDomain ? styles.pillActive : ""}`}
          onClick={() => setSelectedDomain(null)}
        >
          All
        </button>
        {domainData.map((d) => {
          const color = DOMAIN_COLORS[d.domain] || DOMAIN_COLORS.Other;
          return (
            <button
              key={d.domain}
              className={`${styles.pill} ${
                selectedDomain === d.domain ? styles.pillActive : ""
              }`}
              style={
                selectedDomain === d.domain
                  ? { backgroundColor: color.fill, color: "#fff" }
                  : {}
              }
              onClick={() =>
                setSelectedDomain(
                  selectedDomain === d.domain ? null : d.domain
                )
              }
            >
              {d.domain}
            </button>
          );
        })}
      </div>

      {/* Skill Detail List */}
      <div className={styles.skillList}>
        <AnimatePresence mode="popLayout">
          {filteredSkills.map((skill) => {
            const color = DOMAIN_COLORS[skill.domain] || DOMAIN_COLORS.Other;
            return (
              <motion.div
                key={skill.name}
                className={styles.skillItem}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <div className={styles.skillInfo}>
                  <span
                    className={styles.skillDot}
                    style={{ backgroundColor: color.fill }}
                  />
                  <span className={styles.skillName}>{skill.name}</span>
                </div>
                <div className={styles.skillBar}>
                  <div
                    className={styles.skillBarFill}
                    style={{
                      width: `${skill.proficiency}%`,
                      backgroundColor: color.fill,
                    }}
                  />
                </div>
                <span className={styles.skillPercent}>
                  {skill.proficiency}%
                </span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default SkillMap;
