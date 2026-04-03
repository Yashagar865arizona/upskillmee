import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './SignUp.module.css';

const questions = [
  {
    id: 'basic',
    title: 'Basic Information',
    description: 'Let\'s start with the essentials',
    fields: [
      { name: 'name', label: 'What should I call you?', type: 'text', placeholder: 'Your name' },
      { name: 'email', label: 'What\'s your email?', type: 'email', placeholder: 'email@example.com' },
      { name: 'password', label: 'Choose a password', type: 'password', placeholder: 'Minimum 8 characters' }
    ]
  },
  {
    id: 'cognitive_style',
    title: 'Understanding Your Thought Process',
    description: 'These questions help me understand how you approach problems and learn best',
    fields: [
      {
        name: 'problem_solving',
        label: 'When faced with a complex problem, how do you typically approach it?',
        type: 'multiselect',
        options: [
          'Break it down into smaller parts',
          'Research similar problems first',
          'Try different solutions through trial and error',
          'Draw diagrams or visualize the problem',
          'Discuss with others to get different perspectives',
          'Start with what I know and build up gradually'
        ]
      },
      {
        name: 'learning_triggers',
        label: 'What makes a topic or concept "click" for you?',
        type: 'multiselect',
        options: [
          'Real-world examples and applications',
          'Visual explanations and diagrams',
          'Step-by-step breakdowns',
          'Hands-on practice',
          'Analogies to familiar concepts',
          'Understanding the underlying principles'
        ]
      }
    ]
  },
  {
    id: 'motivation_goals',
    title: 'Your Motivation and Goals',
    description: 'Help me understand what drives you and what you want to achieve',
    fields: [
      {
        name: 'learning_motivation',
        label: 'What\'s your primary motivation for learning programming?',
        type: 'multiselect',
        options: [
          'Career advancement or change',
          'Building specific projects or products',
          'Personal interest and curiosity',
          'Problem-solving and automation',
          'Starting a business or startup',
          'Academic or research purposes'
        ]
      },
      {
        name: 'success_metrics',
        label: 'How would you define success in your learning journey?',
        type: 'text',
        placeholder: 'Describe what success means to you'
      }
    ]
  },
  {
    id: 'learning_preferences',
    title: 'Your Learning Style',
    description: 'Let me understand how you learn best',
    fields: [
      {
        name: 'preferred_resources',
        label: 'What types of learning resources do you find most effective?',
        type: 'multiselect',
        options: [
          'Interactive tutorials',
          'Video courses',
          'Technical documentation',
          'Books and written guides',
          'Project-based learning',
          'Pair programming',
          'Community forums and discussions'
        ]
      },
      {
        name: 'learning_pace',
        label: 'How do you prefer to pace your learning?',
        type: 'select',
        options: [
          'Quick sprints with breaks',
          'Steady and consistent pace',
          'Deep dives into specific topics',
          'Flexible depending on the topic'
        ]
      }
    ]
  },
  {
    id: 'background_experience',
    title: 'Your Background and Experience',
    description: 'Help me understand where you\'re starting from',
    fields: [
      {
        name: 'coding_experience',
        label: 'What\'s your experience with coding so far?',
        type: 'text',
        placeholder: 'Tell me about your coding journey'
      },
      {
        name: 'learning_challenges',
        label: 'What aspects of programming have you found challenging in the past?',
        type: 'text',
        placeholder: 'This helps me address potential roadblocks proactively'
      }
    ]
  },
  {
    id: 'interests_context',
    title: 'Your Interests and Context',
    description: 'Help me understand what excites you',
    fields: [
      {
        name: 'interest_areas',
        label: 'What topics or areas of technology interest you the most?',
        type: 'multiselect',
        options: [
          'Web Development',
          'Mobile Apps',
          'Data Science',
          'Machine Learning',
          'Game Development',
          'Cybersecurity',
          'DevOps',
          'Blockchain',
          'IoT',
          'UI/UX Design'
        ]
      },
      {
        name: 'industry_context',
        label: 'What industry or domain do you work in or are interested in?',
        type: 'text',
        placeholder: 'This helps me provide relevant examples'
      }
    ]
  },
  {
    id: 'working_style',
    title: 'Your Working Style',
    description: 'Help me understand how you prefer to work and learn',
    fields: [
      {
        name: 'project_preferences',
        label: 'What kind of projects do you enjoy working on?',
        type: 'multiselect',
        options: [
          'Small, focused projects',
          'Large, complex systems',
          'Creative and visual projects',
          'Data-driven projects',
          'Tools and automation',
          'User-facing applications'
        ]
      },
      {
        name: 'collaboration_style',
        label: 'How do you prefer to collaborate and get help?',
        type: 'multiselect',
        options: [
          'Independent problem-solving first',
          'Regular check-ins and guidance',
          'Detailed explanations and examples',
          'Quick hints and pointers',
          'Code reviews and feedback',
          'Pair programming sessions'
        ]
      }
    ]
  }
];

