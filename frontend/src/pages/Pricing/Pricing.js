import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../context/ThemeContext";
import { Check, X, Globe, ToggleLeft, ToggleRight } from "lucide-react";
import styles from "./Pricing.module.css";

const PLANS = {
  IN: {
    currency: "INR",
    symbol: "\u20B9",
    locale: "en-IN",
    tiers: [
      { name: "Free", monthlyPrice: 0 },
      { name: "Pro", monthlyPrice: 599 },
      { name: "Growth", monthlyPrice: 999 },
    ],
  },
  US: {
    currency: "USD",
    symbol: "$",
    locale: "en-US",
    tiers: [
      { name: "Free", monthlyPrice: 0 },
      { name: "Pro", monthlyPrice: 19 },
      { name: "Growth", monthlyPrice: 29 },
    ],
  },
};

const FEATURES = [
  { name: "AI Chat Mentor", free: true, pro: true, growth: true },
  { name: "Personalized Learning Plans", free: true, pro: true, growth: true },
  { name: "Community Access", free: true, pro: true, growth: true },
  { name: "Basic Project Templates", free: true, pro: true, growth: true },
  { name: "Advanced AI Conversations", free: false, pro: true, growth: true },
  { name: "Skill Assessments", free: false, pro: true, growth: true },
  { name: "Portfolio Builder", free: false, pro: true, growth: true },
  { name: "Priority Support", free: false, pro: true, growth: true },
  { name: "Career Mentor Agent", free: false, pro: false, growth: true },
  { name: "Custom Learning Paths", free: false, pro: false, growth: true },
  { name: "1-on-1 Expert Sessions", free: false, pro: false, growth: true },
  { name: "Interview Prep Suite", free: false, pro: false, growth: true },
];

function detectRegion() {
  try {
    const lang = navigator.language || navigator.languages?.[0] || "";
    if (lang.includes("IN") || lang === "hi" || lang.startsWith("hi-")) {
      return "IN";
    }
  } catch {
    // fall through
  }
  return "US";
}

function formatPrice(amount, locale, currency) {
  if (amount === 0) return "Free";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

const Pricing = () => {
  const { darkMode } = useTheme();
  const navigate = useNavigate();
  const [region, setRegion] = useState(detectRegion);
  const [isAnnual, setIsAnnual] = useState(false);

  const plan = PLANS[region];
  const annualDiscount = 0.2;

  const tiers = useMemo(
    () =>
      plan.tiers.map((tier) => {
        const monthly = tier.monthlyPrice;
        const discounted = Math.round(monthly * (1 - annualDiscount));
        return {
          ...tier,
          displayPrice: isAnnual ? discounted : monthly,
          period: monthly === 0 ? "" : isAnnual ? "/mo (billed annually)" : "/mo",
          annualTotal: discounted * 12,
        };
      }),
    [plan, isAnnual, annualDiscount]
  );

  const toggleRegion = () => setRegion((r) => (r === "IN" ? "US" : "IN"));

  return (
    <section className={`${styles.pricing} ${darkMode ? styles.dark : ""}`}>
      {/* Header */}
      <div className={styles.headerSection}>
        <motion.button
          className={styles.backBtn}
          onClick={() => navigate("/")}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          &larr; Back to Home
        </motion.button>

        <motion.h1
          className={styles.title}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Simple, Transparent Pricing
        </motion.h1>
        <motion.p
          className={styles.subtitle}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          Start free. Upgrade when you're ready to accelerate.
        </motion.p>

        {/* Controls */}
        <div className={styles.controls}>
          {/* Region toggle */}
          <button className={styles.regionToggle} onClick={toggleRegion}>
            <Globe size={16} />
            <span>{region === "IN" ? "India (\u20B9)" : "USA ($)"}</span>
          </button>

          {/* Billing toggle */}
          <div className={styles.billingToggle}>
            <span className={!isAnnual ? styles.activeLabel : ""}>Monthly</span>
            <button
              className={styles.toggleSwitch}
              onClick={() => setIsAnnual((v) => !v)}
              aria-label="Toggle annual billing"
            >
              {isAnnual ? (
                <ToggleRight size={32} className={styles.toggleOn} />
              ) : (
                <ToggleLeft size={32} className={styles.toggleOff} />
              )}
            </button>
            <span className={isAnnual ? styles.activeLabel : ""}>
              Annual{" "}
              <span className={styles.saveBadge}>Save 20%</span>
            </span>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className={styles.cardsContainer}>
        {tiers.map((tier, idx) => {
          const isPopular = tier.name === "Pro";
          return (
            <motion.div
              key={tier.name}
              className={`${styles.card} ${isPopular ? styles.popular : ""}`}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: idx * 0.15 }}
            >
              {isPopular && <div className={styles.popularBadge}>Most Popular</div>}
              <h2 className={styles.tierName}>{tier.name}</h2>

              <div className={styles.priceBlock}>
                <span className={styles.priceAmount}>
                  {formatPrice(tier.displayPrice, plan.locale, plan.currency)}
                </span>
                {tier.period && <span className={styles.pricePeriod}>{tier.period}</span>}
              </div>

              {isAnnual && tier.monthlyPrice > 0 && (
                <p className={styles.annualNote}>
                  {formatPrice(tier.annualTotal, plan.locale, plan.currency)}/year
                </p>
              )}

              <ul className={styles.featureList}>
                {FEATURES.map((feat) => {
                  const key =
                    tier.name === "Free"
                      ? "free"
                      : tier.name === "Pro"
                      ? "pro"
                      : "growth";
                  const included = feat[key];
                  return (
                    <li
                      key={feat.name}
                      className={included ? styles.included : styles.excluded}
                    >
                      {included ? (
                        <Check size={16} className={styles.checkIcon} />
                      ) : (
                        <X size={16} className={styles.xIcon} />
                      )}
                      <span>{feat.name}</span>
                    </li>
                  );
                })}
              </ul>

              <motion.button
                className={`${styles.ctaBtn} ${isPopular ? styles.ctaPrimary : ""}`}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => {
                  if (tier.name === "Free") {
                    navigate("/auth/register");
                  }
                }}
              >
                {tier.name === "Free" ? "Sign Up Free" : "Coming Soon"}
              </motion.button>
            </motion.div>
          );
        })}
      </div>

      {/* Feature Comparison Table */}
      <div className={styles.comparisonSection}>
        <h2 className={styles.comparisonTitle}>Feature Comparison</h2>
        <div className={styles.tableWrapper}>
          <table className={styles.comparisonTable}>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Free</th>
                <th>Pro</th>
                <th>Growth</th>
              </tr>
            </thead>
            <tbody>
              {FEATURES.map((feat) => (
                <tr key={feat.name}>
                  <td>{feat.name}</td>
                  <td>
                    {feat.free ? (
                      <Check size={18} className={styles.tableCheck} />
                    ) : (
                      <X size={18} className={styles.tableX} />
                    )}
                  </td>
                  <td>
                    {feat.pro ? (
                      <Check size={18} className={styles.tableCheck} />
                    ) : (
                      <X size={18} className={styles.tableX} />
                    )}
                  </td>
                  <td>
                    {feat.growth ? (
                      <Check size={18} className={styles.tableCheck} />
                    ) : (
                      <X size={18} className={styles.tableX} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer CTA */}
      <div className={styles.footerCta}>
        <p>Have questions? We'd love to help.</p>
        <motion.button
          className={styles.contactBtn}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate("/")}
        >
          Contact Us
        </motion.button>
      </div>
    </section>
  );
};

export default Pricing;
