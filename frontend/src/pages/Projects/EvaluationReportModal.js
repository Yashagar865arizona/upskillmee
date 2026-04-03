import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import styles from "./Projects.module.css";

const EvaluationReportModal = ({ report, onClose }) => {
  return (
    <AnimatePresence>
      {report && (
        <div className={styles.modalOverlay} onClick={onClose}>
          <motion.div
            className={styles.modalContent}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Evaluation Report</h3>
            <p><strong>Score:</strong> {report.score}</p>
            <p><strong>Feedback:</strong> {report.feedback}</p>

            {report.errors?.length > 0 && (
              <>
                <h4>Errors:</h4>
                <ul>{report.errors.map((err, i) => <li key={i}>{err}</li>)}</ul>
              </>
            )}

            {report.suggestions?.length > 0 && (
              <>
                <h4>Suggestions:</h4>
                <ul>{report.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </>
            )}

            {report.tips?.length > 0 && (
              <>
                <h4>Tips:</h4>
                <ul>{report.tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
              </>
            )}

            {report.references?.length > 0 && (
              <>
                <h4>References:</h4>
                <ul>
                  {report.references.map((r, i) => (
                    <li key={i}><a href={r} target="_blank" rel="noopener noreferrer">{r}</a></li>
                  ))}
                </ul>
              </>
            )}

            {report.theory && (
              <>
                <h4>Theory:</h4>
                <p>{report.theory}</p>
              </>
            )}

            <button className={styles.closeModalButton} onClick={onClose}>
              Close
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default EvaluationReportModal;
