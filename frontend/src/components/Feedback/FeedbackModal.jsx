import React, { useState } from "react";
import styles from "./FeedbackModal.module.css";

const FeedbackModal = ({ isOpen, onClose, onSubmit }) => {
  const [feedbackData, setFeedbackData] = useState({
    type: "general",
    category: "",
    title: "",
    description: "",
    rating: null,
    page_url: window.location.href,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const feedbackTypes = [
    { value: "bug_report", label: "Bug Report" },
    { value: "feature_request", label: "Feature Request" },
    { value: "general", label: "General Feedback" },
    { value: "rating", label: "Rating" },
  ];

  const categories = [
    { value: "ui", label: "User Interface" },
    { value: "performance", label: "Performance" },
    { value: "content", label: "Content" },
    { value: "functionality", label: "Functionality" },
    { value: "other", label: "Other" },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!feedbackData.title.trim() || !feedbackData.description.trim()) {
      alert("Please fill in all required fields");
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        ...feedbackData,
        user_agent: navigator.userAgent,
        metadata: {
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          viewport_size: `${window.innerWidth}x${window.innerHeight}`,
          timestamp: new Date().toISOString(),
        },
      });

      // Reset form
      setFeedbackData({
        type: "general",
        category: "",
        title: "",
        description: "",
        rating: null,
        page_url: window.location.href,
      });

      onClose();
    } catch (error) {
      console.error("Error submitting feedback:", error);
      alert("Failed to submit feedback. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRatingClick = (rating) => {
    setFeedbackData((prev) => ({ ...prev, rating }));
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Share Your Feedback</h2>
          <button className={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.feedbackForm}>
          <div className={styles.formGroup}>
            <label htmlFor="type">Feedback Type *</label>
            <select
              id="type"
              value={feedbackData.type}
              onChange={(e) =>
                setFeedbackData((prev) => ({ ...prev, type: e.target.value }))
              }
              className={styles.select}
            >
              {feedbackTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="category">Category</label>
            <select
              id="category"
              value={feedbackData.category}
              onChange={(e) =>
                setFeedbackData((prev) => ({
                  ...prev,
                  category: e.target.value,
                }))
              }
              className={styles.select}
            >
              <option value="">Select a category</option>
              {categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>

          {feedbackData.type === "rating" && (
            <div className={styles.formGroup}>
              <label>Rating *</label>
              <div className={styles.ratingContainer}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`${styles.starButton} ${
                      feedbackData.rating >= star ? styles.starActive : ""
                    }`}
                    onClick={() => handleRatingClick(star)}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="title">Title *</label>
            <input
              type="text"
              id="title"
              value={feedbackData.title}
              onChange={(e) =>
                setFeedbackData((prev) => ({ ...prev, title: e.target.value }))
              }
              className={styles.input}
              placeholder="Brief summary of your feedback"
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description *</label>
            <textarea
              id="description"
              value={feedbackData.description}
              onChange={(e) =>
                setFeedbackData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              className={styles.textarea}
              placeholder="Please provide detailed feedback..."
              rows={5}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="attachment">Attachment</label>
            <input
              type="file"
              id="attachment"
              onChange={(e) =>
                setFeedbackData((prev) => ({
                  ...prev,
                  attachment: e.target.files[0],
                }))
              }
            />
          </div>

          <div className={styles.formActions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelButton}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Submit Feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FeedbackModal;
