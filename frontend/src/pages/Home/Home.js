import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { useTheme } from "../../context/ThemeContext";
import { useNavigate } from "react-router-dom";
import styles from "./Home.module.css";
import vdo from "../../assets/video.mp4";
import {
  FaFacebookF,
  FaTwitter,
  FaLinkedinIn,
  FaInstagram,
} from "react-icons/fa";
import {
  MdOutlinePsychology,
  MdWorkspacePremium,
  MdVerifiedUser,
} from "react-icons/md";
import {
  GiArtificialIntelligence,
  GiAchievement,
  GiBrain,
  GiMagicGate,
  GiRocketFlight,
  GiSkills,
} from "react-icons/gi";
import { useAuth } from "../../context/AuthContext";
import { User, Phone, Mail, MessageCircle, Send } from "lucide-react";

const features = [
  {
    icon: <MdOutlinePsychology size={48} />,
    title: "AI-Powered Insights",
    desc: "Our AI mentor understands your learning style, adapts to your pace, and offers tailored recommendations to help you achieve your goals faster.",
  },
  {
    icon: <MdWorkspacePremium size={48} />,
    title: "Premium Project Workflows",
    desc: "Engage with practical, real-world projects that build your portfolio and prepare you for technical interviews and job readiness.",
  },
  {
    icon: <GiArtificialIntelligence size={48} />,
    title: "Interactive AI Chat",
    desc: "Get instant answers, explanations, and learning prompts via a conversational interface — learn on the go without distractions.",
  },
  {
    icon: <MdVerifiedUser size={48} />,
    title: "Verified Progress Tracking",
    desc: "Monitor your achievements with detailed analytics, receive certificates, and validate your skills for employers and recruiters.",
  },
];

const journeySteps = [
  {
    icon: <GiBrain size={40} />,
    title: "Curiosity",
    desc: "Spark your imagination and explore new topics with ease.",
  },
  {
    icon: <GiMagicGate size={40} />,
    title: "Learn",
    desc: "Get structured learning paths tailored to your pace and style.",
  },
  {
    icon: <GiSkills size={40} />,
    title: "Practice",
    desc: "Hands-on challenges and projects to reinforce learning.",
  },
  {
    icon: <GiAchievement size={40} />,
    title: "Showcase",
    desc: "Build a portfolio that stands out to employers and peers.",
  },
  {
    icon: <GiRocketFlight size={40} />,
    title: "Grow",
    desc: "Achieve career-ready skills and join a global network of learners.",
  },
];

const Home = () => {
  const { darkMode } = useTheme();
  const { submitEmail } = useAuth();
  const [user, setUser]=useState({name:"",email:"",phone_number:"",message:""})
  // const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
const contactRef = useRef(null);

const scrollToContact = () => {
  contactRef.current?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
};

  const navigate = useNavigate();
  const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0 },
  };

  const handleChange = (e) => {
  const { name, value } = e.target;
  setUser((prev) => ({ ...prev, [name]: value }));
};

