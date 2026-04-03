import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import styles from './EmailVerificationGate.module.css';
import config from '../../config';

const EmailVerificationGate = () => {
  const { user } = useAuth();
  const [resendStatus, setResendStatus] = useState(null); // null | 'sending' | 'sent' | 'error'

  const handleResend = async () => {
    if (!user?.email) return;
    setResendStatus('sending');
    try {
      const res = await fetch(`${config.API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email }),
      });
      if (res.ok) {
        setResendStatus('sent');
      } else {
        setResendStatus('error');
      }
    } catch {
      setResendStatus('error');
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.card}>
        <div className={styles.icon}>&#9993;</div>
        <h1 className={styles.title}>Verify your email</h1>
        <p className={styles.message}>
          We sent a verification link to <strong>{user?.email}</strong>.
          Please check your inbox and click the link to access the platform.
        </p>
        <p className={styles.expiry}>The link expires in 24 hours.</p>

        {resendStatus === 'sent' && (
          <div className={styles.success}>A new verification email has been sent!</div>
        )}
        {resendStatus === 'error' && (
          <div className={styles.error}>Failed to resend. Please try again.</div>
        )}

        <button
          className={styles.resendButton}
          onClick={handleResend}
          disabled={resendStatus === 'sending' || resendStatus === 'sent'}
        >
          {resendStatus === 'sending' ? 'Sending...' : resendStatus === 'sent' ? 'Email sent!' : 'Resend verification email'}
        </button>

        <p className={styles.hint}>
          Wrong email? Please contact support or sign in with the correct account.
        </p>
      </div>
    </div>
  );
};

export default EmailVerificationGate;
