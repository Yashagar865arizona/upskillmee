import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import config from '../../config';
import styles from './ReferralWidget.module.css';

const ReferralWidget = () => {
  const { user, token } = useAuth();
  const [stats, setStats] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    if (!user?.id || !token) return;
    try {
      const res = await fetch(`${config.API_BASE_URL}/users/${user.id}/referral`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setStats(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch referral stats', err);
    } finally {
      setLoading(false);
    }
  }, [user?.id, token]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const referralLink = stats
    ? `${config.APP_URL}/signup?ref=${stats.referral_code}`
    : '';

  const handleCopy = () => {
    if (!referralLink) return;
    navigator.clipboard.writeText(referralLink).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) return null;
  if (!stats) return null;

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h3 className={styles.title}>Invite Friends &amp; Earn</h3>
        <span className={styles.badge}>1 free month per referral</span>
      </div>

      <div className={styles.linkRow}>
        <input
          className={styles.linkInput}
          value={referralLink}
          readOnly
          aria-label="Your referral link"
        />
        <button className={styles.copyBtn} onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{stats.total_referrals}</span>
          <span className={styles.statLabel}>Invited</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{stats.completed_referrals}</span>
          <span className={styles.statLabel}>Joined</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{stats.rewards_earned}</span>
          <span className={styles.statLabel}>Rewards Earned</span>
        </div>
      </div>
    </div>
  );
};

export default ReferralWidget;