// Handle form submit
const handleEmailSubmit = async (e) => {
  e.preventDefault();

  const { name, email, phone_number, message } = user;
  if (!name || !email || !phone_number || !message) {
    setMessage("Please fill in all fields.");
    return;
  }

  if (loading) return;
  setLoading(true);

  try {
    const res = await submitEmail({
      name,
      email,
      phone_number,
      message,
    });
    setMessage(res.message || "Message sent successfully!");
    setUser({ name: "", email: "", phone_number: "", message: "" });
    setSuccess(true);
  } catch (err) {
    setMessage(err.response?.data?.detail || "Failed to submit message.");
  } finally {
    setLoading(false);
  }
};

  return (
    <section className={`${styles.home} ${darkMode ? styles.dark : ""}`}>
      {/* Hero */}
      <motion.div
        className={styles.hero}
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        <video autoPlay loop muted className={styles.heroVideo}>
          <source src={vdo} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        <div className={styles.heroOverlay}></div>
        <div className={styles.heroContent}>
          <h1>
            Learn. Build. <span className={styles.highlight}>Grow.</span>
          </h1>
          <p className={styles.heroDescription}>
            Turn curiosity into real skills with AI-powered guidance, hands-on
            projects, and a global community of learners.
          </p>

          
          {!success ? (
            <div className={styles.heroEmailForm}>
           
              <button
                className={styles.btnPrimary}
                
                onClick={scrollToContact}
              >
               
                Book Demo
              </button>
            </div>
          ) : null}
           {message && (
            <motion.p
              className={styles.heroMsg}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.5 }}
            >
              {message}
            </motion.p>
          )}
        </div>
      </motion.div>

      {/* Features Section */}
      <div className={styles.featuresSection}>
        <h2 className={styles.header}>Why Choose Upskillmee?</h2>
        <p className={styles.featuresIntro}>
          Empower your learning journey with personalized guidance, interactive
          tools, and a supportive community designed to help you succeed.
        </p>
        <div className={styles.featuresGrid}>
          {features.map((f, idx) => (
            <motion.div
              key={idx}
              className={styles.featureItem}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.2 }}
            >
              <div className={styles.iconWrapper}>{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Learning Journey */}
      <div className={styles.timelineSection}>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className={styles.header}
        >
          Your Learning Journey
        </motion.h2>
        <motion.div
          className={styles.timelineGrid}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {journeySteps.map((step, index) => (
            <motion.div
              key={index}
              className={styles.timelineItem}
              variants={fadeUp}
              transition={{ delay: index * 0.2, duration: 0.6 }}
            >
              <div className={styles.iconWrapper}>{step.icon}</div>
              <h3>{step.title}</h3>
              <p>{step.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Chat */}
      <div className={styles.demoSectionFull}>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className={styles.header}
        >
          Try It Out
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className={styles.demoDescription}
        >
          Experience how Upskillmee’s AI can assist you. Just pick a prompt and see
          personalized learning suggestions instantly.
        </motion.p>

        <motion.div
          className={styles.chatboxDemoFull}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 1 }}
        >
          {[
            { type: "user", msg: "“Teach me Python in 30 days”" },
            {
              type: "ai",
              msg: "Here’s a 30-day roadmap with mini-projects, from basics to web apps.",
            },
            {
              type: "user",
              msg: "“Help me prepare for a data science interview”",
            },
            {
              type: "ai",
              msg: "Let’s create a study plan covering algorithms, statistics, and mock interviews.",
            },
            {
              type: "user",
              msg: "“Suggest beginner-friendly coding projects”",
            },
            {
              type: "ai",
              msg: "Try building a calculator, a personal diary app, or a weather dashboard to enhance your skills.",
            },
          ].map((chat, idx) => (
            <motion.div
              key={idx}
              className={
                chat.type === "user" ? styles.userMsgFull : styles.aiMsgFull
              }
              initial={{ x: chat.type === "user" ? -200 : 200, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.3, type: "spring", stiffness: 120 }}
            >
              {chat.msg}
            </motion.div>
          ))}
        </motion.div>
      </div>
{/* Futuristic Animated Contact Section */}
<section ref={contactRef} className={styles.contactSection}>
  
  <motion.div
    className={styles.floatingIcon + " " + styles.icon1}
    animate={{ y: [0, -15, 0] }}
    transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
  >
    💡
  </motion.div>
  <motion.div
    className={styles.floatingIcon + " " + styles.icon2}
    animate={{ y: [0, -20, 0] }}
    transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
  >
    🚀
  </motion.div>
  <motion.div
    className={styles.floatingIcon + " " + styles.icon3}
    animate={{ y: [0, -10, 0] }}
    transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
  >
    💬
  </motion.div>

  <motion.div
    className={styles.contactContainer}
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 1 }}
  >
    {/* Left side - Info */}
    <motion.div
      className={styles.contactInfo}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={{
        hidden: { opacity: 0, x: -40 },
        visible: {
          opacity: 1,
          x: 0,
          transition: { staggerChildren: 0.25, duration: 0.8 },
        },
      }}
    >
      <motion.h2 variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }} className={styles.contactHeading}>
        Get in Touch ✨
      </motion.h2>

      <motion.p variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }} className={styles.contactText}>
        Let’s collaborate, innovate, and grow together!  
        Whether you’ve got feedback, partnership ideas, or just want to say hi — we’re here for you.
      </motion.p>

      <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }} className={styles.contactDetails}>
        <p><i className="fas fa-envelope"></i> support@upSkillmee.com</p>
        <p><i className="fas fa-phone-alt"></i> +91 9876567865</p>
        <p><i className="fas fa-map-marker-alt"></i> Santiniketan Building, Camac Street, Kolkata</p>
      </motion.div>

      <motion.div
        variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
        className={styles.socialIcons}
      >
        <a href="#" aria-label="LinkedIn"><i className="fab fa-linkedin"></i></a>
        <a href="#" aria-label="Facebook"><i className="fab fa-facebook"></i></a>
        <a href="#" aria-label="WhatsApp"><i className="fab fa-whatsapp"></i></a>
      </motion.div>
    </motion.div>

    {/* Right side - Form */}
     <motion.form
      className={styles.contactForm}
      initial={{ x: 50, opacity: 0 }}
      whileInView={{ x: 0, opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 1 }}
      onSubmit={(e) => {
        e.preventDefault();
        alert("Message sent successfully! 🚀");
      }}
    >
       <motion.div className={styles.inputGroup}>
    <User className={styles.inputIcon} />
    <motion.input
      type="text"
      placeholder="Your Name"
      name="name"
      value={user.name}
      onChange={handleChange}
      required
    />
  </motion.div>

  
  <motion.div className={styles.inputGroup}>
    <Phone className={styles.inputIcon} />
    <motion.input
      type="tel"
      placeholder="Phone Number"
      name="phone_number"
      value={user.phone_number}
      onChange={handleChange}
      required
    />
  </motion.div>

  
  <motion.div className={styles.inputGroup}>
    <Mail className={styles.inputIcon} />
    <motion.input
      type="email"
      placeholder="Your Email"
      name="email"
      value={user.email}
      onChange={handleChange}
      required
    />
  </motion.div>

  
  <motion.div className={`${styles.inputGroup} ${styles.textarea}`}>
    <MessageCircle className={styles.inputIcon} />
    <motion.textarea
      placeholder="Your Message"
      rows="5"
      name="message"
      value={user.message}
      onChange={handleChange}
      required
      whileFocus={{ scale: 1.02 }}
    />
  </motion.div>

      {/* Submit Button */}
      <motion.button
        type="submit"
        className={styles.submitBtn}
        onClick={handleEmailSubmit}
        disabled={loading}
        whileHover={{
          scale: 1.05,
          boxShadow: "0 0 25px rgba(6,182,212,0.7)",
        }}
        whileTap={{ scale: 0.97 }}
      >
        <Send size={18} /> {loading ? "Submitting..." : "Get Early Access"}
      </motion.button>
      {message && (
      <motion.p
        className={styles.heroMessage}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.5 }}
      >
        {message}
      </motion.p>
    )}
    </motion.form>
  </motion.div>
