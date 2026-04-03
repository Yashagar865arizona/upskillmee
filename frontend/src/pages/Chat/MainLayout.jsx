import React, { useState } from "react";
import { ChatContainer } from "./chat/ChatContainer";
import { ProjectBoard } from "./projectBoard/ProjectBoard";
import { useLearningPlan } from "./context/LearningPlanContext";
import styles from "./MainLayout.module.css";
import { useTheme } from "../../context/ThemeContext";
import { motion, AnimatePresence } from "framer-motion";
import {  FiChevronsLeft, FiChevronsRight } from "react-icons/fi";

export const MainLayout = () => {
  const { projects } = useLearningPlan();
  const { darkMode } = useTheme();
  const [isProjectBoardVisible, setIsProjectBoardVisible] = useState(true);

  // Toggle project board
  const toggleProjectBoard = () => {
    setIsProjectBoardVisible((prev) => !prev);
  };

  if (!projects || projects.length === 0) {
    return (
      <div className={styles.chatOnlyLayout}>
        <ChatContainer />
      </div>
    );
  }

  return (
    <div className={styles.layout}>
     
      <AnimatePresence>
        {isProjectBoardVisible && (
          <motion.div
            className={styles.leftPanel}
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <ProjectBoard />
          </motion.div>
        )}
      </AnimatePresence>

    
      <div className={styles.centerPanel}>
        <div className={styles.toggleIcon} onClick={toggleProjectBoard}>
          {isProjectBoardVisible ? (
            <FiChevronsLeft
              size={26}
              color={darkMode ? "#fff" : "#333"}
              title="Hide Project Board"
            />
          ) : (
            <FiChevronsRight
              size={26}
              color={darkMode ? "#fff" : "#333"}
              title="Show Project Board"
            />
          )}
        </div>
        <ChatContainer />
      </div>
    </div>
  );
};
