import React, { useState, useRef, useEffect } from 'react';
import styles from './AgentModeSelector.module.css';

const AgentModeSelector = ({ currentMode, onModeChange, availableModes }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  const modeNames = {
    chat: 'Mentor',
    work: 'Project Partner', 
    plan: 'Learning Path'
  };

  const modeDescriptions = {
    chat: 'General guidance & mentoring',
    work: 'Execute projects & learning',
    plan: 'Create learning roadmaps'
  };

  const defaultModes = {
    chat: 'General conversation and mentoring',
    work: 'Get technical help with projects', 
    plan: 'Create and edit learning plans'
  };

  const modes = availableModes || defaultModes;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleModeSelect = (mode) => {
    onModeChange(mode);
    setIsOpen(false);
  };

  return (
    <div className={styles.agentModeSelector} ref={dropdownRef}>
      <button 
        className={styles.modeIndicator}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="AI mode selector"
      >
        <span className={styles.name}>{modeNames[currentMode]}</span>
        <span className={`${styles.arrow} ${isOpen ? styles.arrowOpen : ''}`}>▼</span>
      </button>

      {isOpen && (
        <div className={styles.modeDropdown}>
          {Object.entries(modes).map(([mode, description]) => (
            <button
              key={mode}
              className={`${styles.modeOption} ${currentMode === mode ? styles.active : ''}`}
              onClick={() => handleModeSelect(mode)}
            >
              <div className={styles.optionText}>
                <div className={styles.optionName}>{modeNames[mode]}</div>
                <div className={styles.optionDesc}>{modeDescriptions[mode]}</div>
              </div>
              {currentMode === mode && <span className={styles.check}>✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentModeSelector; 