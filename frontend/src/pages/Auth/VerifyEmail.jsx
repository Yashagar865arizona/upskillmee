import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import styles from './ForgotPassword.module.css';
import config from '../../config';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('No verification token found in the URL.');
      return;
    }

    fetch(`${config.API_BASE_URL}/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (res.ok) {
          setStatus('success');
          setMessage(data.message || 'Email verified successfully!');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed. The link may have expired.');
        }
      })
      .catch(() => {
        setStatus('error');
        setMessage('Network error. Please try again.');
      });
  }, [searchParams]);

  if (status === 'verifying') {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>&#8987;</div>
          <h1 className={styles.title}>Verifying...</h1>
          <p className={styles.subtitle}>Please wait while we verify your email address.</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <div className={styles.successIcon}>&#10003;</div>
          <h1 className={styles.title}>Email Verified!</h1>
          <p className={styles.subtitle}>
            Your email address has been verified. You can now sign in to upSkillmee.
          </p>
          <Link to="/auth/login" className={styles.submitButton} style={{ display: 'block', textDecoration: 'none', marginTop: 8 }}>
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>&#10007;</div>
        <h1 className={styles.title}>Verification Failed</h1>
        <p className={styles.subtitle}>{message}</p>
        <p className={styles.hint}>
          Need a new link?{' '}
          <Link to="/auth/resend-verification" className={styles.linkBtn}>
            Resend verification email
          </Link>
        </p>
        <Link to="/auth/login" className={styles.backLink}>Back to Sign In</Link>
      </div>
    </div>
  );
};

export default VerifyEmail;