const SignUp = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const validateStep = () => {
    const currentFields = questions[currentStep].fields;
    const newErrors = {};
    
    currentFields.forEach(field => {
      if (!formData[field.name] || 
          (Array.isArray(formData[field.name]) && formData[field.name].length === 0)) {
        newErrors[field.name] = 'This field is required';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep()) {
      if (currentStep < questions.length - 1) {
        setCurrentStep(prev => prev + 1);
      } else {
        handleSubmit();
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Signup failed');
      }

      // Redirect to onboarding or dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Signup error:', error);
      setErrors({ submit: 'Failed to create account. Please try again.' });
    }
  };

  const renderField = (field) => {
    switch (field.type) {
      case 'multiselect':
        return (
          <div className={styles.field} key={field.name}>
            <label>{field.label}</label>
            <div className={styles.optionsGrid}>
              {field.options.map(option => (
                <label key={option} className={styles.checkbox}>
                  <input
                    type="checkbox"
                    checked={formData[field.name]?.includes(option)}
                    onChange={(e) => {
                      const current = formData[field.name] || [];
                      if (e.target.checked) {
                        handleInputChange(field.name, [...current, option]);
                      } else {
                        handleInputChange(field.name, current.filter(item => item !== option));
                      }
                    }}
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
            {errors[field.name] && <span className={styles.error}>{errors[field.name]}</span>}
          </div>
        );

      case 'select':
        return (
          <div className={styles.field} key={field.name}>
            <label>{field.label}</label>
            <select
              value={formData[field.name] || ''}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
              className={styles.select}
            >
              <option value="">Select an option</option>
              {field.options.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            {errors[field.name] && <span className={styles.error}>{errors[field.name]}</span>}
          </div>
        );

      default:
        return (
          <div className={styles.field} key={field.name}>
            <label>{field.label}</label>
            <input
              type={field.type}
              placeholder={field.placeholder}
              value={formData[field.name] || ''}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
              className={styles.input}
            />
            {errors[field.name] && <span className={styles.error}>{errors[field.name]}</span>}
          </div>
        );
    }
  };

  const currentQuestion = questions[currentStep];

  return (
    <div className={styles.container}>
      <div className={styles.signupCard}>
        <div className={styles.progress}>
          <div 
            className={styles.progressBar} 
            style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
          />
        </div>

        <div className={styles.stepHeader}>
          <h2>{currentQuestion.title}</h2>
          <p>{currentQuestion.description}</p>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -100, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className={styles.step}
          >
            {currentQuestion.fields.map(field => renderField(field))}
          </motion.div>
        </AnimatePresence>

        <div className={styles.buttons}>
          {currentStep > 0 && (
            <button onClick={handleBack} className={styles.backButton}>
              Back
            </button>
          )}
          <button onClick={handleNext} className={styles.nextButton}>
            {currentStep === questions.length - 1 ? 'Create Account' : 'Next'}
          </button>
        </div>

        {errors.submit && <div className={styles.submitError}>{errors.submit}</div>}

        <div className={styles.stepCount}>
          Step {currentStep + 1} of {questions.length}
        </div>
      </div>
    </div>
  );
};

export default SignUp;
