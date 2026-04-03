import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import styles from "./Psychometric.module.css";
import { useUser } from "../../context/UserContext";
import { useTheme } from "../../context/ThemeContext";
import LoadingSpinner from "../../components/Loading/LoadingSpinner";

function PsychometricTest({ onComplete }) {
  const { fetchQuestions, submitResponses } = useUser();
  const { darkMode } = useTheme();
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showPopup, setShowPopup] = useState(false);

  const containerRef = useRef();
  const questionRefs = useRef([]);

  const navigate = useNavigate();

  const options = [0, 1, 2, 3, 4, 5, 6];
  const circleSizes = [60, 50, 40, 28, 40, 50, 60];

  const borderColors = [
    "#8a63d2",
    "#a569f7",
    "#9b82ff",
    "#ccc",
    "#7bb4ff",
    "#63a4ff",
    "#0099ff",
  ];

  useEffect(() => {
    questionRefs.current = questionRefs.current.slice(0, questions.length);
  }, [questions]);

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const q = await fetchQuestions();
        if (q?.length > 0) setQuestions(q);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadQuestions();
  }, [fetchQuestions]);

  const handleSelect = (qIndex, optionIndex) => {
    const qId = questions[qIndex].id;
    setResponses((prev) => ({ ...prev, [qId]: optionIndex }));

    if (qIndex < questions.length - 1) {
      setTimeout(() => {
        const nextIndex = qIndex + 1;
        setCurrentIndex(nextIndex);
        questionRefs.current[nextIndex]?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 500);
    } else {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    try {
      await submitResponses(responses);
      setShowPopup(true);
      onComplete?.();

      
      setTimeout(() => {
        navigate(-1);
      }, 2000);
    } catch (err) {
      console.error(err);
    }
  };
if (loading) {
    return (
      <div className={styles.loaderWrapper}>
        <LoadingSpinner size="large" text="Loading your profile..." fullScreen={true} />
      </div>
    );
  }
  
  if (!questions || questions.length === 0)
    return <div className={styles.loading}>No psychometric test available.</div>;

  return (
    <div
      className={`${styles.container} ${darkMode ? styles.dark : ""}`}
      ref={containerRef}
    >
      {/* Header */}
      <motion.div
        className={styles.header}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className={styles.title}>🧠 Psychometric Test</h1>
        <p className={styles.subtitle}>
          Answer quick questions to personalize your experience.
        </p>
      </motion.div>

      {/* Progress Bar */}
      <div className={styles.progressBarContainer}>
        <motion.div
          className={styles.progressBar}
          initial={{ width: 0 }}
          animate={{
            width: `${((currentIndex + 1) / questions.length) * 100}%`,
          }}
          transition={{ duration: 0.4 }}
        />
      </div>

      <div className={styles.progressInfo}>
        <p className={styles.progressText}>
          {Math.round(((currentIndex + 1) / questions.length) * 100)}%
        </p>
        <p className={styles.progressText}>
          Question {currentIndex + 1} of {questions.length}
        </p>
      </div>

      {/* Questions */}
      {questions.map((question, index) => {
        const selectedIndex = responses[question.id];
        const isActive = index === currentIndex;
        const isDisabled = index === currentIndex + 1;

        if (!isActive && !isDisabled) return null;

        return (
          <motion.div
            key={question.id}
            ref={(el) => (questionRefs.current[index] = el)}
            className={`${styles.card} ${isDisabled ? styles.disabled : ""}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className={styles.questionLabel}>
              <span>Question {index + 1}</span>
            </div>

            <div className={styles.questionText}>
              <div className={styles.iconWrapper}>
                <span role="img" aria-label="user">
                  🧑
                </span>
              </div>
              {question.text}
            </div>

            <div className={styles.sliderWrapper}>
              <div className={styles.sliderLine}>
                {options.map((opt, idx) => {
                  const isSelected = selectedIndex === idx;
                  const color = borderColors[idx];
                  const nextLineColor =
                    idx < borderColors.length - 1 ? borderColors[idx + 1] : "#ccc";

                  const circleStyle = {
                    border: `3px solid ${color}`,
                    background: isSelected ? color : "#fff",
                    cursor: isActive ? "pointer" : "not-allowed",
                    opacity: isDisabled ? 0.5 : 1,
                  };

                  return (
                    <React.Fragment key={idx}>
                      <div
                        className={styles.circle}
                        onClick={() => isActive && handleSelect(index, idx)}
                        style={{
                          width: `${circleSizes[idx]}px`,
                          height: `${circleSizes[idx]}px`,
                          ...circleStyle,
                        }}
                      />
                      {idx < options.length - 1 && (
                        <div
                          className={styles.line}
                          style={{
                            background: nextLineColor,
                          }}
                        />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              <div className={styles.sliderLabels}>
                <span>AGREE</span>
                <span>DISAGREE</span>
              </div>
            </div>
          </motion.div>
        );
      })}

      
      {showPopup && (
        <div className={styles.successPopup}>
          🎉 Test Completed Successfully! Redirecting...
        </div>
      )}
    </div>
  );
}

export default PsychometricTest;
