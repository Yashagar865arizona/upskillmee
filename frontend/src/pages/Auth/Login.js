import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import styles from "./Auth.module.css";
import ForgotPasswordModal from "./ForgotPasswordModal";
import Apple from "../../assets/apple.png";
import Google from "../../assets/google.png";
import Microsoft from "../../assets/microsoft.png";
import Github from "../../assets/github.png";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";

const Login = () => {
  const [emailOrPhone, setEmailOrPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login, googleLogin } = useAuth();
  const navigate = useNavigate();

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login(emailOrPhone, password);
      navigate("/dashboard");
    } catch (err) {
      const msg = err.message || "";
      if (msg.toLowerCase().includes("not verified") || msg.toLowerCase().includes("verify your email")) {
        navigate("/auth/resend-verification");
        return;
      }
      setError(msg || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthClick = (provider) => {
    if (provider === "google") {
      googleLogin()
        .then(() => navigate("/dashboard"))
        .catch(() => setError("Google login failed"));
    } else {
      setError(`${provider} login coming soon`);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <h1>Welcome Back</h1>
        <p>Sign in to continue your learning journey</p>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handlePasswordLogin} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="emailOrPhone">Email or Phone</label>
            <input
              id="emailOrPhone"
              type="text"
              value={emailOrPhone}
              onChange={(e) => setEmailOrPhone(e.target.value)}
              required
              placeholder="Enter your email or phone"
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <div className={styles.passwordWrapper}>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className={styles.input}
              />
              <span
                className={styles.eyeIcon}
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <AiOutlineEyeInvisible /> : <AiOutlineEye />}
              </span>
            </div>
            <small
              className={styles.forgotLink}
              onClick={() => setShowForgotPassword(true)}
            >
              Forgot Password?
            </small>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
          >
            {isLoading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <div className={styles.oauthSection}>
          <p className={styles.orText}>or continue with</p>
          <div className={styles.oauthButtons}>
            <button
              onClick={() => handleOAuthClick("google")}
              className={styles.oauthButton}
            >
              <img src={Google} alt="Google" /> Google
            </button>
            <button
              onClick={() => handleOAuthClick("github")}
              className={styles.oauthButton}
            >
              <img src={Github} alt="GitHub" /> GitHub
            </button>
            <button
              onClick={() => handleOAuthClick("microsoft")}
              className={styles.oauthButton}
            >
              <img src={Microsoft} alt="Microsoft" /> Microsoft
            </button>
            <button
              onClick={() => handleOAuthClick("apple")}
              className={styles.oauthButton}
            >
              <img src={Apple} alt="Apple" /> Apple
            </button>
          </div>
        </div>

        <div className={styles.links}>
          <p>
            Don’t have an account?{" "}
            <Link to="/auth/register">Create Account</Link>
          </p>
        </div>
      </div>

      {showForgotPassword && (
        <ForgotPasswordModal onClose={() => setShowForgotPassword(false)} />
      )}
    </div>
  );
};

export default Login;
