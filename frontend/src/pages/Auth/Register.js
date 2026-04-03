import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import styles from "./Auth.module.css";
import Apple from "../../assets/apple.png";
import Google from "../../assets/google.png";
import Microsoft from "../../assets/microsoft.png";
import Github from "../../assets/github.png";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";

const Register = () => {
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [usernameSuggestions, setUsernameSuggestions] = useState([]);
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [otp, setOtp] = useState({ email: "", phoneNumber: "" });
  const [isOtp, setIsOtp] = useState({ email: false, phoneNumber: false });
  const [isVerifying, setIsVerifying] = useState({
    email: false,
    phoneNumber: false,
  });
  const [isResending, setIsResending] = useState({
    email: false,
    phoneNumber: false,
  });

  const { register, sendOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!name) {
      setUsernameSuggestions([]);
      return;
    }

    const parts = name.toLowerCase().split(" ");
    const first = parts[0] || "";
    const last = parts[parts.length - 1] || "";

    const randomNum = (max = 99) => Math.floor(Math.random() * max) + 1;
    const randomLetter = () =>
      String.fromCharCode(97 + Math.floor(Math.random() * 26));
    const symbols = ["_", "."];

    setUsernameSuggestions([
      `${first}${randomNum()}`,
      `${first}${randomLetter()}${randomNum()}`,
      `${first}${
        symbols[Math.floor(Math.random() * symbols.length)]
      }${randomNum()}`,
      `${first.substring(0, 3)}${last.substring(0, 2)}${randomNum(99)}`,
    ]);
  }, [name]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Check if email and phone are verified
    if (isOtp.email !== "verified" || isOtp.phoneNumber !== "verified") {
      setError("Please verify your email and phone number before registering.");
      return;
    }
    const emailVerified = isOtp.email === "verified";
    const phoneVerified = isOtp.phoneNumber === "verified";

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await register(
        email,
        password,
        name,
        username,
        phoneNumber,
        emailVerified,
        phoneVerified
      );
      navigate("/onboarding");
    } catch (err) {
      setError(err.message || "Failed to create account");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthClick = (provider) => {
    console.log(`OAuth login with ${provider} clicked`);
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <h1>Create Account</h1>
        <p>Join Ponder to start your learning journey</p>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Full Name */}
          <div className={styles.formGroup}>
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Enter your full name"
              className={styles.input}
            />
          </div>

          {/* Username */}
          <div className={styles.formGroup}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Choose a username"
              className={styles.input}
            />
            {usernameSuggestions.length > 0 && !username && (
              <div className={styles.suggestions}>
                <small>Suggestions:</small>
                <div className={styles.suggestionList}>
                  {usernameSuggestions.map((u) => (
                    <span
                      key={u}
                      className={styles.suggestionItem}
                      onClick={() => setUsername(u)}
                    >
                      {u}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Email */}
          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <div style={{ display: "flex", alignItems: "center" }}>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setIsOtp({ ...isOtp, email: false }); 
                }}
                required
                placeholder="Enter your email"
                style={{ flex: 1 }}
                className={styles.input}
              />
              {isOtp.email === "verified" ? (
                <button className={styles.submitButton} disabled>
                  Verified
                </button>
              ) : (
                <button
                  type="button"
                  className={styles.submitButton}
                  disabled={isLoading || !email}
                  onClick={async () => {
                    setIsResending({ ...isResending, email: true });
                    try {
                      await sendOtp(email);
                      setIsOtp({ ...isOtp, email: true });
                    } catch (err) {
                      setError(err.message || "Failed to send OTP");
                    } finally {
                      setIsResending({ ...isResending, email: false });
                    }
                  }}
                >
                  {isResending.email ? "Sending..." : "Send OTP"}
                </button>
              )}
            </div>

            {/* Render OTP input only if email is sent but not yet verified */}
            {isOtp.email && isOtp.email !== "verified" && (
              <div style={{ marginTop: "8px", display: "flex", gap: "8px" }}>
                <input
                  type="text"
                  value={otp.email}
                  onChange={(e) => setOtp({ ...otp, email: e.target.value })}
                  placeholder="Enter OTP"
                  style={{ flex: 1 }}
                  className={styles.input}
                />
                <button
                  type="button"
                  className={styles.submitButton}
                  onClick={async () => {
                    setIsVerifying({ ...isVerifying, email: true });
                    try {
                      await verifyOtp(email, otp.email);
                      setIsOtp({ ...isOtp, email: "verified" }); // Mark as verified
                      setError("");
                    } catch (err) {
                      setError(err.message || "OTP verification failed");
                    } finally {
                      setIsVerifying({ ...isVerifying, email: false });
                    }
                  }}
                >
                  Verify
                </button>
              </div>
            )}
          </div>

          {/* Phone */}

          <div className={styles.formGroup}>
            <label htmlFor="phoneNumber">Phone Number</label>
            <div style={{ display: "flex", alignItems: "center" }}>
              <input
                id="phoneNumber"
                type="tel"
                value={phoneNumber}
                onChange={(e) => {
                  setPhoneNumber(e.target.value);
                  setIsOtp({ ...isOtp, phoneNumber: false });
                }}
                required
                placeholder="Enter your phone number"
                style={{ flex: 1 }}
                className={styles.input}
              />
              {isOtp.phoneNumber === "verified" ? (
                <button className={styles.submitButton} disabled>
                  Verified
                </button>
              ) : (
                <button
                  type="button"
                  className={styles.submitButton}
                  disabled={isLoading || !phoneNumber}
                  onClick={async () => {
                    setIsResending({ ...isResending, phoneNumber: true });
                    try {
                      await sendOtp(phoneNumber, "phone"); 
                      setIsOtp({ ...isOtp, phoneNumber: true });
                    } catch (err) {
                      setError(err.message || "Failed to send OTP");
                    } finally {
                      setIsResending({ ...isResending, phoneNumber: false });
                    }
                  }}
                >
                  {isResending.phoneNumber ? "Sending..." : "Send OTP"}
                </button>
              )}
            </div>

            {/* Render OTP input only if phone OTP sent but not verified */}
            {isOtp.phoneNumber && isOtp.phoneNumber !== "verified" && (
              <div style={{ marginTop: "8px", display: "flex", gap: "8px" }}>
                <input
                  type="text"
                  value={otp.phoneNumber}
                  onChange={(e) =>
                    setOtp({ ...otp, phoneNumber: e.target.value })
                  }
                  placeholder="Enter OTP"
                  style={{ flex: 1 }}
                  className={styles.input}
                />
                <button
                  type="button"
                  className={styles.submitButton}
                  onClick={async () => {
                    setIsVerifying({ ...isVerifying, phoneNumber: true });
                    try {
                      await verifyOtp(phoneNumber, otp.phoneNumber, "phone"); // distinguish type
                      setIsOtp({ ...isOtp, phoneNumber: "verified" });
                      setError("");
                    } catch (err) {
                      setError(err.message || "OTP verification failed");
                    } finally {
                      setIsVerifying({ ...isVerifying, phoneNumber: false });
                    }
                  }}
                >
                  Verify
                </button>
              </div>
            )}
          </div>

          {/* Password */}
          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <div className={styles.passwordWrapper}>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Create a password"
                minLength={8}
                className={styles.input}
              />
              <span
                className={styles.eyeIcon}
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <AiOutlineEyeInvisible /> : <AiOutlineEye />}
              </span>
            </div>
          </div>

          {/* Confirm Password */}
          <div className={styles.formGroup}>
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className={styles.passwordWrapper}>
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Confirm your password"
                minLength={8}
                className={styles.input}
              />
              <span
                className={styles.eyeIcon}
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <AiOutlineEyeInvisible />
                ) : (
                  <AiOutlineEye />
                )}
              </span>
            </div>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
          >
            {isLoading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        {/* OAuth */}
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
            Already have an account? <Link to="/auth/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
