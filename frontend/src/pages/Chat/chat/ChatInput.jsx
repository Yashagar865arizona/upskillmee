import React, { useState } from "react";
import styles from "./Chat.module.css";

export const ChatInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form className={styles.chatInputWrapper} onSubmit={handleSubmit}>
      <div className={styles.inputContainer}>
        <label htmlFor="chatInput" className="visually-hidden">
          Type your message
        </label>
        <input
          id="chatInput"
          type="text"
          className={styles.messageInput}
          placeholder="Type your message..."
          aria-label="Chat message input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
        />
      </div>
      <button
        type="submit"
        className={styles.sendButton}
        aria-label="Send message"
        disabled={!message.trim()}
      >
        <img
          src="https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c01e9e55fca4c6e626a892d0cc292e84871074493a4223a91d4d8cbb5440c6ab?apiKey=6d52bc9029684ea6804919348d39f130&"
          alt=""
          className={styles.sendIcon}
        />
      </button>
    </form>
  );
};
