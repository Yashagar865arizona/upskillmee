import React, { useEffect, useState } from "react";
import Confetti from "react-confetti";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import styles from "./Onboarding.module.css";

const CompletionPopup = () => {
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(true);

  useEffect(() => {
   
    const confettiTimer = setTimeout(() => setShowConfetti(false), 5000);


    const redirectTimer = setTimeout(() => navigate("/dashboard"), 6000);

    return () => {
      clearTimeout(confettiTimer);
      clearTimeout(redirectTimer);
    };
  }, [navigate]);

  return (
    <div className={styles.overlaycomplition}>
      {/* Gradient background */}
      <div className={styles.gradientBg}></div>

      {/* Confetti */}
      {showConfetti && (
        <Confetti
          numberOfPieces={400}
          recycle={false}
          style={{
            pointerEvents: "none",
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            zIndex: 1,
          }}
        />
      )}

      {/* Card */}
      <motion.div
        className={styles.card}
        initial={{ scale: 0.7, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 120, damping: 12 }}
      >
        <motion.div
          className={styles.ring}
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
        />

        <motion.div
          className={styles.checkCircle}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 10 }}
        >
          🎉
        </motion.div>

        <h2 className={styles.title}>Welcome to the Dashboard!</h2>
        <p className={styles.subtitle}>
          You’ve successfully completed onboarding. <br />
          Preparing your dashboard...
        </p>

        <motion.div
          className={styles.progressBar}
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 4 }}
        />

        <div className={styles.iconRow}>
          <motion.span animate={{ y: [0, -12, 0] }} transition={{ repeat: Infinity, duration: 2 }}>🤖</motion.span>
          <motion.span animate={{ y: [0, -12, 0] }} transition={{ repeat: Infinity, duration: 2, delay: 0.3 }}>📚</motion.span>
          <motion.span animate={{ y: [0, -12, 0] }} transition={{ repeat: Infinity, duration: 2, delay: 0.6 }}>✨</motion.span>
          <motion.span animate={{ y: [0, -12, 0] }} transition={{ repeat: Infinity, duration: 2, delay: 0.9 }}>💡</motion.span>
        </div>
      </motion.div>
    </div>
  );
};

export default CompletionPopup;
