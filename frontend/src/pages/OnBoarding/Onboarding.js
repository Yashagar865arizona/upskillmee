import React, { useState } from "react";
import styles from "./Onboarding.module.css";
import { useNavigate } from "react-router-dom";
import { useUser } from "../../context/UserContext";
import { useAuth } from "../../context/AuthContext";
import CompletionPopup from "../../pages/OnBoarding/CompletionPopup";

const steps = [
  "Welcome",
  "Educational Background",
  "Strength Discovery",
  "Real-World Project Scenarios",
  "Learning Style Discovery",
  "Goals",
  "Preferences",
  "Complete",
];

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const { submitOnboarding } = useUser();
  const [showPopup, setShowPopup] = useState(false);
  const { token } = useAuth();
const navigate = useNavigate();

  const [formData, setFormData] = useState({
    current_status: "",
    other_status: "",
    subjects: [],
    other_subject: "",
    engaging_subjects: "",
    struggle_subjects: "",
    strength_help: "",
    activities: [],
    groupRole: "",
    projects: [],
    learning_styles: [],
    stuck_strategies: [],
    learning_structure: "",
    certifications: false,
    time_commitment: "",
    goals: "",
  });

  const progress = ((step - 1) / (steps.length - 1)) * 100;

  const handleBack = () => {
    if (step > 1) setStep((prev) => prev - 1);
  };



