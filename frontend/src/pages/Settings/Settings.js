import React, { useState, useEffect, useCallback } from "react";
import styles from "./Settings.module.css";

import { Camera } from "lucide-react";
import Avatar from "../../assets/avatar.png";
import { useAuth } from "../../context/AuthContext";
import { debounce } from "lodash";
import PsychometricTest from "./PsychometricTest";
import LoadingSpinner from "../../components/Loading/LoadingSpinner";
import { useTheme } from "../../context/ThemeContext"; 

function Settings() {
  const { darkMode } = useTheme();
  const { user, updateProfile, profileCompletion, refreshUser} = useAuth();
  const showPsychometric = user?.psychometric_status !== "submitted";
  const [profileCompletionData, setProfileCompletionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTest, setShowTest] = useState(false);
const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    username: user?.username || "",
    full_name: user?.full_name || "",
    email: user?.email || "",
    phone_number: user?.phone_number || "",
    country: user?.country || "",
    city: user?.city || "",
  });

  const [profileImage, setProfileImage] = useState(null);
  const [file, setFile] = useState(null);

  const countries = {
    India: ["Kolkata", "Delhi", "Mumbai", "Bangalore"],
    USA: ["New York", "San Francisco", "Chicago"],
    UK: ["London", "Manchester", "Birmingham"],
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFile(file);
      setProfileImage(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile(form, file);
      await refreshUser();
      alert("Profile updated successfully!");
    } catch (err) {
      console.error(err);
      alert(err.message);
    } finally {
      setSaving(false); 
    }
  };

  useEffect(() => {
    const fetchProfileCompletion = async () => {
      try {
        const data = await profileCompletion();
        setProfileCompletionData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
        
      }
    };
    fetchProfileCompletion();
  }, []);

  if (loading) {
    return (
      <div className={styles.loaderWrapper}>
        <LoadingSpinner size="large" text="Loading your profile..." fullScreen={true} />
      </div>
    );
  }

  if (error) {
    return <div className={styles.error}>Error: {error}</div>;
  }

  if (showTest) {
    return <PsychometricTest onComplete={() => setShowTest(false)} />;
  }

  return (
    <div className={`${styles.page} ${darkMode ? styles.dark : styles.light}`}>
      {/* Left Column */}
      <aside className={styles.leftColumn}>
        <div className={styles.profileSection}>
          <div className={styles.profileImageWrapper}>
            <img
              src={
                profileImage ||
                (user?.photo_url ? encodeURI(user.photo_url) : Avatar)
              }
              alt="Profile"
              className={styles.profileImage}
            />
            <label className={styles.uploadIcon}>
              <Camera size={20} />
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                hidden
              />
            </label>
          </div>
          <h3 className={styles.userName}>{form.full_name || ""}</h3>
          <p className={styles.userEmail}>{form.email || ""}</p>
        </div>

        {showPsychometric && (
          <div className={styles.testCard}>
            <h3>🧠 Psychometric Test</h3>
            <p>Take this short test to personalize your experience.</p>
            <button
              className={styles.takeTestBtn}
              onClick={() => setShowTest(true)}
            >
              Take Psychometric Test
            </button>
          </div>
        )}
      </aside>

      {/* Right Column */}
      <main className={styles.rightColumn}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <h4>Personal Information</h4>
          <div className={styles.row}>
            <label>Username</label>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter your username"
            />
          </div>

          <div className={styles.row}>
            <label>Full Name</label>
            <input
              type="text"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              placeholder="Enter your full name"
            />
          </div>

          <div className={styles.row}>
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter your email"
            />
          </div>

          <div className={styles.row}>
            <label>Phone Number</label>
            <input
              type="text"
              name="phone_number"
              value={form.phone_number}
              onChange={handleChange}
              placeholder="Enter your phone number"
            />
          </div>

         
          <div className={styles.row}>
            <label>Country</label>
            <select name="country" value={form.country} onChange={handleChange}>
              <option value="">Select country</option>
              {Object.keys(countries).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {form.country && (
            <div className={styles.row}>
              <label>City</label>
              <select name="city" value={form.city} onChange={handleChange}>
                <option value="">Select city</option>
                {countries[form.country].map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button type="submit" className={styles.saveButton}>
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default Settings;
