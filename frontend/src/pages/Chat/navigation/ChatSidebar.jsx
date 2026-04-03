import * as React from "react";
import styles from './ChatSidebar.module.css';

const editingActions = [
  { title: "Change the Schedule", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Restart Personalization", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Ask AI Mentor Anything", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" }
];

const learningActions = [
  { title: "Recommend Online Course", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Networking with Local Founders", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Interview Interesting People", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" }
];

const projectActions = [
  { title: "Start a Marketing Agency", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Start a E-commerce Store", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" },
  { title: "Start a Social Media Channel", icon: "https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/c72d19eee2c9ba6ec13c3e460e03366a5ab4d2fa06a5e796a09e8cbe98a75b56?apiKey=6d52bc9029684ea6804919348d39f130&" }
];

export const ChatSidebar = () => {
  const wrapperRef = React.useRef();
  const observerRef = React.useRef();

  React.useEffect(() => {
    // Don't proceed if wrapper ref is not available
    if (!wrapperRef.current) return;

    const options = {
      root: wrapperRef.current,
      rootMargin: '0px',
      threshold: 0.3,
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add(styles.visible);
        } else {
          entry.target.classList.remove(styles.visible);
        }
      });
    }, options);

    observerRef.current = observer;

    const sections = wrapperRef.current.querySelectorAll(`.${styles.sectionContainer}`);
    if (sections) {
      sections.forEach(section => observer.observe(section));
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  return (
    <div className={styles.sidebarContainer}>
      <div className={styles.sidebarWrapper} ref={wrapperRef}>
        <div className={styles.sectionContainer}>
          <div className={styles.sectionHeader}>
            <h3 className={styles.sectionTitle}>Editing</h3>
          </div>
          <div className={styles.actionsList}>
            {editingActions.map((action, index) => (
              <button
                key={index}
                className={styles.actionButton}
                tabIndex={0}
                aria-label={action.title}
                onClick={() => {}}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                  }
                }}
              >
                <span className={styles.actionText}>{action.title}</span>
                <div className={styles.iconContainer}>
                  <img
                    className={styles.actionIcon}
                    src={action.icon}
                    alt=""
                    aria-hidden="true"
                  />
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.sectionContainer}>
          <div className={styles.sectionHeader}>
            <img
              className={styles.headerIcon}
              src="https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/741d5a9e524fc64b063bdf375b8e9db9c550a6f2f64c801d0947a929152d3f6c?apiKey=6d52bc9029684ea6804919348d39f130&"
              alt=""
              aria-hidden="true"
            />
            <h3 className={styles.sectionTitle}>More Learnings</h3>
          </div>
          <div className={styles.actionsList}>
            {learningActions.map((action, index) => (
              <button
                key={index}
                className={styles.actionButton}
                tabIndex={0}
                aria-label={action.title}
                onClick={() => {}}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                  }
                }}
              >
                <span className={styles.actionText}>{action.title}</span>
                <div className={styles.iconContainer}>
                  <img
                    className={styles.actionIcon}
                    src={action.icon}
                    alt=""
                    aria-hidden="true"
                  />
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.sectionContainer}>
          <div className={styles.sectionHeader}>
            <img
              className={styles.headerIcon}
              src="https://cdn.builder.io/api/v1/image/assets/6d52bc9029684ea6804919348d39f130/741d5a9e524fc64b063bdf375b8e9db9c550a6f2f64c801d0947a929152d3f6c?apiKey=6d52bc9029684ea6804919348d39f130&"
              alt=""
              aria-hidden="true"
            />
            <h3 className={styles.sectionTitle}>More Projects</h3>
          </div>
          <div className={styles.actionsList}>
            {projectActions.map((action, index) => (
              <button
                key={index}
                className={styles.actionButton}
                tabIndex={0}
                aria-label={action.title}
                onClick={() => {}}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                  }
                }}
              >
                <span className={styles.actionText}>{action.title}</span>
                <div className={styles.iconContainer}>
                  <img
                    className={styles.actionIcon}
                    src={action.icon}
                    alt=""
                    aria-hidden="true"
                  />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
