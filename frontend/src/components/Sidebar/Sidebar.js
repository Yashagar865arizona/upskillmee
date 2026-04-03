import React, { memo, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import styles from "./Sidebar.module.css";
import { Home, MessageSquare, Folder, Settings, Sun, Moon } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import Avatar from "../../assets/avatar.png";
import { RiDashboardLine, RiCalendarLine } from "react-icons/ri";
import { BiMessageSquareDetail, BiCubeAlt } from "react-icons/bi"; 
import { RiSunLine, RiMoonLine } from "react-icons/ri";
import { FiMenu } from "react-icons/fi";
import { FiX } from "react-icons/fi"; 


const Sidebar = memo(function Sidebar({ collapsed = false, onToggle }) {
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const percentage = localStorage.getItem('profileCompletion');
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user, profileCompletion } = useAuth();
  const { darkMode, toggleTheme } = useTheme();

  const [completion, setCompletion] = useState(0);
useEffect(() => {
  const fetchProfileCompletion = async () => {
    try {
      const data = await profileCompletion();
      console.log("Profile completion data:", data);
      setCompletion(data?.completion_percentage || 0);
      
    } catch (error) {
      console.error("Failed to fetch profile completion", error);
    }
  };
  fetchProfileCompletion();
}, [profileCompletion]);


  const navigationItems = [
    {
      icon: RiDashboardLine,
      label: "Dashboard",
      href: "/dashboard",
      active: location.pathname === "/dashboard",
    },
    {
      icon: BiMessageSquareDetail,
      label: "Chat",
      href: "/chat",
      active: location.pathname === "/chat",
    },
    {
      icon: BiCubeAlt,
      label: "Projects",
      href: "/projects",
      active: location.pathname === "/projects",
    },
    {
      icon: RiCalendarLine,
      label: "Calendar",
      href:"/calendar",
      active: location.pathname === "/calendar"
    }
  ];

  const handleLogout = (e) => {
    e.preventDefault();
    logout();
    navigate("/auth/login");
    setShowSettingsMenu(false);
  };

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        {!collapsed && (
          <div className={styles.logoContainer}>
            <div className={styles.logoBox}>
              <span className={styles.logoText}>U</span>
            </div>
            <div>
              <h1 className={styles.brand}>upSkillmee</h1>
              <p className={styles.subtitle}>AI Learning Mentor</p>
            </div>
          </div>
        )}
        <button onClick={onToggle} className={styles.toggleBtn}>
           {collapsed ? <FiMenu size={22} /> : <FiX size={22} />}
        </button>
      </div>

      <div className={styles.navSection}>
        <nav className={styles.navList}>
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <Link
                key={item.label}
                to={item.href}
                className={`${styles.navItem} ${
                  item.active ? styles.active : ""
                }`}
              >
                <IconComponent
                  size={18}
                  color={darkMode ? "#ffffff" : "#111827"}
                />
                {!collapsed && (
                  <span className={styles.navLabel}>{item.label}</span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className={styles.footer}>
        <div
          className={`${styles.profileRow} ${collapsed ? styles.centered : ""}`}
        >
          {!collapsed && (
            <Link to="/profile" className={styles.profileLink}>
              <img
                src={
                  user?.photo_url ? encodeURI(user.photo_url) : Avatar
                }
                alt="User"
                className={styles.avatar}
              />
              <div className={styles.userInfo}>
                <p className={styles.userName}>
                  {user?.full_name?.split(" ")[0] || "User"}
                </p>
              </div>
            </Link>
          )}
          {!collapsed && (
            <button onClick={toggleTheme} className={styles.iconBtn}>
              {darkMode ? (
                <RiSunLine size={18} color="#ffffff" />
              ) : (
                <RiMoonLine size={18} color="#111827" />
              )}
            </button>
          )}

          <div className={styles.settingsWrapper}>
            <button
              onClick={() => setShowSettingsMenu((prev) => !prev)}
              className={styles.iconBtn}
            >
              <Settings size={18} color={darkMode ? "#ffffff" : "#111827"} />
            </button>

            {showSettingsMenu && (
              <div className={styles.settingsMenu}>
                <button
                  className={styles.menuItem}
                  onClick={() => {
                    navigate("/settings");
                    setShowSettingsMenu(false);
                  }}
                >
                  View Profile
                </button>
                <button className={styles.menuItem} onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Profile Completion Bar */}
      {!collapsed && (
        <div className={styles.completionContainer}>
          <p className={styles.completionLabel}>Profile Completion</p>
          <div className={styles.completionBar}>
            <div
              className={styles.completionFill}
              style={{ width: `${completion || percentage}%` }}
            ></div>
          </div>
          {/* <p className={styles.completionPercentage}>{completion}%</p> */}
        </div>
      )}
    </div>
  );
});

export default Sidebar;
