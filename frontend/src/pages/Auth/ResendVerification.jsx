import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './ForgotPassword.module.css';
import config from '../../config';

const ResendVerification = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Something went wrong');
      }

      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to resend. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <div className={styles.successIcon}>&#10003;</div>
          <h1 className={styles.title}>Check Your Email</h1>
          <p className={styles.subtitle}>
            If <strong>{email}</strong> is registered and unverified, a new verification link has been sent.
            The link expires in 24 hours.
          </p>
          <p className={styles.hint}>
            Didn't receive it? Check your spam folder or{' '}
            <button className={styles.linkBtn} onClick={() => setSubmitted(false)}>
              try again
            </button>.
          </p>
          <Link to="/auth/login" className={styles.backLink}>Back to Sign In</Link>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>&#9993;</div>
        <h1 className={styles.title}>Resend Verification</h1>
        <p className={styles.subtitle}>
          Enter your email address and we'll send you a new verification link.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button type="submit" className={styles.submitButton} disabled={isLoading || !email}>
            {isLoading ? 'Sending...' : 'Resend Verification Email'}
          </button>
        </form>

        <Link to="/auth/login" className={styles.backLink}>Back to Sign In</Link>
      </div>
    </div>
  );
};

export default ResendVerification;
