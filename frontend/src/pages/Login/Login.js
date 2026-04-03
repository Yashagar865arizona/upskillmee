// src/pages/Login/Login.js
import React, { useContext, useState } from 'react';
import styles from './Login.module.css';
import { AuthContext } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const { email, password } = formData;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Implement authentication logic here (e.g., API call)
    // For now, we'll simulate successful login
    console.log('Logged in:', formData);
    login(); // Update auth state
    navigate('/'); // Redirect to Dashboard
  };

  return (
    <div className={styles.login}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={email}
          onChange={handleChange}
          required
          className={styles.input}
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={password}
          onChange={handleChange}
          required
          className={styles.input}
        />
        <button type="submit" className={styles.button}>
          Login
        </button>
      </form>
      <p>
        Don't have an account?{' '}
        <a href="/register" className={styles.link}>
          Register here
        </a>
      </p>
    </div>
  );
};

export default Login;