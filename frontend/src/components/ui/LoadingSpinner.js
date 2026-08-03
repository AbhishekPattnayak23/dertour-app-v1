import "../styles/designTokens.css";
import React from 'react';
import PropTypes from 'prop-types';

const LoadingSpinner = ({ 
  size = 'medium', 
  overlay = false, 
  color = 'primary',
  className = '',
  text = ''
}) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
    xlarge: 'w-16 h-16'
  };

  const colorClasses = {
    primary: 'border-blue-600',
    secondary: 'border-gray-600',
    white: 'border-white',
    success: 'border-green-600',
    warning: 'border-yellow-600',
    error: 'border-red-600'
  };

  const spinnerElement = (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`
          ${sizeClasses[size]}
          ${colorClasses[color]}
          border-2
          border-t-transparent
          border-solid
          rounded-full
          animate-spin
        `}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <span className={`mt-2 text-sm ${color === 'white' ? 'text-white' : 'text-gray-600'}`}>
          {text}
        </span>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 shadow-lg">
          {spinnerElement}
        </div>
      </div>
    );
  }

  return spinnerElement;
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large', 'xlarge']),
  overlay: PropTypes.bool,
  color: PropTypes.oneOf(['primary', 'secondary', 'white', 'success', 'warning', 'error']),
  className: PropTypes.string,
  text: PropTypes.string
};

export { LoadingSpinner };