</section>

      {/* Footer */}
      <footer className={styles.footerSection}>
        <div className={styles.footerTop}>
          <div className={styles.footerColumn}>
            <h4 className={styles.header}>Upskillmee</h4>
            <p>Learn. Build. Grow. Your AI-powered learning companion.</p>
            <div className={styles.footerSocial}>
              <a href="#">
                <FaFacebookF />
              </a>
              <a href="#">
                <FaTwitter />
              </a>
              <a href="#">
                <FaLinkedinIn />
              </a>
              <a href="#">
                <FaInstagram />
              </a>
            </div>
          </div>
          <div className={styles.footerColumn}>
            <h4 className={styles.header}>Quick Links</h4>
            <ul>
              <li>
                <a href="#">Home</a> 
              </li>
              <li>
                <a href="#">Features</a>
              </li>
              <li>
                <a href="#">Pricing</a>
              </li>
              <li>
                <a href="#">Blog</a>
              </li>
            </ul>
          </div>
          <div className={styles.footerColumn}>
            <h4 className={styles.header}>Resources</h4>
            <ul>
              <li>
                <a href="#">Docs</a>
              </li>
              <li>
                <a href="#">Tutorials</a>
              </li>
              <li>
                <a href="#">Community</a>
              </li>
              <li>
                <a href="#">Support</a>
              </li>
            </ul>
          </div>
          <div className={styles.footerColumn}>
            <h4 className={styles.header}>Contact Us</h4>
            <p>Email: support@upSkillmee.com</p>
            <p>Phone: +91 9876567865</p>
            <p>Address: Santiniketan Building, Camac Street, Kolkata</p>
          </div>
        </div>
        <div className={styles.footerBottom}>
          &copy; 2025 upSkillmee. All rights reserved.
        </div>
      </footer>
    </section>
  );
};

export default Home;
