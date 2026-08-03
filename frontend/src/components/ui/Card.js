import "../styles/designTokens.css";
import React from 'react';
import PropTypes from 'prop-types';

const Card = ({ 
  children, 
  className = '', 
  elevation = 1, 
  hoverable = false,
  ...props 
}) => {
  const elevationClasses = {
    0: 'shadow-none',
    1: 'shadow-sm',
    2: 'shadow-md',
    3: 'shadow-lg',
    4: 'shadow-xl',
    5: 'shadow-2xl'
  };

  const baseClasses = 'bg-white rounded-lg border border-gray-200 overflow-hidden';
  const hoverClasses = hoverable ? 'hover:shadow-lg transition-shadow duration-200' : '';
  const shadowClasses = elevationClasses[elevation] || elevationClasses[1];

  return (
    <div 
      className={`${baseClasses} ${shadowClasses} ${hoverClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ 
  children, 
  className = '',
  title,
  subtitle,
  actions,
  ...props 
}) => {
  const baseClasses = 'px-6 py-4 border-b border-gray-200 bg-gray-50';

  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      {title || subtitle || actions ? (
        <div className="flex items-center justify-between">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="flex items-center space-x-2">
              {actions}
            </div>
          )}
        </div>
      ) : null}
      {children}
    </div>
  );
};

const CardBody = ({ 
  children, 
  className = '',
  padding = 'normal',
  ...props 
}) => {
  const paddingClasses = {
    none: '',
    small: 'p-4',
    normal: 'p-6',
    large: 'p-8'
  };

  const baseClasses = 'text-gray-700';
  const spacingClasses = paddingClasses[padding] || paddingClasses.normal;

  return (
    <div 
      className={`${baseClasses} ${spacingClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

const CardFooter = ({ 
  children, 
  className = '',
  align = 'right',
  ...props 
}) => {
  const alignmentClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
    around: 'justify-around'
  };

  const baseClasses = 'px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center';
  const alignClasses = alignmentClasses[align] || alignmentClasses.right;

  return (
    <div 
      className={`${baseClasses} ${alignClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  elevation: PropTypes.oneOf([0, 1, 2, 3, 4, 5]),
  hoverable: PropTypes.bool
};

CardHeader.propTypes = {
  children: PropTypes.node,
  className: PropTypes.string,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  actions: PropTypes.node
};

CardBody.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  padding: PropTypes.oneOf(['none', 'small', 'normal', 'large'])
};

CardFooter.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  align: PropTypes.oneOf(['left', 'center', 'right', 'between', 'around'])
};

export { Card, CardHeader, CardBody, CardFooter };