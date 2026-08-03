import React from 'react';
import { useNavigate } from 'react-router-dom';
import ProfileCard from '../components/profile/ProfileCard';
import SettingsPanel from '../components/profile/SettingsPanel';
import ActivityHistory from '../components/profile/ActivityHistory';
import Button from '../components/common/Button';
import '../styles/designTokens.css';
import './ProfilePage.css';

const ProfilePage = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear any stored auth data
    localStorage.removeItem('authToken');
    navigate('/login');
  };

  const handleBackToChat = () => {
    navigate('/chat');
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1 className="page-title">My Profile</h1>
        <div className="profile-actions">
          <Button variant="secondary" onClick={handleBackToChat}>
            Back to Chat
          </Button>
          <Button variant="danger" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </div>

      <div className="profile-content">
        <ProfileCard />
        <SettingsPanel />
        <ActivityHistory />
      </div>
    </div>
  );
};

export default ProfilePage;