const handleFinish = async () => {
   const authToken = token || localStorage.getItem("token");
   console.log("@@@@@@",authToken)

const payload = {
  age: formData.age || null,
  location: formData.location || null,
  education_level: formData.current_status === "Other" ? formData.other_status : formData.current_status,
  languages: formData.languages || [],
  learning_style: formData.learning_style || null,
  hobbies: formData.hobbies || [],
  preferred_subjects: formData.subjects || [],
  work_style: null,
  work_preferences: [],
  career_interests: formData.career_interests || [],
  long_term_goals: formData.goals ? [formData.goals] : [],
  technical_skills: [],
  soft_skills: [],
  certifications: Array.isArray(formData.certifications) ? formData.certifications : formData.certifications ? ['Yes'] : [],
  achievements: [],
  personality_traits: {},
  cognitive_strengths: [],
  learning_preferences: {
    learning_styles: formData.learning_styles || [],
    stuck_strategies: formData.stuck_strategies || []
  },
  preferences: {
    time_commitment: formData.time_commitment || null,
    group_role: formData.groupRole || null,
    activities: formData.activities || [],
    engaging_subjects: formData.engaging_subjects || null,
    struggle_subjects: formData.struggle_subjects || null,
    strength_help: formData.strength_help || null
  }
};


  try {
    await submitOnboarding(payload);
    // navigate("/dashboard");
    setShowPopup(true);
  } catch (err) {
    console.error("Onboarding error:", err);
    alert(err.message || "Failed to submit onboarding");
  }
};

 const handleContinue = () => {
  console.log("$$$$$$$$$$$$$$$$$$$$$44")
    setShowPopup(false);
    navigate("/dashboard"); 
  };
  const handleSubmit = (e) => {
    e.preventDefault();
    if (step === steps.length - 1) {
      handleFinish();
    } else {
      setStep((prev) => prev + 1);
    }
  };

  return (
    <div className={styles.onboardingContainer}>
      {step === 1 ? (
        <div className={styles.welcomeContainer}>
          <div className={styles.overlay}></div>
          <div className={styles.welcomeContent}>
            <h1 className={styles.welcomeTitle}>
              Welcome to <span className={styles.brandName}>upSkillMee</span>
            </h1>
            <p className={styles.welcomeSubtitle}>
              🚀 Discover your strengths, explore your interests, and create a
              personalized learning journey tailored just for you.
            </p>
            <button className={styles.startButton} onClick={() => setStep(2)}>
              Start Your Journey →
            </button>
          </div>
          <div className={styles.welcomeImageWrapper}>
            <img
              src="https://cdn-icons-png.flaticon.com/512/888/888879.png"
              alt="upSkillMee Logo"
              className={styles.welcomeImage}
            />
          </div>
        </div>
      ) : (
        <div className={styles.onboardingCard}>
          <h2 className={styles.stepTitle}>{steps[step - 1]}</h2>
          <div className={styles.progressBarBackground}>
            <div
              className={styles.progressBarFill}
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          <form className={styles.onboardingForm} onSubmit={handleSubmit}>
            {/* Step 2: Educational Background */}
            {step === 2 && (
              <>
                <p className={styles.question}>
                  Help us understand your educational journey:
                </p>
                <div className={styles.prefGrid}>
                  {[
                    "High School (Grade 9-12)",
                    "College/University (Year 1-4+)",
                    "Graduate School",
                    "Working Professional",
                    "Career Break / Gap Year",
                    "Other",
                  ].map((status) => (
                    <label
                      key={status}
                      className={`${styles.prefCard} ${
                        formData.current_status === status
                          ? styles.selectedCard
                          : ""
                      }`}
                    >
                      <input
                        type="radio"
                        name="current_status"
                        value={status}
                        checked={formData.current_status === status}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            current_status: e.target.value,
                            subjects: [],
                          })
                        }
                      />
                      {status}
                    </label>
                  ))}
                </div>

                {formData.current_status === "Other" && (
                  <input
                    type="text"
                    placeholder="Please specify"
                    className={styles.inputField}
                    value={formData.other_status || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, other_status: e.target.value })
                    }
                  />
                )}

                {[
                  "High School (Grade 9-12)",
                  "College/University (Year 1-4+)",
                ].includes(formData.current_status) && (
                  <>
                    <p className={styles.question}>
                      Which subjects are you currently taking?
                    </p>
                    <div className={styles.prefGrid}>
                      {[
                        "Mathematics",
                        "Sciences (Biology, Chemistry, Physics)",
                        "English/Literature",
                        "History/Social Studies",
                        "Foreign Languages",
                        "Art/Creative Arts",
                        "Computer Science/Technology",
                        "Business/Economics",
                        "Psychology",
                        "Engineering",
                        "Other",
                      ].map((subject) => (
                        <label
                          key={subject}
                          className={`${styles.prefCard} ${
                            formData.subjects.includes(subject)
                              ? styles.selectedCard
                              : ""
                          }`}
                        >
                          <input
                            type="checkbox"
                            value={subject}
                            checked={formData.subjects.includes(subject)}
                            onChange={(e) => {
                              const currentSubjects = formData.subjects;
                              if (e.target.checked) {
                                setFormData({
                                  ...formData,
                                  subjects: [...currentSubjects, subject],
                                });
                              } else {
                                setFormData({
                                  ...formData,
                                  subjects: currentSubjects.filter(
                                    (s) => s !== subject
                                  ),
                                });
                              }
                            }}
                          />
                          {subject}
                        </label>
                      ))}
                    </div>

                    {formData.subjects.includes("Other") && (
                      <input
                        type="text"
                        placeholder="Please specify other subjects"
                        className={styles.inputField}
                        value={formData.other_subject || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            other_subject: e.target.value,
                          })
                        }
                      />
                    )}

                    <input
                      type="text"
                      placeholder="Which subjects are most engaging? (Top 3)"
                      className={styles.inputField}
                      value={formData.engaging_subjects || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          engaging_subjects: e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      placeholder="Which subjects feel like a struggle? (Optional)"
                      className={styles.inputField}
                      value={formData.struggle_subjects || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          struggle_subjects: e.target.value,
                        })
                      }
                    />
                  </>
                )}
              </>
            )}

            {/* Step 3: Strength Discovery */}
            {step === 3 && (
              <>
                <p className={styles.question}>
                  What are your natural strengths?
                </p>
                <input
                  type="text"
                  placeholder="People often ask me for help with..."
                  value={formData.strength_help || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, strength_help: e.target.value })
                  }
                  className={styles.inputField}
                />

                <p className={styles.question}>
                  Activities you lose track of time doing:
                </p>
                <div className={styles.prefGrid}>
                  {[
                    "Building/making things",
                    "Solving puzzles",
                    "Creative writing",
                    "Drawing/designing",
                    "Helping others",
                    "Organizing events",
                    "Analyzing data",
                    "Performing/presenting",
                    "Learning about how things work",
                    "Debating ideas",
                  ].map((activity) => (
                    <label
                      key={activity}
                      className={`${styles.prefCard} ${
                        formData.activities.includes(activity)
                          ? styles.selectedCard
                          : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        value={activity}
                        checked={formData.activities.includes(activity)}
                        onChange={(e) => {
                          const current = formData.activities;
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              activities: [...current, activity],
                            });
                          } else {
                            setFormData({
                              ...formData,
                              activities: current.filter((a) => a !== activity),
                            });
                          }
                        }}
                      />
                      {activity}
                    </label>
                  ))}
                </div>

                <p className={styles.question}>
                  When working on group projects, you usually:
                </p>
                <div className={styles.prefGrid}>
                  {[
                    "Take charge and organize",
                    "Come up with creative ideas",
                    "Handle research and details",
                    "Keep everyone motivated",
                    "Focus on design/appearance",
                    "Ensure accuracy",
                    "Present to the class",
                  ].map((role) => (
                    <label
                      key={role}
                      className={`${styles.prefCard} ${
                        formData.groupRole === role ? styles.selectedCard : ""
                      }`}
                    >
                      <input
                        type="radio"
                        name="groupRole"
                        value={role}
                        checked={formData.groupRole === role}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            groupRole: e.target.value,
                          })
                        }
                      />
                      {role}
                    </label>
                  ))}
                </div>
              </>
            )}

            {step === 4 && (
              <>
                <p className={styles.question}>
                  Which mini-projects interest you most? (Select multiple)
                </p>

                <div className={styles.projectGrid}>
                  <h4 className={styles.categoryTitle}>Creative & Design</h4>
                  <div className={styles.projectCards}>
                    {[
                      { label: "Design a poster", value: "poster" },
                      { label: "Create a short podcast", value: "podcast" },
                      {
                        label: "Write and illustrate a children's story",
                        value: "story",
                      },
                      { label: "Design a board game", value: "boardgame" },
                    ].map((project) => (
                      <label
                        key={project.value}
                        className={`${styles.projectCard} ${
                          formData.projects?.includes(project.value)
                            ? styles.selectedCard
                            : ""
                        }`}
                      >
                        <input
                          type="checkbox"
                          value={project.value}
                          checked={
                            formData.projects?.includes(project.value) || false
                          }
                          onChange={(e) => {
                            const value = e.target.value;
                            const selected = formData.projects || [];
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                projects: [...selected, value],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                projects: selected.filter((v) => v !== value),
                              });
                            }
                          }}
                        />
                        {project.label}
                      </label>
                    ))}
                  </div>

                  <h4 className={styles.categoryTitle}>
                    Problem-Solving & Analysis
                  </h4>
                  <div className={styles.projectCards}>
                    {[
                      {
                        label: "Analyze recycling program",
                        value: "recycling",
                      },
                      {
                        label: "Research study techniques",
                        value: "studytech",
                      },
                      {
                        label: "Solve local traffic problems",
                        value: "traffic",
                      },
                      { label: "Investigate viral songs", value: "viral" },
                    ].map((project) => (
                      <label
                        key={project.value}
                        className={`${styles.projectCard} ${
                          formData.projects?.includes(project.value)
                            ? styles.selectedCard
                            : ""
                        }`}
                      >
                        <input
                          type="checkbox"
                          value={project.value}
                          checked={
                            formData.projects?.includes(project.value) || false
                          }
                          onChange={(e) => {
                            const value = e.target.value;
                            const selected = formData.projects || [];
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                projects: [...selected, value],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                projects: selected.filter((v) => v !== value),
                              });
                            }
                          }}
                        />
                        {project.label}
                      </label>
                    ))}
                  </div>
                </div>
              </>
            )}

            {step === 5 && (
              <>
                <p className={styles.question}>
                  How do you learn best? (Select all that apply)
                </p>
                <div className={styles.learningGrid}>
                  {[
                    {
                      label: "Jump in and start experimenting",
                      value: "experiment",
                    },
                    { label: "Watch others do it first", value: "observe" },
                    { label: "Read about it thoroughly", value: "read" },
                    {
                      label: "Discuss it with friends or mentors",
                      value: "discuss",
                    },
                    { label: "Find real-world examples", value: "examples" },
                    { label: "Break it down into small steps", value: "steps" },
                  ].map((style) => (
                    <label
                      key={style.value}
                      className={`${styles.learningCard} ${
                        formData.learning_styles?.includes(style.value)
                          ? styles.selectedCard
                          : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        value={style.value}
                        checked={
                          formData.learning_styles?.includes(style.value) ||
                          false
                        }
                        onChange={(e) => {
                          const value = e.target.value;
                          const selected = formData.learning_styles || [];
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              learning_styles: [...selected, value],
                            });
                          } else {
                            setFormData({
                              ...formData,
                              learning_styles: selected.filter(
                                (v) => v !== value
                              ),
                            });
                          }
                        }}
                      />
                      {style.label}
                    </label>
                  ))}
                </div>

                <p className={styles.question}>
                  When you get stuck, what do you usually do? (Select all that
                  apply)
                </p>
                <div className={styles.learningGrid}>
                  {[
                    {
                      label: "Take a break and come back fresh",
                      value: "break",
                    },
                    { label: "Ask someone for help", value: "ask" },
                    {
                      label: "Research different approaches online",
                      value: "research",
                    },
                    {
                      label: "Try to figure it out through trial and error",
                      value: "trial",
                    },
                    {
                      label: "Look for simpler explanations or examples",
                      value: "simplify",
                    },
                  ].map((style) => (
                    <label
                      key={style.value}
                      className={`${styles.learningCard} ${
                        formData.stuck_strategies?.includes(style.value)
                          ? styles.selectedCard
                          : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        value={style.value}
                        checked={
                          formData.stuck_strategies?.includes(style.value) ||
                          false
                        }
                        onChange={(e) => {
                          const value = e.target.value;
                          const selected = formData.stuck_strategies || [];
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              stuck_strategies: [...selected, value],
                            });
                          } else {
                            setFormData({
                              ...formData,
                              stuck_strategies: selected.filter(
                                (v) => v !== value
                              ),
                            });
                          }
                        }}
                      />
                      {style.label}
                    </label>
                  ))}
                </div>
              </>
            )}

            {step === 6 && (
              <input
                type="text"
                placeholder="Your goals"
                className={styles.inputField}
                value={formData.goals || ""}
                onChange={(e) =>
                  setFormData({ ...formData, goals: e.target.value })
                }
              />
            )}

            {step === 7 && (
              <>
                <p className={styles.question}>
                  How would you like to structure your learning?
                </p>
                <div className={styles.prefGrid}>
                  {[
                    { label: "Structured", value: "structured" },
                    { label: "Flexible", value: "flexible" },
                  ].map((option) => (
                    <label
                      key={option.value}
                      className={`${styles.prefCard} ${
                        formData.learning_structure === option.value
                          ? styles.selectedCard
                          : ""
                      }`}
                    >
                      <input
                        type="radio"
                        name="learning_structure"
                        value={option.value}
                        checked={formData.learning_structure === option.value}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            learning_structure: e.target.value,
                          })
                        }
                      />
                      {option.label}
                    </label>
                  ))}
                </div>

                <p className={styles.question}>Interested in certifications?</p>
                <label
                  className={`${styles.prefCard} ${
                    formData.certifications ? styles.selectedCard : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={formData.certifications || false}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        certifications: e.target.checked,
                      })
                    }
                  />
                  Yes, I am interested
                </label>

                <p className={styles.question}>
                  Time commitment (hours per week)
                </p>
                <input
                  type="number"
                  placeholder="e.g., 5"
                  min="0"
                  max="168"
                  className={styles.inputField}
                  value={formData.time_commitment || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      time_commitment: e.target.value,
                    })
                  }
                />
              </>
            )}

            {/* Step 8 Complete */}
            {step === 8 && (
              <div className={styles.completeContainer}>
                <div className={styles.confetti}></div>
                <div className={styles.completeCard}>
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/190/190411.png"
                    alt="Complete"
                    className={styles.completeImage}
                  />
                  <h1 className={styles.completeTitle}>Congratulations!</h1>
                  <p className={styles.completeSubtitle}>
                    You’ve completed your onboarding journey. Get ready to
                    explore your personalized learning experience 🚀
                  </p>
                  <button
                    className={styles.completeButton}
                    onClick={handleFinish}
                  >
                    Go to Dashboard →
                  </button>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            {step !== 1 && step !== 8 && (
              <div className={styles.buttonGroup}>
                <button
                  type="button"
                  className={styles.backButton}
                  onClick={handleBack}
                >
                  Back
                </button>
                <button type="submit" className={styles.nextButton}>
                  {step === steps.length - 1 ? "Finish" : "Next"}
                </button>
              </div>
            )}
          </form>
        </div>
      )}
   
{showPopup && <CompletionPopup onContinue={handleContinue} />}

    </div>
  );
}
