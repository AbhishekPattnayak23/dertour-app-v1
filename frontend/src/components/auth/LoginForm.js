import React, { useState } from 'react';
import './LoginForm.css';

const LoginForm = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAzureLogin = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Redirect to Azure AD login endpoint
      window.location.href = '/api/auth/azure';
    } catch (err) {
      setError('Failed to initiate login. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img 
            src="/assets/dertour-logo.png" 
            alt="DerTour" 
            className="company-logo"
          />
          <h1 className="login-title">Welcome to DerTour</h1>
          <p className="login-subtitle">Sign in to your account</p>
        </div>

        <div className="login-form">
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <button
            onClick={handleAzureLogin}
            disabled={isLoading}
            className={`azure-login-btn ${isLoading ? 'loading' : ''}`}
          >
            <div className="btn-content">
              {isLoading ? (
                <>
                  <div className="spinner"></div>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <svg className="microsoft-icon" viewBox="0 0 23 23">
                    <path fill="#f25022" d="M1 1h10v10H1z"/>
                    <path fill="#00a4ef" d="M12 1h10v10H12z"/>
                    <path fill="#7fba00" d="M1 12h10v10H1z"/>
                    <path fill="#ffb900" d="M12 12h10v10H12z"/>
                  </svg>
                  <span>Sign in with Microsoft</span>
                </>
              )}
            </div>
          </button>

          <div className="login-footer">
            <p className="help-text">
              Need help? Contact your system administrator
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;