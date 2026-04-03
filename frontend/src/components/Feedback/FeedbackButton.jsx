import React, {useState } from 'react';
import FeedbackModal from './FeedbackModal';
import styles from './FeedbackButton.module.css';
import config from '../../config';
import { toast } from "react-toastify";
import { useAuth } from '../../context/AuthContext';

const FeedbackButton = ({ position = 'bottom-right', variant = 'floating' }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {token}=useAuth()
  
const submitFeedback = async (feedbackData, attachment) => {
  const formData = new FormData();
  formData.append("feedback_type", feedbackData.type);
  formData.append("category", feedbackData.category);
  formData.append("title", feedbackData.title);
  formData.append("description", feedbackData.description);
  if (feedbackData.rating) formData.append("rating", feedbackData.rating);
  formData.append("page_url", feedbackData.page_url);
  formData.append("user_agent", feedbackData.user_agent);

  if (attachment) {
    formData.append("attachment", attachment);
  }

  const response = await fetch(`${config.API_BASE_URL}/feedback/`, {
    method: "POST",
    headers: {
      
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to submit feedback");
  }

  return response.json();
};


const handleSubmitFeedback = async (feedbackData) => {
  setIsSubmitting(true);
  try {
    await submitFeedback(feedbackData, feedbackData.attachment);
    toast.success("Thank you for your feedback!");
  } catch (error) {
    console.error("Error submitting feedback:", error);

    toast.error("Failed to submit feedback. Please try again.");
    throw error;
  } finally {
    setIsSubmitting(false);
  }
};


  const buttonClasses = [
    styles.feedbackButton,
    styles[variant],
    styles[position]
  ].join(' ');

  return (
    <>
      <button
        className={buttonClasses}
        onClick={() => setIsModalOpen(true)}
        disabled={isSubmitting}
        title="Share your feedback"
      >
        {variant === 'floating' ? (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        ) : (
          'Feedback'
        )}
      </button>

      <FeedbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmitFeedback}
      />
    </>
  );
};

export default FeedbackButton;