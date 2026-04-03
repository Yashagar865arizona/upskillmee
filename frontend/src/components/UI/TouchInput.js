import React, { forwardRef } from 'react';
import styles from './TouchInput.module.css';

const TouchInput = forwardRef(({
  label,
  error,
  helperText,
  variant = 'outlined',
  size = 'medium',
  fullWidth = false,
  multiline = false,
  rows = 3,
  className = '',
  ...props
}, ref) => {
  const inputClasses = [
    styles.input,
    styles[variant],
    styles[size],
    fullWidth ? styles.fullWidth : '',
    error ? styles.error : '',
    className
  ].filter(Boolean).join(' ');

  const InputComponent = multiline ? 'textarea' : 'input';

  return (
    <div className={styles.inputContainer}>
      {label && (
        <label className={styles.label} htmlFor={props.id}>
          {label}
          {props.required && <span className={styles.required}>*</span>}
        </label>
      )}
      <InputComponent
        ref={ref}
        className={inputClasses}
        rows={multiline ? rows : undefined}
        {...props}
      />
      {error && <span className={styles.errorText}>{error}</span>}
      {helperText && !error && <span className={styles.helperText}>{helperText}</span>}
    </div>
  );
});

TouchInput.displayName = 'TouchInput';

export default TouchInput;