import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import styles from "./Auth.module.css";

const ForgotPasswordModal = ({ onClose }) => {
  const [emailOrPhone, setEmailOrPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

const { sendOtp, verifyOtp, resetPasswordWithOtp } = useAuth();


  const handleSendOtp = async () => {
    setError("");
    setIsLoading(true);
    try {
      await sendOtp(emailOrPhone);
      setStep(2);
    } catch (err) {
      setError(err.message || "Failed to send OTP");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    setError("");
    setIsLoading(true);
    try {
      await verifyOtp(emailOrPhone, otp);
      setStep(3);
    } catch (err) {
      setError(err.message || "Invalid OTP");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    setError("");
    setIsLoading(true);
    try {
      await resetPasswordWithOtp(emailOrPhone, otp, newPassword);
      alert("Password changed successfully!");
      onClose();
    } catch (err) {
      setError(err.message || "Failed to reset password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalCard}>
        <div className={styles.modalHeader}>
          <h2>🔐 Reset Password</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            ✖
          </button>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.modalContent}>
          {step === 1 && (
            <>
              <p className={styles.infoText}>
                Enter your <b>email</b> or <b>phone number</b> to receive an OTP.
              </p>
              <input
                type="text"
                placeholder="Email or Phone"
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                className={styles.input}
              />
              <button
                className={styles.primaryBtn}
                onClick={handleSendOtp}
                disabled={isLoading || !emailOrPhone}
              >
                {isLoading ? "Sending..." : "Send OTP"}
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <p className={styles.infoText}>Enter the OTP sent to your email/phone.</p>
              <input
                type="text"
                placeholder="Enter OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className={styles.input}
              />
              <button
                className={styles.primaryBtn}
                onClick={handleVerifyOtp}
                disabled={isLoading || !otp}
              >
                {isLoading ? "Verifying..." : "Verify OTP"}
              </button>
              <button
                className={styles.secondaryBtn}
                onClick={handleSendOtp}
                disabled={isLoading}
              >
                Resend OTP
              </button>
            </>
          )}

          {step === 3 && (
            <>
              <p className={styles.infoText}>Enter your new password below.</p>
              <input
                type="password"
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={styles.input}
              />
              <button
                className={styles.primaryBtn}
                onClick={handleResetPassword}
                disabled={isLoading || !newPassword}
              >
                {isLoading ? "Resetting..." : "Reset Password"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordModal;
