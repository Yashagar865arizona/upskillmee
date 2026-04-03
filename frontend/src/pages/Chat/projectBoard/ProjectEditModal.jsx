import React, { useState, useEffect } from 'react';
import styles from './ProjectEditModal.module.css';

const ProjectEditModal = ({ project, isOpen, onClose, onSave, projectIndex }) => {
  const [editedProject, setEditedProject] = useState({
    title: '',
    description: '',
    tasks: [],
    resources: [],
    skills: []
  });

  // Initialize form with project data when modal opens
  useEffect(() => {
    if (project) {
      setEditedProject({
        title: project.title || '',
        description: project.description || '',
        tasks: [...(project.tasks || [])],
        resources: [...(project.resources || [])],
        skills: [...(project.skills || [])]
      });
    }
  }, [project]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditedProject(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle array input changes (tasks, resources, skills)
  const handleArrayInputChange = (e, index, arrayName) => {
    const newArray = [...editedProject[arrayName]];
    newArray[index] = e.target.value;
    setEditedProject(prev => ({
      ...prev,
      [arrayName]: newArray
    }));
  };

  // Add a new empty item to an array
  const handleAddItem = (arrayName) => {
    setEditedProject(prev => ({
      ...prev,
      [arrayName]: [...prev[arrayName], '']
    }));
  };

  // Remove an item from an array
  const handleRemoveItem = (index, arrayName) => {
    const newArray = [...editedProject[arrayName]];
    newArray.splice(index, 1);
    setEditedProject(prev => ({
      ...prev,
      [arrayName]: newArray
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Filter out empty items
    const cleanedProject = {
      ...editedProject,
      tasks: editedProject.tasks.filter(task => task.trim() !== ''),
      resources: editedProject.resources.filter(resource => resource.trim() !== ''),
      skills: editedProject.skills.filter(skill => skill.trim() !== '')
    };
    
    onSave(cleanedProject, projectIndex);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h2>Edit Learning Plan</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className={styles.editForm}>
          <div className={styles.formGroup}>
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={editedProject.title}
              onChange={handleInputChange}
              className={styles.input}
              required
            />
          </div>
          
          <div className={styles.formGroup}>
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={editedProject.description}
              onChange={handleInputChange}
              className={styles.textarea}
              rows="4"
            />
          </div>
          
          <div className={styles.formGroup}>
            <label>Tasks</label>
            {editedProject.tasks.map((task, index) => (
              <div key={`task-${index}`} className={styles.arrayItem}>
                <input
                  type="text"
                  value={task}
                  onChange={(e) => handleArrayInputChange(e, index, 'tasks')}
                  className={styles.input}
                />
                <button 
                  type="button" 
                  onClick={() => handleRemoveItem(index, 'tasks')}
                  className={styles.removeButton}
                >
                  ×
                </button>
              </div>
            ))}
            <button 
              type="button" 
              onClick={() => handleAddItem('tasks')}
              className={styles.addButton}
            >
              + Add Task
            </button>
          </div>
          
          <div className={styles.formGroup}>
            <label>Resources</label>
            {editedProject.resources.map((resource, index) => (
              <div key={`resource-${index}`} className={styles.arrayItem}>
                <input
                  type="text"
                  value={resource}
                  onChange={(e) => handleArrayInputChange(e, index, 'resources')}
                  className={styles.input}
                />
                <button 
                  type="button" 
                  onClick={() => handleRemoveItem(index, 'resources')}
                  className={styles.removeButton}
                >
                  ×
                </button>
              </div>
            ))}
            <button 
              type="button" 
              onClick={() => handleAddItem('resources')}
              className={styles.addButton}
            >
              + Add Resource
            </button>
          </div>
          
          <div className={styles.formGroup}>
            <label>Skills</label>
            {editedProject.skills.map((skill, index) => (
              <div key={`skill-${index}`} className={styles.arrayItem}>
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => handleArrayInputChange(e, index, 'skills')}
                  className={styles.input}
                />
                <button 
                  type="button" 
                  onClick={() => handleRemoveItem(index, 'skills')}
                  className={styles.removeButton}
                >
                  ×
                </button>
              </div>
            ))}
            <button 
              type="button" 
              onClick={() => handleAddItem('skills')}
              className={styles.addButton}
            >
              + Add Skill
            </button>
          </div>
          
          <div className={styles.formActions}>
            <button type="button" onClick={onClose} className={styles.cancelButton}>
              Cancel
            </button>
            <button type="submit" className={styles.saveButton}>
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProjectEditModal; 