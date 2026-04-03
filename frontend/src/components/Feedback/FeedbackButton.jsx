import React, { useState } from 'react';
import FeedbackModal from './FeedbackModal';
import styles from './FeedbackButton.module.css';
import config from '../../config';
import { toast } from 'react-toastify';
import { useAuth } from '../../context/AuthContext';

const FeedbackButton = ({ position = 'bottom-right' }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { token } = useAuth();

  const handleSubmit = async ({ category, body }) => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/feedback/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ category, body }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to submit feedback');
      }

      toast.success('Thanks for your feedback!');
    } catch (error) {
      toast.error('Failed to submit feedback. Please try again.');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const buttonClasses = [
    styles.feedbackButton,
    styles.floating,
    styles[position],
  ].join(' ');

  return (
    <>
      <button
        className={buttonClasses}
        onClick={() => setIsModalOpen(true)}
        disabled={isSubmitting}
        title="Share your feedback"
        aria-label="Open feedback form"
      >
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
      </button>

      <FeedbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </>
  );
};

export default FeedbackButton;
