import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '../../store/slices/authSlice';
import './Header.css';

const Header = () => {
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [isNotificationDropdownOpen, setIsNotificationDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  const notifications = useSelector((state) => state.notifications?.items || []);
  const unreadCount = notifications.filter(n => !n.read).length;

  const handleLogout = () => {
    dispatch(logout());
    setIsProfileDropdownOpen(false);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Implement search functionality
      console.log('Searching for:', searchQuery);
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read and navigate
    console.log('Clicked notification:', notification);
    setIsNotificationDropdownOpen(false);
  };

  const toggleProfileDropdown = () => {
    setIsProfileDropdownOpen(!isProfileDropdownOpen);
    setIsNotificationDropdownOpen(false);
  };

  const toggleNotificationDropdown = () => {
    setIsNotificationDropdownOpen(!isNotificationDropdownOpen);
    setIsProfileDropdownOpen(false);
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="header-left">
          <div className="logo">
            <h1>App</h1>
          </div>
          
          <form className="search-form" onSubmit={handleSearch}>
            <div className="search-input-wrapper">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-button">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
              </button>
            </div>
          </form>
        </div>

        <div className="header-right">
          {isAuthenticated ? (
            <>
              <div className="notification-wrapper">
                <button
                  className="notification-button"
                  onClick={toggleNotificationDropdown}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                  </svg>
                  {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount}</span>
                  )}
                </button>

                {isNotificationDropdownOpen && (
                  <div className="notification-dropdown">
                    <div className="dropdown-header">
                      <h3>Notifications</h3>
                    </div>
                    <div className="notification-list">
                      {notifications.length > 0 ? (
                        notifications.slice(0, 5).map((notification) => (
                          <div
                            key={notification.id}
                            className={`notification-item ${!notification.read ? 'unread' : ''}`}
                            onClick={() => handleNotificationClick(notification)}
                          >
                            <div className="notification-content">
                              <p className="notification-title">{notification.title}</p>
                              <p className="notification-message">{notification.message}</p>
                              <span className="notification-time">{notification.createdAt}</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="no-notifications">
                          <p>No notifications</p>
                        </div>
                      )}
                    </div>
                    {notifications.length > 5 && (
                      <div className="dropdown-footer">
                        <button className="view-all-button">View All</button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="profile-wrapper">
                <button
                  className="profile-button"
                  onClick={toggleProfileDropdown}
                >
                  <div className="profile-avatar">
                    {user?.avatar ? (
                      <img src={user.avatar} alt={user.name} />
                    ) : (
                      <span>{user?.name?.charAt(0) || 'U'}</span>
                    )}
                  </div>
                  <span className="profile-name">{user?.name || 'User'}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6,9 12,15 18,9"></polyline>
                  </svg>
                </button>

                {isProfileDropdownOpen && (
                  <div className="profile-dropdown">
                    <div className="dropdown-header">
                      <div className="profile-info">
                        <div className="profile-avatar-large">
                          {user?.avatar ? (
                            <img src={user.avatar} alt={user.name} />
                          ) : (
                            <span>{user?.name?.charAt(0) || 'U'}</span>
                          )}
                        </div>
                        <div>
                          <p className="profile-name-large">{user?.name}</p>
                          <p className="profile-email">{user?.email}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="dropdown-menu">
                      <button className="dropdown-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        Profile
                      </button>
                      
                      <button className="dropdown-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="3"></circle>
                          <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"></path>
                        </svg>
                        Settings
                      </button>
                      
                      <button className="dropdown-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="1"></circle>
                          <circle cx="19" cy="12" r="1"></circle>
                          <circle cx="5" cy="12" r="1"></circle>
                        </svg>
                        Help
                      </button>
                      
                      <hr className="dropdown-divider" />
                      
                      <button className="dropdown-item logout-item" onClick={handleLogout}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                          <polyline points="16,17 21,12 16,7"></polyline>
                          <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                        Logout
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="auth-buttons">
              <button className="login-button">Login</button>
              <button className="signup-button">Sign Up</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export { Header };