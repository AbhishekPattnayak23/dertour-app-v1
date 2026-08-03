import "../styles/designTokens.css";
import React, { useState, useEffect } from 'react';

const Toast = ({
  message,
  type = 'info',
  duration = 5000,
  onClose,
  isVisible = false
}) => {
  const [show, setShow] = useState(isVisible);

  useEffect(() => {
    setShow(isVisible);
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        setShow(false);
        if (onClose) onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!show) return null;

  const typeClasses = {
    success: 'bg-green-100 border-green-400 text-green-700',
    error: 'bg-red-100 border-red-400 text-red-700',
    warning: 'bg-yellow-100 border-yellow-400 text-yellow-700',
    info: 'bg-blue-100 border-blue-400 text-blue-700'
  };

  const iconMap = {
    success: '',
    error: '',
    warning: '!',
    info: 'i'
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className={`flex items-center p-4 border rounded-md shadow-lg ${typeClasses[type]}`}>
        <div className="flex-shrink-0 mr-3">
          <span className="font-bold">{iconMap[type]}</span>
        </div>
        <div className="flex-1">
          <p className="text-sm">{message}</p>
        </div>
        <button
          onClick={() => {
            setShow(false);
            if (onClose) onClose();
          }}
          className="flex-shrink-0 ml-3 text-lg leading-none"
        >

        </button>
      </div>
    </div>
  );
};

export default Toast;
