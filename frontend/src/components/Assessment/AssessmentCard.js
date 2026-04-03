import React from "react";
import styles from "./AssessmentCard.module.css";

const ScoreBadge = ({ label, value }) => {
  const color =
    value >= 80 ? "#22c55e" : value >= 60 ? "#f59e0b" : "#ef4444";
  return (
    <div className={styles.scoreBadge}>
      <span className={styles.scoreValue} style={{ color }}>
        {value}
      </span>
      <span className={styles.scoreLabel}>{label}</span>
    </div>
  );
};

const Section = ({ title, items, emoji }) => {
  if (!items || items.length === 0) return null;
  return (
    <div className={styles.section}>
      <h4 className={styles.sectionTitle}>
        {emoji} {title}
      </h4>
      <ul className={styles.list}>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
};

const AssessmentCard = ({ assessment, onClose }) => {
  if (!assessment) return null;

  const { score, completeness_score, quality_score, skill_alignment_score,
    feedback, strengths, improvements, next_steps, recommended_topics, assessed_at } = assessment;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.card} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>✕</button>

        <h2 className={styles.heading}>Project Assessment</h2>

        <div className={styles.overallScore}>
          <span className={styles.overallValue}>{score}</span>
          <span className={styles.overallLabel}>/ 100</span>
        </div>

        <div className={styles.scoreBadges}>
          {completeness_score != null && (
            <ScoreBadge label="Completeness" value={completeness_score} />
          )}
          {quality_score != null && (
            <ScoreBadge label="Quality" value={quality_score} />
          )}
          {skill_alignment_score != null && (
            <ScoreBadge label="Skill Alignment" value={skill_alignment_score} />
          )}
        </div>

        {feedback && (
          <p className={styles.feedback}>{feedback}</p>
        )}

        <Section title="Strengths" items={strengths} emoji="💪" />
        <Section title="Areas to Improve" items={improvements} emoji="🔧" />
        <Section title="Next Steps" items={next_steps} emoji="🚀" />
        <Section title="Recommended Topics" items={recommended_topics} emoji="📚" />

        {assessed_at && (
          <p className={styles.timestamp}>
            Assessed on {new Date(assessed_at).toLocaleDateString()}
          </p>
        )}
      </div>
    </div>
  );
};

export default AssessmentCard;
