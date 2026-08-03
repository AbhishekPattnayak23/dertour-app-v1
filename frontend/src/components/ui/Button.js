import "../styles/designTokens.css";
import React from 'react';

const Button = ({ children, variant = 'primary', size = 'medium', onClick, disabled = false, ...props }) => {
  const baseClasses = 'btn';
  const variantClass = `btn-${variant}`;
  const sizeClass = `btn-${size}`;

  return (
    <button
      className={`${baseClasses} ${variantClass} ${sizeClass}`}
      onClick={onClick}
      disabled={disabled}
      style={{
        backgroundColor: 'var(--color-primary)',
        color: 'var(--color-white)',
        padding: 'var(--spacing-md)',
        fontSize: 'var(--font-size-base)',
        fontFamily: 'var(--font-primary)',
        border: 'none',
        borderRadius: 'var(--spacing-xs)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1
      }}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
