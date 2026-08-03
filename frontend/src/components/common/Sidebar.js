import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ isOpen = true, onToggle }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      path: '/dashboard',
      icon: '📊'
    },
    {
      id: 'projects',
      label: 'Projects',
      path: '/projects',
      icon: '📁'
    },
    {
      id: 'tasks',
      label: 'Tasks',
      path: '/tasks',
      icon: '✓'
    },
    {
      id: 'calendar',
      label: 'Calendar',
      path: '/calendar',
      icon: '📅'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      path: '/analytics',
      icon: '📈'
    },
    {
      id: 'settings',
      label: 'Settings',
      path: '/settings',
      icon: '⚙️'
    }
  ];

  const handleToggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const isActiveRoute = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          {!isCollapsed && <span className="logo-text">App</span>}
          <span className="logo-icon">🚀</span>
        </div>
        <button 
          className="sidebar-toggle"
          onClick={handleToggleCollapse}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="sidebar-nav">
        <ul className="nav-list">
          {navigationItems.map((item) => (
            <li key={item.id} className="nav-item">
              <Link
                to={item.path}
                className={`nav-link ${isActiveRoute(item.path) ? 'active' : ''}`}
                title={isCollapsed ? item.label : ''}
              >
                <span className="nav-icon">{item.icon}</span>
                {!isCollapsed && <span className="nav-label">{item.label}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">👤</div>
          {!isCollapsed && (
            <div className="user-details">
              <span className="user-name">User</span>
              <span className="user-role">Admin</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
export { Sidebar };