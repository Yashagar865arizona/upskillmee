import React from "react";
import { ChatContainer } from "./chat/ChatContainer";
import { ProjectBoard } from "./projectBoard/ProjectBoard";
import styles from "./Chat.module.css";
import { useLearningPlan } from "./context/LearningPlanContext";

export const Chat = () => {
    const { projects } = useLearningPlan(); 
  const hasProjects = projects && projects.length > 0;

  return (
    <div className={styles.chatLayout}>
      {hasProjects && (
        <div className={styles.boardContainer}>
          <ProjectBoard />
        </div>
      )}
      <div className={styles.messagesContainer}>
        <div className={styles.chatBox}>
          <ChatContainer />
        </div>
      </div>
    </div>
  );
};
